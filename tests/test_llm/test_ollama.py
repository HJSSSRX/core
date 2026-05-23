from __future__ import annotations

from forhacker.llm.ollama import OllamaBackend


def test_ollama_backend_default_url():
    backend = OllamaBackend(model="llama3:8b")
    assert backend.model_name == "llama3:8b"


def test_ollama_backend_custom_url():
    backend = OllamaBackend(model="mistral:7b", base_url="http://192.168.1.100:11434/v1")
    assert backend.model_name == "mistral:7b"
