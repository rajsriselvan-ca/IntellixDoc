from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class DocumentUpload(BaseModel):
    filename: str
    file_size: int
    status: str = "processing"


class DocumentResponse(BaseModel):
    id: int
    filename: str
    file_size: Optional[int]
    upload_date: datetime
    status: str
    
    class Config:
        from_attributes = True


class ChunkResponse(BaseModel):
    id: int
    document_id: int
    content: str
    page_number: Optional[int]
    chunk_index: Optional[int]
    
    class Config:
        from_attributes = True


class ChatCreate(BaseModel):
    document_id: Optional[int] = None
    title: Optional[str] = "New Chat"


class ChatResponse(BaseModel):
    id: int
    document_id: Optional[int]
    title: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class MessageCreate(BaseModel):
    content: str


class CitationResponse(BaseModel):
    id: int
    chunk_id: int
    document_id: int
    document_filename: str
    chunk_content: str
    page_number: Optional[int]
    relevance_score: Optional[float]
    
    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime
    citations: List[CitationResponse] = []
    
    class Config:
        from_attributes = True


class ChatWithMessages(ChatResponse):
    messages: List[MessageResponse] = []

