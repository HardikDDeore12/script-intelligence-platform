import pandas as pd
import chromadb
from chromadb.utils import embedding_functions
from src import config
import os
import requests
import numpy as np
from chromadb.api.types import EmbeddingFunction, Documents, Embeddings

class HuggingFaceAPIEmbeddingFunction(EmbeddingFunction):
    def __init__(self, model_name="sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.api_url = f"https://router.huggingface.co/hf-inference/models/{model_name}"
        self.headers = {
            "Authorization": f"Bearer {os.environ.get('HF_TOKEN')}",
            "Content-Type": "application/json"
        }

    def __call__(self, input: Documents) -> Embeddings:
        # Convert documents input safely
        texts = list(input) if isinstance(input, (list, tuple)) else [input]
        
        response = requests.post(
            self.api_url,
            headers=self.headers,
            json={"inputs": texts, "options": {"wait_for_model": True}},
            timeout=30
        )

        if response.status_code != 200:
            print(f"Hugging Face API Error ({response.status_code}): {response.text}", flush=True)
            raise Exception(f"HF API Error: {response.text}")

        data = response.json()

        # Handle nested 3D tensor responses [batch_size, seq_len, hidden_dim]
        try:
            arr = np.array(data)
            if arr.ndim == 3:
                # Token-level mean pooling to get 2D embeddings [batch_size, hidden_dim]
                arr = np.mean(arr, axis=1)
            return arr.tolist()
        except Exception as e:
            print(f"Embedding Parsing Error: {e}", flush=True)
            return data

    def name(self) -> str:
        return "sentence_transformer"
    
class VectorStoreManager:
    def __init__(self):
        # HuggingFace Embedding Function (100% Free & Local)
        self.embedding_fn = HuggingFaceAPIEmbeddingFunction()
        # Persistent Local ChromaDB Instance
        self.client = chromadb.PersistentClient(path=str(config.CHROMADB_DIR))
        self.collection = self.client.get_or_create_collection(
            name="movie_plots",
            embedding_function=self.embedding_fn,
            metadata={"hnsw:space": "cosine"}
        )

    def index_dataset(self, csv_path=None):
        """Dataset se plot descriptions ko vector database mein add karna"""
        if csv_path is None:
            csv_path = config.MASTER_DATASET_PATH

        df = pd.read_csv(csv_path)
        print(f"🚀 Indexing {len(df)} movies into local Vector DB...")

        documents = []
        metadatas = []
        ids = []

        for idx, row in df.iterrows():
            # Vector representation ke liye plot aur metadata combine kar rahe hain
            text_to_embed = f"Title: {row['title']}. Director: {row['director']}. Plot: {row['plot_summary']}"
            
            documents.append(text_to_embed)
            ids.append(str(row['movie_id']))
            metadatas.append({
                "movie_id": int(row['movie_id']),
                "title": str(row['title']),
                "release_year": int(row['release_year']),
                "director": str(row['director']),
                "main_cast": str(row['main_cast']),
                "budget": float(row['budget']),
                "revenue_worldwide": float(row['revenue_worldwide']),
                "roi": float(row['roi']),
                "plot_summary": str(row['plot_summary'])[:500],
                "poster_path": str(row.get('poster_path', ''))  # <-- Poster path added
            })

            # Batch upsert every 500 items
            if len(documents) >= 500:
                self.collection.upsert(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
                documents, metadatas, ids = [], [], []

        if documents:
            self.collection.upsert(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )

        print("🎉 Successfully indexed all movies locally!")

    def search_similar(self, query_plot: str, top_k: int = 5) -> list[dict]:
        """Query plot summary ke liye top-K similar benchmark movies find karna"""
        results = self.collection.query(
            query_texts=[query_plot],
            n_results=top_k
        )

        matches = []
        if results and results.get("metadatas"):
            metas = results["metadatas"][0]
            distances = results["distances"][0] if "distances" in results else [0]*len(metas)

            for meta, dist in zip(metas, distances):
                # Cosine distance to similarity percentage conversion
                similarity_score = round(max(0, (1 - dist)) * 100, 2)
                meta["similarity_score"] = similarity_score
                matches.append(meta)

        return matches