from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import uuid
import aiofiles
import logging
import traceback
from datetime import datetime

from app.database import get_db, init_db, Document, Chat, Message, Chunk, Citation
from app.models import (
    DocumentResponse, ChatCreate, ChatResponse, MessageCreate,
    MessageResponse, ChatWithMessages
)
from app.config import settings
# Lazy import to avoid PyTorch DLL issues on Windows startup
# from app.services.embedding import generate_embedding
from app.services.qdrant_service import qdrant_service
from app.services.llm import llm_service
from redis import Redis
from rq import Queue

# Configure logging first (before other operations that might use it)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize database
init_db()

# Initialize Redis queue (with error handling)
try:
    redis_conn = Redis.from_url(settings.redis_url)
    # Test connection
    redis_conn.ping()
    task_queue = Queue("default", connection=redis_conn)
    logger.info("Redis connection established")
except Exception as e:
    logger.warning(f"Redis connection failed: {str(e)}. Background tasks may not work.")
    redis_conn = None
    task_queue = None

app = FastAPI(title="IntellixDoc API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://frontend:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create uploads directory
os.makedirs(settings.upload_dir, exist_ok=True)

# Maximum file upload size (500MB)
MAX_UPLOAD_SIZE = 500 * 1024 * 1024  # 500MB in bytes
CHUNK_SIZE = 8192  # 8KB chunks for streaming


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    init_db()


@app.get("/")
async def root():
    return {"message": "IntellixDoc API", "status": "running"}


@app.get("/health")
async def health():
    """Health check endpoint with service status."""
    status = {
        "status": "healthy",
        "services": {}
    }
    
    # Check Redis
    try:
        if redis_conn:
            redis_conn.ping()
            status["services"]["redis"] = "connected"
            
            # Check if worker queue has workers
            try:
                from rq import Queue
                queue = Queue("default", connection=redis_conn)
                workers = queue.connection.smembers(queue.redis_workers_key)
                if workers:
                    status["services"]["worker"] = f"connected ({len(workers)} worker(s))"
                else:
                    status["services"]["worker"] = "warning: no workers found"
            except Exception as e:
                status["services"]["worker"] = f"error checking workers: {str(e)}"
        else:
            status["services"]["redis"] = "not_initialized"
            status["services"]["worker"] = "not_available"
    except Exception as e:
        status["services"]["redis"] = f"error: {str(e)}"
        status["services"]["worker"] = "not_available"
    
    # Check Qdrant
    try:
        collections = qdrant_service.client.get_collections()
        status["services"]["qdrant"] = "connected"
    except Exception as e:
        status["services"]["qdrant"] = f"error: {str(e)}"
    
    # Check database
    try:
        from sqlalchemy import text
        from app.database import engine
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        status["services"]["database"] = "connected"
    except Exception as e:
        status["services"]["database"] = f"error: {str(e)}"
    
    # Check embedding model
    try:
        from app.services.embedding import get_embedding_model
        model = get_embedding_model()
        status["services"]["embedding"] = "loaded"
    except Exception as e:
        status["services"]["embedding"] = f"error: {str(e)}"
    
    # Check LLM service
    try:
        if settings.llm_provider.lower() == "groq" and not settings.groq_api_key:
            status["services"]["llm"] = "error: GROQ_API_KEY not set"
        elif settings.llm_provider.lower() == "openai" and not settings.openai_api_key:
            status["services"]["llm"] = "error: OPENAI_API_KEY not set"
        elif settings.llm_provider.lower() == "claude" and not settings.anthropic_api_key:
            status["services"]["llm"] = "error: ANTHROPIC_API_KEY not set"
        else:
            status["services"]["llm"] = f"configured ({settings.llm_provider})"
    except Exception as e:
        status["services"]["llm"] = f"error: {str(e)}"
    
    return status


@app.post("/api/documents/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload a PDF document with streaming support for large files."""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    # Generate unique filename to avoid conflicts
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(settings.upload_dir, unique_filename)
    
    # Stream file directly to disk (no memory loading)
    file_size = 0
    file_too_large = False
    try:
        async with aiofiles.open(file_path, 'wb') as f:
            while True:
                chunk = await file.read(CHUNK_SIZE)  # Read in 8KB chunks
                if not chunk:
                    break
                
                file_size += len(chunk)
                
                # Check size limit during upload
                if file_size > MAX_UPLOAD_SIZE:
                    file_too_large = True
                    break
                
                await f.write(chunk)
    except Exception as e:
        # Clean up on any error
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=500,
            detail=f"Error uploading file: {str(e)}"
        )
    
    # Check if file was too large (after closing the file)
    if file_too_large:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size: {MAX_UPLOAD_SIZE / (1024 * 1024):.0f}MB"
        )
    
    # Create document record
    document = Document(
        filename=file.filename,  # Original filename
        file_path=file_path,      # Unique file path on disk
        file_size=file_size,
        status="processing"
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    
    # Queue processing task
    if task_queue:
        try:
            from app.tasks import process_document
            job = task_queue.enqueue(process_document, document.id, file_path)
            logger.info(f"Document {document.id} queued for processing with job ID: {job.id}")
        except Exception as e:
            logger.error(f"Failed to queue document processing task: {str(e)}")
            # Don't fail the upload, but log the error
            # The document will remain in "processing" status
    else:
        logger.warning("Redis not available, document processing will not be queued")
        # Set status to failed if Redis is not available
        document.status = "failed"
        db.commit()
        raise HTTPException(
            status_code=503,
            detail="Background processing service is not available. Please ensure Redis and the worker are running."
        )
    
    return document


@app.get("/api/documents", response_model=List[DocumentResponse])
async def list_documents(db: Session = Depends(get_db)):
    """List all documents."""
    documents = db.query(Document).order_by(Document.upload_date.desc()).all()
    return documents


@app.get("/api/documents/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: int, db: Session = Depends(get_db)):
    """Get a specific document."""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@app.delete("/api/documents/{document_id}")
async def delete_document(document_id: int, db: Session = Depends(get_db)):
    """Delete a document and all its chunks."""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Delete citations referencing this document
    db.query(Citation).filter(Citation.document_id == document_id).delete()
    
    # Delete all chunks for this document
    db.query(Chunk).filter(Chunk.document_id == document_id).delete()
    
    # Delete vectors from Qdrant
    try:
        qdrant_service.delete_document_vectors(document_id)
    except Exception as e:
        logger.warning(f"Error deleting vectors from Qdrant: {str(e)}")
    
    # Delete the file from disk
    if document.file_path and os.path.exists(document.file_path):
        try:
            os.remove(document.file_path)
        except Exception as e:
            logger.warning(f"Error deleting file: {str(e)}")
    
    # Delete the document
    db.delete(document)
    db.commit()
    
    return {"message": "Document deleted successfully"}


@app.post("/api/chats", response_model=ChatResponse)
async def create_chat(chat_data: ChatCreate, db: Session = Depends(get_db)):
    """Create a new chat."""
    chat = Chat(
        document_id=chat_data.document_id,
        title=chat_data.title or "New Chat"
    )
    db.add(chat)
    db.commit()
    db.refresh(chat)
    return chat


@app.get("/api/chats", response_model=List[ChatResponse])
async def list_chats(db: Session = Depends(get_db)):
    """List all chats."""
    chats = db.query(Chat).order_by(Chat.updated_at.desc()).all()
    return chats


@app.delete("/api/chats/{chat_id}")
async def delete_chat(chat_id: int, db: Session = Depends(get_db)):
    """Delete a chat and all its messages."""
    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    # Delete all citations for messages in this chat
    messages = db.query(Message).filter(Message.chat_id == chat_id).all()
    for message in messages:
        db.query(Citation).filter(Citation.message_id == message.id).delete()
    
    # Delete all messages
    db.query(Message).filter(Message.chat_id == chat_id).delete()
    
    # Delete the chat
    db.delete(chat)
    db.commit()
    
    return {"message": "Chat deleted successfully"}


@app.get("/api/chats/{chat_id}", response_model=ChatWithMessages)
async def get_chat(chat_id: int, db: Session = Depends(get_db)):
    """Get a chat with messages."""
    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return chat


@app.post("/api/chats/{chat_id}/messages", response_model=MessageResponse)
async def create_message(
    chat_id: int,
    message_data: MessageCreate,
    db: Session = Depends(get_db)
):
    """Create a message and get AI response."""
    try:
        # Verify chat exists
        chat = db.query(Chat).filter(Chat.id == chat_id).first()
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")
        
        # Create user message
        user_message = Message(
            chat_id=chat_id,
            role="user",
            content=message_data.content
        )
        db.add(user_message)
        db.commit()
        logger.info(f"Created user message for chat {chat_id}")
        
        # Update chat timestamp
        chat.updated_at = datetime.utcnow()
        db.commit()
        
        # Generate embedding for query (lazy import to avoid PyTorch DLL issues)
        try:
            from app.services.embedding import generate_embedding
            query_embedding = generate_embedding(message_data.content)
            logger.info("Generated query embedding successfully")
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=500,
                detail=f"Error generating embedding: {str(e)}"
            )
        
        # Search for relevant chunks
        try:
            search_results = qdrant_service.search(query_embedding, limit=5, score_threshold=0.3)
            logger.info(f"Found {len(search_results)} search results")
        except Exception as e:
            logger.error(f"Error searching Qdrant: {str(e)}")
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=500,
                detail=f"Error searching for relevant chunks: {str(e)}. Make sure Qdrant is running."
            )
        
        # Get chat history for context
        previous_messages = db.query(Message).filter(
            Message.chat_id == chat_id
        ).order_by(Message.created_at.desc()).limit(10).all()
        
        chat_history = [
            {"role": msg.role, "content": msg.content}
            for msg in reversed(previous_messages[:-1])  # Exclude current user message
        ]
        
        # Build context from retrieved chunks
        context_chunks = []
        chunk_ids = []
        document_ids = set()
        
        for result in search_results:
            try:
                payload = result.get("payload", {})
                if not payload:
                    logger.warning(f"Search result missing payload: {result}")
                    continue
                    
                chunk_ids.append(payload.get("chunk_id"))
                if "document_id" in payload:
                    document_ids.add(payload["document_id"])
                if "content" in payload:
                    context_chunks.append({
                        "content": payload["content"],
                        "page": payload.get("page_number"),
                        "score": result.get("score", 0.0)
                    })
            except Exception as e:
                logger.warning(f"Error processing search result: {str(e)}")
                continue
        
        # If no context chunks found, use empty context
        if not context_chunks:
            logger.warning("No context chunks found from search results")
            context = "No relevant context found in documents."
        else:
            context = "\n\n".join([
                f"[Page {chunk.get('page', 'N/A')}] {chunk['content']}"
                for chunk in context_chunks
            ])
        
        # Generate AI response
        try:
            ai_response = await llm_service.generate_response(
                query=message_data.content,
                context=context,
                chat_history=chat_history
            )
            logger.info("Generated AI response successfully")
        except Exception as e:
            logger.error(f"Error generating AI response: {str(e)}")
            logger.error(traceback.format_exc())
            ai_response = f"I apologize, but I encountered an error while generating a response: {str(e)}"
        
        # Create assistant message
        assistant_message = Message(
            chat_id=chat_id,
            role="assistant",
            content=ai_response
        )
        db.add(assistant_message)
        db.commit()
        db.refresh(assistant_message)
        
        # Create citations
        for result in search_results:
            try:
                payload = result.get("payload", {})
                if not payload:
                    continue
                    
                chunk_id = payload.get("chunk_id")
                
                if chunk_id:
                    chunk = db.query(Chunk).filter(Chunk.id == chunk_id).first()
                else:
                    # Fallback: find by document_id and chunk_index
                    if "document_id" in payload:
                        chunk = db.query(Chunk).filter(
                            Chunk.document_id == payload["document_id"],
                            Chunk.chunk_index == payload.get("chunk_index")
                        ).first()
                    else:
                        chunk = None
                
                if chunk and "document_id" in payload:
                    citation = Citation(
                        message_id=assistant_message.id,
                        chunk_id=chunk.id,
                        document_id=payload["document_id"],
                        relevance_score=result.get("score")
                    )
                    db.add(citation)
            except Exception as e:
                logger.warning(f"Error creating citation: {str(e)}")
                continue
        
        db.commit()
        db.refresh(assistant_message)
        
        # Load citations for response
        citations = db.query(Citation).filter(Citation.message_id == assistant_message.id).all()
        
        response_data = {
            "id": assistant_message.id,
            "role": assistant_message.role,
            "content": assistant_message.content,
            "created_at": assistant_message.created_at,
            "citations": []
        }
        
        for citation in citations:
            try:
                chunk = db.query(Chunk).filter(Chunk.id == citation.chunk_id).first()
                document = db.query(Document).filter(Document.id == citation.document_id).first()
                
                if chunk and document:
                    response_data["citations"].append({
                        "id": citation.id,
                        "chunk_id": citation.chunk_id,
                        "document_id": citation.document_id,
                        "document_filename": document.filename,
                        "chunk_content": chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content,
                        "page_number": chunk.page_number,
                        "relevance_score": citation.relevance_score
                    })
            except Exception as e:
                logger.warning(f"Error loading citation data: {str(e)}")
                continue
        
        return response_data
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Log unexpected errors
        logger.error(f"Unexpected error in create_message: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.get("/api/chats/{chat_id}/messages", response_model=List[MessageResponse])
async def get_messages(chat_id: int, db: Session = Depends(get_db)):
    """Get all messages for a chat."""
    messages = db.query(Message).filter(
        Message.chat_id == chat_id
    ).order_by(Message.created_at.asc()).all()
    
    result = []
    for message in messages:
        citations = db.query(Citation).filter(Citation.message_id == message.id).all()
        citations_data = []
        
        for citation in citations:
            chunk = db.query(Chunk).filter(Chunk.id == citation.chunk_id).first()
            document = db.query(Document).filter(Document.id == citation.document_id).first()
            
            if chunk and document:
                citations_data.append({
                    "id": citation.id,
                    "chunk_id": citation.chunk_id,
                    "document_id": citation.document_id,
                    "document_filename": document.filename,
                    "chunk_content": chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content,
                    "page_number": chunk.page_number,
                    "relevance_score": citation.relevance_score
                })
        
        result.append({
            "id": message.id,
            "role": message.role,
            "content": message.content,
            "created_at": message.created_at,
            "citations": citations_data
        })
    
    return result

