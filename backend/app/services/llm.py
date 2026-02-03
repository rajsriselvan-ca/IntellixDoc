from typing import List, Dict, Optional
from app.config import settings
import httpx


class LLMService:
    def __init__(self):
        self.provider = settings.llm_provider.lower()
        self.groq_api_key = settings.groq_api_key
        self.openai_api_key = settings.openai_api_key
        self.anthropic_api_key = settings.anthropic_api_key
        self.ollama_base_url = settings.ollama_base_url
    
    async def generate_response(
        self,
        query: str,
        context: str,
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """Generate response using the configured LLM provider."""
        
        if self.provider == "groq":
            return await self._generate_groq(query, context, chat_history)
        elif self.provider == "ollama":
            return await self._generate_ollama(query, context, chat_history)
        elif self.provider == "openai":
            return await self._generate_openai(query, context, chat_history)
        elif self.provider == "claude":
            return await self._generate_claude(query, context, chat_history)
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")
    
    async def _generate_groq(self, query: str, context: str, chat_history: Optional[List[Dict[str, str]]]) -> str:
        """Generate response using Groq API."""
        try:
            from groq import Groq
            client = Groq(api_key=self.groq_api_key)
            
            system_prompt = """You are a helpful assistant that answers questions based on the provided context from documents. 
Always cite the relevant parts of the context in your answer. If the context doesn't contain enough information, say so."""
            
            messages = [{"role": "system", "content": system_prompt}]
            
            if chat_history:
                messages.extend(chat_history[-5:])  # Last 5 messages for context
            
            messages.append({
                "role": "user",
                "content": f"Context from documents:\n\n{context}\n\nQuestion: {query}\n\nAnswer based on the context above:"
            })
            
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=messages,
                temperature=0.7,
                max_tokens=1024
            )
            
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"Groq API error: {str(e)}")
    
    async def _generate_ollama(self, query: str, context: str, chat_history: Optional[List[Dict[str, str]]]) -> str:
        """Generate response using Ollama (local)."""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                prompt = f"""Context from documents:

{context}

Question: {query}

Answer based on the context above:"""
                
                response = await client.post(
                    f"{self.ollama_base_url}/api/generate",
                    json={
                        "model": "llama2",
                        "prompt": prompt,
                        "stream": False
                    }
                )
                response.raise_for_status()
                result = response.json()
                return result.get("response", "No response generated")
        except Exception as e:
            raise Exception(f"Ollama API error: {str(e)}")
    
    async def _generate_openai(self, query: str, context: str, chat_history: Optional[List[Dict[str, str]]]) -> str:
        """Generate response using OpenAI API."""
        if not self.openai_api_key:
            raise ValueError("OpenAI API key is not set")
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=self.openai_api_key)
            
            system_prompt = """You are a helpful assistant that answers questions based on the provided context from documents. 
Always cite the relevant parts of the context in your answer."""
            
            messages = [{"role": "system", "content": system_prompt}]
            
            if chat_history:
                messages.extend(chat_history[-5:])
            
            messages.append({
                "role": "user",
                "content": f"Context from documents:\n\n{context}\n\nQuestion: {query}\n\nAnswer based on the context above:"
            })
            
            response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.7,
                max_tokens=1024
            )
            
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")
    
    async def _generate_claude(self, query: str, context: str, chat_history: Optional[List[Dict[str, str]]]) -> str:
        """Generate response using Anthropic Claude API."""
        if not self.anthropic_api_key:
            raise ValueError("Anthropic API key is not set")
        try:
            from anthropic import AsyncAnthropic
            client = AsyncAnthropic(api_key=self.anthropic_api_key)
            
            prompt = f"""Context from documents:

{context}

Question: {query}

Answer based on the context above:"""
            
            message = await client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1024,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return message.content[0].text
        except Exception as e:
            raise Exception(f"Claude API error: {str(e)}")


llm_service = LLMService()

