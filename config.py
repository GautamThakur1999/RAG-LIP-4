from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    groq_api_key: str = ""
    llm_model: str = "llama-3.3-70b-versatile"
    embed_model: str = "BAAI/bge-small-en-v1.5"
    top_k: int = 5
    score_threshold: float = 0.35
    max_sentences: int = 3

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()

if __name__ == "__main__":
    print("Loaded settings:")
    print(settings.model_dump())
