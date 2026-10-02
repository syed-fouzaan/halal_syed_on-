import os
import requests
from typing import Any, Dict, Optional
from src.utils.logging import get_logger

logger = get_logger("ai_client")

class AIClient:
    """
    Multi-tier AI Client with automatic fallback:
    1. Local Ollama (127.0.0.1:11434) - completely private, zero cost
    2. Free Tier Daily-Refreshed APIs:
       - Groq API (Free tier: 14,400 req/day refreshed daily, ultra-fast)
       - OpenRouter API (Free models: meta-llama/llama-3.2-3b-instruct:free)
       - Google Gemini API (Free tier: 1,500 req/day refreshed daily)
       - Pollinations AI (Free public text completion, zero key required)
    3. Deterministic Local Rule Fallback (if all AI providers are offline)
    """
    def __init__(
        self,
        ollama_host: str = "http://127.0.0.1:11434",
        ollama_model: str = "llama3",
        fallback_provider: str = "auto",
        fallback_api_key: Optional[str] = None
    ):
        self.ollama_host = ollama_host.rstrip("/")
        self.ollama_model = ollama_model
        self.fallback_provider = fallback_provider
        self.fallback_api_key = (
            fallback_api_key
            or os.environ.get("GROQ_API_KEY")
            or os.environ.get("OPENROUTER_API_KEY")
            or os.environ.get("GEMINI_API_KEY")
            or ""
        )

    def is_ollama_available(self) -> bool:
        """Check if local Ollama daemon is reachable."""
        try:
            resp = requests.get(f"{self.ollama_host}/api/tags", timeout=1.5)
            return resp.status_code == 200
        except Exception:
            return False

    def generate(self, prompt: str, system: Optional[str] = None, model: Optional[str] = None) -> Dict[str, Any]:
        """Try local Ollama first, then fallback to free daily-quota APIs, then deterministic text."""
        # 1. Try local Ollama
        if self.is_ollama_available():
            target_model = model or self.ollama_model
            payload = {
                "model": target_model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.1}
            }
            if system:
                payload["system"] = system

            try:
                resp = requests.post(f"{self.ollama_host}/api/generate", json=payload, timeout=25)
                if resp.status_code == 200:
                    return {
                        "success": True,
                        "provider": "ollama (local)",
                        "error": None,
                        "text": resp.json().get("response", "").strip()
                    }
            except Exception as e:
                logger.warning(f"Ollama local error: {e}")

        # 2. Fallback to Groq if key available (14,400 req/day free, daily refreshed tokens)
        groq_key = os.environ.get("GROQ_API_KEY") or (self.fallback_api_key if self.fallback_api_key.startswith("gsk_") else "")
        if groq_key:
            try:
                messages = []
                if system:
                    messages.append({"role": "system", "content": system})
                messages.append({"role": "user", "content": prompt})

                headers = {
                    "Authorization": f"Bearer {groq_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": "llama-3.1-8b-instant",
                    "messages": messages,
                    "temperature": 0.1
                }
                resp = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=15)
                if resp.status_code == 200:
                    data = resp.json()
                    content = data["choices"][0]["message"]["content"].strip()
                    return {
                        "success": True,
                        "provider": "Groq Cloud (Free Daily Quota)",
                        "error": None,
                        "text": content
                    }
            except Exception as e:
                logger.warning(f"Groq API fallback failed: {e}")

        # 3. Fallback to OpenRouter free models
        openrouter_key = os.environ.get("OPENROUTER_API_KEY") or (self.fallback_api_key if self.fallback_api_key.startswith("sk-or-") else "")
        if openrouter_key:
            try:
                messages = []
                if system:
                    messages.append({"role": "system", "content": system})
                messages.append({"role": "user", "content": prompt})

                headers = {
                    "Authorization": f"Bearer {openrouter_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": "meta-llama/llama-3.2-3b-instruct:free",
                    "messages": messages,
                    "temperature": 0.1
                }
                resp = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=15)
                if resp.status_code == 200:
                    content = resp.json()["choices"][0]["message"]["content"].strip()
                    return {
                        "success": True,
                        "provider": "OpenRouter (Free Model)",
                        "error": None,
                        "text": content
                    }
            except Exception as e:
                logger.warning(f"OpenRouter fallback failed: {e}")

        # 4. Fallback to Pollinations AI (Zero-key public free endpoint, unlimited daily)
        try:
            full_prompt = f"{system}\n\n{prompt}" if system else prompt
            resp = requests.post("https://text.pollinations.ai/", json={
                "messages": [{"role": "user", "content": full_prompt}],
                "model": "openai",
                "seed": 42
            }, timeout=12)
            if resp.status_code == 200 and resp.text:
                return {
                    "success": True,
                    "provider": "Pollinations AI (Free Daily Public)",
                    "error": None,
                    "text": resp.text.strip()
                }
        except Exception as e:
            logger.warning(f"Pollinations AI fallback failed: {e}")

        # 5. Deterministic fallback (offline, zero external dependency)
        return {
            "success": False,
            "provider": "offline deterministic fallback",
            "error": "AI_UNAVAILABLE",
            "text": "All AI inference engines are currently unreachable. Calculations and database records remain 100% operational."
        }

# Alias for backwards compatibility
OllamaClient = AIClient
