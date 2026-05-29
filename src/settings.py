from pathlib import Path

import yaml
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Paths
    docs_path: str = str(_ROOT / "atlas-corpus" / "atlas" / "data" / "docs")
    vector_store_path: str = str(_ROOT / "data" / "vector_store")

    # Embeddings — BAAI/bge-m3 chosen for native EN+AR support with strong
    # cross-lingual recall; downloads ~570 MB on first run, cached afterwards
    embedding_model: str = "BAAI/bge-m3"

    # Chunking
    chunk_size: int = 512
    chunk_overlap: int = 64

    # Retrieval
    top_k: int = 5

    # LangGraph runtime limits
    max_steps: int = 10
    max_tool_calls: int = 3

    # LLM providers (fill in .env)
    google_api_key: str = ""
    groq_api_key: str = ""


settings = Settings()



def load_rai_config() -> dict:
    config_path = Path("config/RAI_Config.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

rai_config = load_rai_config()