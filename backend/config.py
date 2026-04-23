from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    gemini_api_key: str
    github_token: str = ""
    obsidian_vault_path: str = "C:/Users/charl/Desktop/obi-secondbrain"
    whisper_model: str = "base"
    tts_voice: str = "en-US-GuyNeural"
    host: str = "0.0.0.0"
    port: int = 8000

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
