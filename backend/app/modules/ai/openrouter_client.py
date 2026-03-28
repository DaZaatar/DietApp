import httpx
from fastapi import HTTPException

from app.core.config import settings


class OpenRouterClient:
    base_url = "https://openrouter.ai/api/v1"

    async def chat_completion(self, prompt: str) -> str:
        if not settings.openrouter_api_key:
            raise HTTPException(status_code=500, detail="OPENROUTER_API_KEY is not configured")

        payload = {
            "model": settings.openrouter_model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0,
        }
        headers = {
            "Authorization": f"Bearer {settings.openrouter_api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers,
            )

        if response.status_code >= 400:
            raise HTTPException(status_code=502, detail=f"OpenRouter error: {response.text}")

        data = response.json()
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise HTTPException(status_code=502, detail="Malformed OpenRouter response") from exc
