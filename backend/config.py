from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    llm_provider: str = "gemini"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    ollama_base_url: str = "http://localhost:11434/api"
    ollama_model: str = "qwen2.5-coder:14b"
    ollama_think: bool | str | None = None
    ollama_timeout_seconds: float = 120.0
    ollama_tool_iterations: int = 8
    ollama_tools_enabled: bool = True
    github_token: str = ""
    obsidian_vault_path: str = "C:/Users/charl/Desktop/obi-secondbrain"
    whisper_model: str = "base"
    tts_voice: str = "en-US-GuyNeural"
    host: str = "0.0.0.0"
    port: int = 8000

    model_config = {
        "env_file": str(Path(__file__).with_name(".env")),
        "env_file_encoding": "utf-8",
    }


settings = Settings()
