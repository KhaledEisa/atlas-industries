# src/retriever.py
from src.ingest import load_index, build_embeddings
from src.settings import settings
from pathlib import Path

embeddings  = build_embeddings()
faiss_index = load_index(Path(settings.vector_store_path), embeddings)