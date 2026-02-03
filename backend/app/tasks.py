from rq import get_current_job
from app.database import SessionLocal, Document, Chunk
from app.services.pdf_parser import pdf_parser
from app.services.embedding import generate_embeddings
from app.services.qdrant_service import qdrant_service, COLLECTION_NAME
from qdrant_client.models import PointStruct
import os
import logging
import traceback

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def process_document(document_id: int, file_path: str):
    """Background task to process uploaded PDF."""
    db = SessionLocal()
    document = None
    
    try:
        logger.info(f"Starting to process document {document_id} from {file_path}")
        
        # Verify file exists
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            document = db.query(Document).filter(Document.id == document_id).first()
            if document:
                document.status = "failed"
                db.commit()
            return
        
        # Update document status
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            logger.error(f"Document {document_id} not found in database")
            return
        
        document.status = "processing"
        db.commit()
        logger.info(f"Document {document_id} status set to processing")
        
        # Parse PDF
        logger.info(f"Parsing PDF: {file_path}")
        chunks_data = pdf_parser.parse_pdf(file_path)
        
        if not chunks_data:
            logger.warning(f"No chunks extracted from PDF {file_path}")
            document.status = "failed"
            db.commit()
            return
        
        logger.info(f"Extracted {len(chunks_data)} chunks from PDF")
        
        # Generate embeddings
        logger.info(f"Generating embeddings for {len(chunks_data)} chunks")
        chunk_texts = [chunk["content"] for chunk in chunks_data]
        embeddings = generate_embeddings(chunk_texts)
        
        if not embeddings or len(embeddings) != len(chunks_data):
            logger.error(f"Embedding generation failed: got {len(embeddings) if embeddings else 0} embeddings for {len(chunks_data)} chunks")
            document.status = "failed"
            db.commit()
            return
        
        logger.info(f"Generated {len(embeddings)} embeddings")
        
        # Prepare vectors and payloads for Qdrant
        vectors = []
        payloads = []
        vector_ids = []
        
        for i, (chunk_data, embedding) in enumerate(zip(chunks_data, embeddings)):
            vector_id = f"doc_{document_id}_chunk_{i}"
            vector_ids.append(vector_id)
            vectors.append(embedding)
            
            payloads.append({
                "document_id": document_id,
                "chunk_index": chunk_data.get("chunk_index", i),
                "page_number": chunk_data.get("page_number"),
                "content": chunk_data["content"]
            })
        
        # Add to Qdrant
        logger.info(f"Adding {len(vectors)} vectors to Qdrant")
        qdrant_service.add_vectors(vectors, payloads, vector_ids)
        logger.info("Vectors added to Qdrant successfully")
        
        # Save chunks to database
        logger.info("Saving chunks to database")
        db_chunks = []
        for i, (chunk_data, vector_id) in enumerate(zip(chunks_data, vector_ids)):
            chunk = Chunk(
                document_id=document_id,
                content=chunk_data["content"],
                page_number=chunk_data.get("page_number"),
                chunk_index=chunk_data.get("chunk_index", i),
                vector_id=vector_id
            )
            db.add(chunk)
            db_chunks.append(chunk)
        
        db.flush()  # Flush to get chunk IDs
        logger.info(f"Saved {len(db_chunks)} chunks to database")
        
        # Update Qdrant payloads with chunk IDs
        logger.info("Updating Qdrant payloads with chunk IDs")
        updated_points = []
        for chunk, vector_id, embedding in zip(db_chunks, vector_ids, embeddings):
            # Update payload in Qdrant with chunk ID
            payload = {
                "document_id": document_id,
                "chunk_id": chunk.id,
                "chunk_index": chunk.chunk_index,
                "page_number": chunk.page_number,
                "content": chunk.content
            }
            updated_points.append(PointStruct(id=vector_id, vector=embedding, payload=payload))
        
        # Re-upsert with updated payloads
        if updated_points:
            qdrant_service.client.upsert(
                collection_name=COLLECTION_NAME,
                points=updated_points
            )
            logger.info("Updated Qdrant payloads with chunk IDs")
        
        document.status = "completed"
        db.commit()
        logger.info(f"Document {document_id} processing completed successfully")
        
    except Exception as e:
        error_msg = f"Error processing document {document_id}: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        
        try:
            if document:
                document.status = "failed"
                db.commit()
                logger.info(f"Document {document_id} status set to failed")
        except Exception as db_error:
            logger.error(f"Failed to update document status to failed: {str(db_error)}")
    finally:
        try:
            db.close()
        except Exception as e:
            logger.error(f"Error closing database connection: {str(e)}")

