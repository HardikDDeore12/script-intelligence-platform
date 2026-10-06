import pandas as pd
import chromadb
from chromadb.utils import embedding_functions
from src import config

class VectorStoreManager:
    def __init__(self):
        # HuggingFace Embedding Function (100% Free & Local)
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=config.FREE_EMBEDDING_MODEL
        )
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