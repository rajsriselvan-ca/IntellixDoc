import fitz  # PyMuPDF
from typing import List, Dict
import os


class PDFParser:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def extract_text(self, file_path: str) -> List[Dict]:
        """Extract text from PDF with page information."""
        doc = fitz.open(file_path)
        pages_data = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            
            if text.strip():
                pages_data.append({
                    "page_number": page_num + 1,
                    "text": text.strip()
                })
        
        doc.close()
        return pages_data
    
    def chunk_text(self, text: str, page_number: int) -> List[Dict]:
        """Split text into chunks with overlap."""
        chunks = []
        words = text.split()
        
        current_chunk = []
        current_length = 0
        chunk_index = 0
        
        for word in words:
            word_length = len(word) + 1  # +1 for space
            
            if current_length + word_length > self.chunk_size and current_chunk:
                # Save current chunk
                chunk_text = " ".join(current_chunk)
                chunks.append({
                    "content": chunk_text,
                    "page_number": page_number,
                    "chunk_index": chunk_index
                })
                chunk_index += 1
                
                # Start new chunk with overlap
                overlap_words = current_chunk[-self.chunk_overlap:] if len(current_chunk) > self.chunk_overlap else current_chunk
                current_chunk = overlap_words + [word]
                current_length = sum(len(w) + 1 for w in current_chunk)
            else:
                current_chunk.append(word)
                current_length += word_length
        
        # Add remaining chunk
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            chunks.append({
                "content": chunk_text,
                "page_number": page_number,
                "chunk_index": chunk_index
            })
        
        return chunks
    
    def parse_pdf(self, file_path: str) -> List[Dict]:
        """Parse PDF and return chunks."""
        pages_data = self.extract_text(file_path)
        all_chunks = []
        
        for page_data in pages_data:
            page_chunks = self.chunk_text(
                page_data["text"],
                page_data["page_number"]
            )
            all_chunks.extend(page_chunks)
        
        return all_chunks


pdf_parser = PDFParser()

