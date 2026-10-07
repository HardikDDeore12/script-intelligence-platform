import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# Dataset Paths
DATA_RAW_DIR = BASE_DIR / "data" / "raw"
DATA_PROCESSED_DIR = BASE_DIR / "data" / "processed"
MASTER_DATASET_PATH = DATA_PROCESSED_DIR / "master_movie_dataset.csv"

# Local Vector Store Path (Zero-Cost Storage)
CHROMADB_DIR = BASE_DIR / "data" / "chroma_db"

# Free HuggingFace Embedding Model
FREE_EMBEDDING_MODEL = "all-MiniLM-L6-v2"

TMDB_API_KEY = os.getenv("TMDB_API_KEY", "")