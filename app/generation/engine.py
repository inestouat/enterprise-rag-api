from typing import List, Dict
import requests
from app.core.config import settings


class GenerationEngine:
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL
        print(f"🤖 Generation engine ready (model: {self.model})")

    def is_ready(self) -> bool:
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=3)
            return response.status_code == 200
        except:
            return False

    def generate(self, query: str, context: str, citations: List[Dict]) -> str:
        if not self.is_ready():
            return self._fallback(context)

        # Split context back into numbered parts for explicit citation
        parts = [p.strip() for p in context.split("\n\n") if p.strip()]
        c1 = parts[0] if len(parts) > 0 else ""
        c2 = parts[1] if len(parts) > 1 else ""
        c3 = parts[2] if len(parts) > 2 else ""

        prompt = f"""You are a precise document Q&A assistant.
Answer the question using ONLY the context provided below.

RULES — follow strictly:
1. Every sentence MUST end with [1], [2], or [3] to cite its source
2. Never write a sentence without a citation marker
3. Keep answer to 3-4 sentences maximum
4. If the answer is not in the context, say exactly:
   "I don't have enough information to answer this based on the provided documents."

Context:
[1] {c1[:600]}

[2] {c2[:600]}

[3] {c3[:600]}

Question: {query}

Answer (remember: every sentence must end with [1], [2], or [3]):"""

        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.0,
                        "num_predict": 400
                    }
                },
                timeout=120
            )

            if response.status_code != 200:
                return self._fallback(context)

            answer = response.json().get("response", "").strip()
            return answer if answer else self._fallback(context)

        except requests.exceptions.ConnectionError:
            return self._fallback(context)
        except requests.exceptions.Timeout:
            return self._fallback(context)
        except Exception as e:
            print(f"⚠️ Generation error: {e}")
            return self._fallback(context)

    def _fallback(self, context: str) -> str:
        lines = [l.strip() for l in context.split("\n") if l.strip()]
        preview = " ".join(lines[:4])[:400]
        return (
            f"⚠️ LLM unavailable — raw retrieved content:\n\n{preview}\n\n"
            f"Start Ollama with: ollama serve"
        )