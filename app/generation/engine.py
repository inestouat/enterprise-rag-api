from typing import List, Dict
import requests
from app.core.config import settings

class GenerationEngine:
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL
    
    def is_ready(self) -> bool:
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def generate(self, query: str, context: str, citations: List[Dict]) -> str:
        """Generate answer using Qwen2.5 with citations"""
        
        # Build prompt with citations
        prompt = f"""You are a helpful assistant. Answer the question using ONLY the provided context.
        
If the answer is not in the context, say "I don't have enough information to answer this."
        
Context:
{context}
        
Question: {query}
        
Provide a clear, concise answer. Include citation numbers [1], [2], etc. when referencing specific information."""
        
        # Call Ollama
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "num_predict": 500
                }
            },
            timeout=120
        )
        
        if response.status_code != 200:
            return f"Error: LLM returned {response.status_code}"
        
        result = response.json()
        return result.get("response", "No response generated")