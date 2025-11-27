"""
PDF Processing Service for Regulatory Documents
Extracts text from PDF and structures it for chunking

⚠️ DEMO MODE: Used to process the preloaded RBI Payment Aggregator regulation
"""

import re
from pathlib import Path
from typing import List, Dict, Optional
from loguru import logger
from pypdf import PdfReader


class PDFProcessor:
    """Extract and structure text from regulatory PDFs"""
    
    def extract_text(self, pdf_path: Path) -> str:
        """
        Extract all text from PDF file.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            str: Extracted text content
        """
        try:
            # Use pypdf (preferred modern package)
            with open(pdf_path, 'rb') as file:
                pdf_reader = PdfReader(file)
                text = ""
                
                for page_num, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()
                    text += f"\n--- Page {page_num + 1} ---\n{page_text}"
                
                logger.info(f"Extracted {len(text)} characters from {pdf_path.name} using pypdf")
                return text

        except Exception as e:
            logger.error(f"Failed to extract PDF {pdf_path}: {e}")
            raise
    
    def structure_sections(self, text: str) -> List[Dict[str, str]]:
        """
        Break PDF text into structured sections.
        Detects headings, clauses, sub-clauses.
        
        Args:
            text: Raw PDF text
            
        Returns:
            List of section dictionaries with number, title, and content
        """
        sections = []
        
        # Pattern: Detect numbered sections (e.g., "1. Introduction", "2.1 Definitions")
        section_pattern = r'^(\d+\.?\d*\.?\d*)\s+([A-Z][^\n]+)'
        
        current_section = None
        current_text = []
        
        for line in text.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            # Check if this is a section heading
            match = re.match(section_pattern, line)
            
            if match:
                # Save previous section
                if current_section:
                    sections.append({
                        "section_number": current_section["number"],
                        "section_title": current_section["title"],
                        "content": "\n".join(current_text).strip()
                    })
                
                # Start new section
                current_section = {
                    "number": match.group(1),
                    "title": match.group(2)
                }
                current_text = []
            
            else:
                # Add to current section
                current_text.append(line)
        
        # Add last section
        if current_section:
            sections.append({
                "section_number": current_section["number"],
                "section_title": current_section["title"],
                "content": "\n".join(current_text).strip()
            })
        
        logger.info(f"Structured PDF into {len(sections)} sections")
        return sections
    
    def chunk_sections(
        self, 
        sections: List[Dict[str, str]], 
        max_chunk_size: int = 1000
    ) -> List[Dict[str, str]]:
        """
        Break sections into chunks suitable for embedding.
        Keeps semantic meaning intact.
        
        Args:
            sections: List of structured sections
            max_chunk_size: Maximum characters per chunk
            
        Returns:
            List of chunk dictionaries
        """
        chunks = []
        
        for section in sections:
            content = section["content"]
            
            # If section is small enough, use as single chunk
            if len(content) <= max_chunk_size:
                chunks.append({
                    "section_number": section["section_number"],
                    "section_title": section["section_title"],
                    "text": content,
                    "chunk_index": 0
                })
            
            else:
                # Split by paragraphs first
                paragraphs = content.split('\n\n')
                current_chunk = []
                current_size = 0
                chunk_index = 0
                
                for para in paragraphs:
                    para_size = len(para)
                    
                    if current_size + para_size > max_chunk_size and current_chunk:
                        # Save current chunk
                        chunks.append({
                            "section_number": section["section_number"],
                            "section_title": section["section_title"],
                            "text": "\n\n".join(current_chunk),
                            "chunk_index": chunk_index
                        })
                        
                        # Start new chunk
                        current_chunk = [para]
                        current_size = para_size
                        chunk_index += 1
                    
                    else:
                        current_chunk.append(para)
                        current_size += para_size
                
                # Add remaining chunk
                if current_chunk:
                    chunks.append({
                        "section_number": section["section_number"],
                        "section_title": section["section_title"],
                        "text": "\n\n".join(current_chunk),
                        "chunk_index": chunk_index
                    })
        
        logger.info(f"Created {len(chunks)} chunks from {len(sections)} sections")
        return chunks
