import sys
from pathlib import Path

# Project root directory ko Python path mein add karna
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.vector_store import VectorStoreManager

if __name__ == "__main__":
    print("🚀 Local Vector Store Indexing Process Starting...")
    store = VectorStoreManager()
    store.index_dataset()
    print("✅ Indexing Complete!")