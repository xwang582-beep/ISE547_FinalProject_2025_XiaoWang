"""
Text Chunker Module
Intelligently breaks text into manageable chunks for LLM processing
"""

import re
from typing import List, Optional
import tiktoken


class TextChunker:
    """Split text into semantic chunks with context preservation"""
    
    def __init__(self, max_tokens: int = 800, overlap: int = 100, model: str = "gpt-3.5-turbo"):
        """
        Initialize TextChunker
        
        Args:
            max_tokens: Maximum tokens per chunk
            overlap: Number of overlapping tokens between chunks
            model: Model name for tokenization
        """
        self.max_tokens = max_tokens
        self.overlap = overlap
        
        try:
            self.encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            # Fallback to cl100k_base encoding
            self.encoding = tiktoken.get_encoding("cl100k_base")
    
    def chunk_text(self, text: str) -> List[dict]:
        """
        Split text into chunks with metadata
        
        Args:
            text: Text to chunk
            
        Returns:
            List of chunk dictionaries with text and metadata
        """
        # First try to split by sections (headers, paragraphs)
        sections = self._split_by_sections(text)
        
        # Then create chunks from sections
        chunks = []
        current_chunk = ""
        current_tokens = 0
        
        for section in sections:
            section_tokens = len(self.encoding.encode(section))
            
            # If section itself is too large, split it
            if section_tokens > self.max_tokens:
                # Save current chunk if it exists
                if current_chunk:
                    chunks.append({
                        'text': current_chunk.strip(),
                        'tokens': current_tokens,
                        'chunk_id': len(chunks)
                    })
                    current_chunk = ""
                    current_tokens = 0
                
                # Split large section
                large_chunks = self._split_large_section(section)
                chunks.extend(large_chunks)
            
            # If adding this section exceeds max, save current chunk
            elif current_tokens + section_tokens > self.max_tokens:
                if current_chunk:
                    chunks.append({
                        'text': current_chunk.strip(),
                        'tokens': current_tokens,
                        'chunk_id': len(chunks)
                    })
                
                # Start new chunk with overlap
                overlap_text = self._get_overlap_text(current_chunk, self.overlap)
                current_chunk = overlap_text + "\n\n" + section
                current_tokens = len(self.encoding.encode(current_chunk))
            
            else:
                # Add section to current chunk
                if current_chunk:
                    current_chunk += "\n\n" + section
                else:
                    current_chunk = section
                current_tokens += section_tokens
        
        # Add final chunk
        if current_chunk.strip():
            chunks.append({
                'text': current_chunk.strip(),
                'tokens': current_tokens,
                'chunk_id': len(chunks)
            })
        
        return chunks
    
    def _split_by_sections(self, text: str) -> List[str]:
        """
        Split text into semantic sections (by headers, paragraphs, etc.)
        
        Args:
            text: Text to split
            
        Returns:
            List of sections
        """
        # Split by double newlines (paragraphs)
        sections = re.split(r'\n\n+', text)
        
        # Filter out empty sections
        sections = [s.strip() for s in sections if s.strip()]
        
        return sections
    
    def _split_large_section(self, text: str) -> List[dict]:
        """
        Split a large section that exceeds max_tokens
        
        Args:
            text: Text section to split
            
        Returns:
            List of chunk dictionaries
        """
        # Split by sentences
        sentences = self._split_by_sentences(text)
        
        chunks = []
        current_chunk = ""
        current_tokens = 0
        
        for sentence in sentences:
            sentence_tokens = len(self.encoding.encode(sentence))
            
            # If single sentence is too large, split by tokens
            if sentence_tokens > self.max_tokens:
                if current_chunk:
                    chunks.append({
                        'text': current_chunk.strip(),
                        'tokens': current_tokens,
                        'chunk_id': len(chunks)
                    })
                    current_chunk = ""
                    current_tokens = 0
                
                # Split sentence by tokens
                token_chunks = self._split_by_tokens(sentence)
                chunks.extend(token_chunks)
            
            elif current_tokens + sentence_tokens > self.max_tokens:
                # Save current chunk
                chunks.append({
                    'text': current_chunk.strip(),
                    'tokens': current_tokens,
                    'chunk_id': len(chunks)
                })
                
                # Start new chunk with overlap
                overlap_text = self._get_overlap_text(current_chunk, self.overlap)
                current_chunk = overlap_text + " " + sentence
                current_tokens = len(self.encoding.encode(current_chunk))
            
            else:
                # Add sentence to current chunk
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence
                current_tokens += sentence_tokens
        
        # Add final chunk
        if current_chunk.strip():
            chunks.append({
                'text': current_chunk.strip(),
                'tokens': current_tokens,
                'chunk_id': len(chunks)
            })
        
        return chunks
    
    def _split_by_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences
        
        Args:
            text: Text to split
            
        Returns:
            List of sentences
        """
        # Simple sentence splitting (can be improved with NLTK)
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _split_by_tokens(self, text: str) -> List[dict]:
        """
        Split text by token count (last resort for very long segments)
        
        Args:
            text: Text to split
            
        Returns:
            List of chunk dictionaries
        """
        tokens = self.encoding.encode(text)
        chunks = []
        
        start = 0
        chunk_id = 0
        
        while start < len(tokens):
            end = start + self.max_tokens
            chunk_tokens = tokens[start:end]
            chunk_text = self.encoding.decode(chunk_tokens)
            
            chunks.append({
                'text': chunk_text,
                'tokens': len(chunk_tokens),
                'chunk_id': chunk_id
            })
            
            # Move start with overlap
            start = end - self.overlap
            chunk_id += 1
        
        return chunks
    
    def _get_overlap_text(self, text: str, overlap_tokens: int) -> str:
        """
        Get the last N tokens from text for overlap
        
        Args:
            text: Source text
            overlap_tokens: Number of tokens to extract
            
        Returns:
            Overlap text
        """
        if not text or overlap_tokens <= 0:
            return ""
        
        tokens = self.encoding.encode(text)
        
        if len(tokens) <= overlap_tokens:
            return text
        
        overlap = tokens[-overlap_tokens:]
        return self.encoding.decode(overlap)
    
    def get_statistics(self, chunks: List[dict]) -> dict:
        """
        Get statistics about chunks
        
        Args:
            chunks: List of chunk dictionaries
            
        Returns:
            Dictionary with statistics
        """
        if not chunks:
            return {
                'total_chunks': 0,
                'total_tokens': 0,
                'avg_tokens': 0,
                'min_tokens': 0,
                'max_tokens': 0
            }
        
        token_counts = [c['tokens'] for c in chunks]
        
        return {
            'total_chunks': len(chunks),
            'total_tokens': sum(token_counts),
            'avg_tokens': round(sum(token_counts) / len(token_counts), 2),
            'min_tokens': min(token_counts),
            'max_tokens': max(token_counts)
        }


# Example usage
if __name__ == "__main__":
    # Test text
    test_text = """
    This is a test document. It has multiple paragraphs.
    
    This is the second paragraph. It contains some more information about the topic.
    We want to test how the chunker handles different section sizes.
    
    This is the third paragraph. It's longer and contains more detailed information
    about various topics. The chunker should be able to handle this appropriately
    and create meaningful chunks that maintain context.
    """
    
    chunker = TextChunker(max_tokens=50, overlap=10)
    chunks = chunker.chunk_text(test_text)
    
    print(f"Created {len(chunks)} chunks:")
    for i, chunk in enumerate(chunks):
        print(f"\n--- Chunk {i} ({chunk['tokens']} tokens) ---")
        print(chunk['text'][:200])
    
    stats = chunker.get_statistics(chunks)
    print(f"\nStatistics: {stats}")

