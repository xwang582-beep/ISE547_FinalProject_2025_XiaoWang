"""
FAQ Generator Module
Uses LLM to generate question-answer pairs from text chunks
"""

from typing import List, Dict, Optional
import json
import time
from openai import OpenAI
from anthropic import Anthropic
import numpy as np


class FAQGenerator:
    """Generate FAQs from text chunks using LLM"""
    
    def __init__(
        self,
        api_key: str,
        model: str = "gpt-3.5-turbo",
        max_faqs_per_chunk: int = 3,
        temperature: float = 0.7,
        provider: str = "openai"
    ):
        """
        Initialize FAQ Generator
        
        Args:
            api_key: API key for LLM provider
            model: Model name to use
            max_faqs_per_chunk: Maximum FAQs to generate per chunk
            temperature: Sampling temperature (0-1)
            provider: LLM provider ("openai" or "anthropic")
        """
        self.model = model
        self.max_faqs_per_chunk = max_faqs_per_chunk
        self.temperature = temperature
        self.provider = provider.lower()
        
        if self.provider == "openai":
            self.client = OpenAI(api_key=api_key)
        elif self.provider == "anthropic":
            self.client = Anthropic(api_key=api_key)
        else:
            raise ValueError(f"Unsupported provider: {provider}. Use 'openai' or 'anthropic'")
    
    def generate_faqs_from_chunk(self, chunk_text: str, chunk_id: int = 0) -> List[Dict]:
        """
        Generate FAQs from a single text chunk
        
        Args:
            chunk_text: Text chunk to process
            chunk_id: Identifier for the chunk
            
        Returns:
            List of FAQ dictionaries with 'question' and 'answer' keys
        """
        prompt = self._create_prompt(chunk_text)
        
        try:
            response = self._call_llm(prompt)
            faqs = self._parse_response(response)
            
            # Add metadata
            for i, faq in enumerate(faqs):
                faq['chunk_id'] = chunk_id
                faq['faq_id'] = f"{chunk_id}_{i}"
            
            return faqs
        
        except Exception as e:
            print(f"Error generating FAQs for chunk {chunk_id}: {str(e)}")
            return []
    
    def generate_faqs_batch(self, chunks: List[Dict], verbose: bool = True) -> List[Dict]:
        """
        Generate FAQs from multiple chunks
        
        Args:
            chunks: List of chunk dictionaries
            verbose: Whether to print progress
            
        Returns:
            List of all generated FAQs
        """
        all_faqs = []
        
        for i, chunk in enumerate(chunks):
            if verbose:
                print(f"Processing chunk {i+1}/{len(chunks)}...")
            
            faqs = self.generate_faqs_from_chunk(
                chunk['text'],
                chunk_id=chunk.get('chunk_id', i)
            )
            
            all_faqs.extend(faqs)
            
            # Rate limiting - sleep briefly between API calls
            if i < len(chunks) - 1:
                time.sleep(0.5)
        
        if verbose:
            print(f"\nGenerated {len(all_faqs)} FAQs from {len(chunks)} chunks")
        
        return all_faqs
    
    def _create_prompt(self, text: str) -> str:
        """
        Create the prompt for FAQ generation
        
        Args:
            text: Text chunk to generate FAQs from
            
        Returns:
            Formatted prompt
        """
        prompt = f"""You are an expert at creating helpful Frequently Asked Questions (FAQs) from documents.

Based on the following text, generate {self.max_faqs_per_chunk} relevant and useful question-answer pairs.

Guidelines:
1. Questions should be natural and reflect what users would actually ask
2. Answers should be clear, concise, and based ONLY on the provided text
3. Do not make up information - if something isn't in the text, don't include it
4. Focus on the most important and useful information
5. Avoid yes/no questions - prefer questions that elicit detailed answers

Text:
{text}

Please provide your response in the following JSON format:
{{
    "faqs": [
        {{
            "question": "Question text here?",
            "answer": "Answer text here."
        }},
        ...
    ]
}}

Generate exactly {self.max_faqs_per_chunk} FAQs."""

        return prompt
    
    def _call_llm(self, prompt: str) -> str:
        """
        Call the LLM API
        
        Args:
            prompt: Prompt to send
            
        Returns:
            LLM response text
        """
        if self.provider == "openai":
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that generates FAQs from documents."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=1500
            )
            return response.choices[0].message.content
        
        elif self.provider == "anthropic":
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                temperature=self.temperature,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return response.content[0].text
        
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    def _parse_response(self, response: str) -> List[Dict]:
        """
        Parse LLM response into FAQ dictionaries
        
        Args:
            response: Raw LLM response
            
        Returns:
            List of FAQ dictionaries
        """
        try:
            # Try to find JSON in the response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                data = json.loads(json_str)
                
                if 'faqs' in data:
                    return data['faqs']
                else:
                    return []
            else:
                # Fallback: try to parse manually
                return self._parse_response_manual(response)
        
        except json.JSONDecodeError:
            # Fallback to manual parsing
            return self._parse_response_manual(response)
    
    def _parse_response_manual(self, response: str) -> List[Dict]:
        """
        Manually parse response if JSON parsing fails
        
        Args:
            response: Raw LLM response
            
        Returns:
            List of FAQ dictionaries
        """
        faqs = []
        
        # Split by question markers
        parts = response.split('Q:')
        
        for part in parts[1:]:  # Skip first empty part
            if 'A:' in part:
                q_text, a_text = part.split('A:', 1)
                question = q_text.strip()
                answer = a_text.strip()
                
                # Clean up
                question = question.replace('**', '').strip()
                answer = answer.replace('**', '').strip()
                
                # Remove any trailing separators
                answer = answer.split('\n\n')[0]
                
                if question and answer:
                    faqs.append({
                        'question': question,
                        'answer': answer
                    })
        
        return faqs
    
    def deduplicate_faqs(
        self,
        faqs: List[Dict],
        similarity_threshold: float = 0.85
    ) -> List[Dict]:
        """
        Remove duplicate or very similar FAQs
        
        Args:
            faqs: List of FAQ dictionaries
            similarity_threshold: Similarity threshold for deduplication (0-1)
            
        Returns:
            Deduplicated list of FAQs
        """
        if not faqs:
            return []
        
        # Simple deduplication based on question text similarity
        unique_faqs = []
        seen_questions = []
        
        for faq in faqs:
            question = faq['question'].lower().strip()
            
            # Check if question is too similar to existing ones
            is_duplicate = False
            for seen_q in seen_questions:
                similarity = self._calculate_similarity(question, seen_q)
                if similarity >= similarity_threshold:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_faqs.append(faq)
                seen_questions.append(question)
        
        return unique_faqs
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate simple word-based similarity between two texts
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score (0-1)
        """
        # Simple word overlap similarity
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    def rank_faqs(self, faqs: List[Dict]) -> List[Dict]:
        """
        Rank FAQs by importance (simple heuristic)
        
        Args:
            faqs: List of FAQ dictionaries
            
        Returns:
            Sorted list of FAQs
        """
        # Simple ranking based on answer length and question quality
        for faq in faqs:
            score = 0
            
            # Longer answers are often more informative
            score += min(len(faq['answer'].split()) / 50, 1.0) * 40
            
            # Questions with "what", "how", "why" are often more useful
            question_lower = faq['question'].lower()
            if any(word in question_lower for word in ['what', 'how', 'why', 'when', 'where']):
                score += 30
            
            # Longer questions often indicate more specific queries
            score += min(len(faq['question'].split()) / 15, 1.0) * 30
            
            faq['score'] = score
        
        # Sort by score (highest first)
        sorted_faqs = sorted(faqs, key=lambda x: x.get('score', 0), reverse=True)
        
        return sorted_faqs


# Example usage
if __name__ == "__main__":
    # This is just example code - need actual API key to run
    print("FAQ Generator module loaded successfully")
    print("To use: Initialize with your API key and call generate_faqs_from_chunk()")

