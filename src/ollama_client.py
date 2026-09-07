"""Ollama 호환 API를 호출하는 공통 클라이언트."""

import os

import requests


class OllamaClient:
    def __init__(self, base_url=None, model=None):
        self.base_url = (
            base_url
            or os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
        ).rstrip("/")

        self.model = (
            model
            or os.environ.get("OLLAMA_MODEL", "gemma4:31b")
        )

    def chat(self, messages, tools=None):
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": 0,
                "num_ctx": 65536,
                "num_predict": 4096,
            },
        }

        if tools:
            payload["tools"] = tools

        response = requests.post(
            f"{self.base_url}/api/chat",
            json=payload,
            timeout=(10, 300),
        )

        if not response.ok:
            raise RuntimeError(
                f"Ollama HTTP {response.status_code}: "
                f"{response.text[:2000]}"
            )

        data = response.json()

        if not isinstance(data, dict):
            raise RuntimeError("Ollama 응답이 JSON 객체가 아닙니다.")

        message = data.get("message")
        if not isinstance(message, dict):
            raise RuntimeError("Ollama 응답에 message 객체가 없습니다.")

        return data
