import json
from pathlib import Path
from typing import List, Dict, Any

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from app.config import CHUNKS_DIR, INDEXES_DIR, ensure_directories


class VectorStore:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        self.index = None
        self.chunk_metadata: List[Dict[str, Any]] = []
        self.index_path = INDEXES_DIR / "chunks.faiss"
        self.metadata_path = INDEXES_DIR / "chunks_metadata.json"

    def load_chunks(self) -> List[Dict[str, Any]]:
        path = CHUNKS_DIR / "chunks.jsonl"
        chunks = []

        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                chunks.append(json.loads(line))

        return chunks

    def build_index(self) -> None:
        ensure_directories()

        chunks = self.load_chunks()
        self.chunk_metadata = chunks

        texts = [chunk["text"] for chunk in chunks]
        embeddings = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=True)

        embeddings = embeddings.astype("float32")

        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(embeddings)

        faiss.write_index(self.index, str(self.index_path))

        with open(self.metadata_path, "w", encoding="utf-8") as f:
            json.dump(self.chunk_metadata, f, indent=2, ensure_ascii=False)

        print(f"Saved FAISS index to: {self.index_path}")
        print(f"Saved metadata to: {self.metadata_path}")
        print(f"Indexed {len(chunks)} chunks.")

    def load_index(self) -> None:
        if not self.index_path.exists():
            raise FileNotFoundError(f"Index file not found: {self.index_path}")

        if not self.metadata_path.exists():
            raise FileNotFoundError(f"Metadata file not found: {self.metadata_path}")

        self.index = faiss.read_index(str(self.index_path))

        with open(self.metadata_path, "r", encoding="utf-8") as f:
            self.chunk_metadata = json.load(f)

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        if self.index is None:
            self.load_index()

        query_embedding = self.model.encode([query], convert_to_numpy=True)
        query_embedding = query_embedding.astype("float32")

        distances, indices = self.index.search(query_embedding, top_k)

        results = []
        for rank, idx in enumerate(indices[0]):
            if idx == -1:
                continue

            chunk = self.chunk_metadata[idx].copy()
            chunk["vector_distance"] = float(distances[0][rank])
            results.append(chunk)

        return results


def main():
    vs = VectorStore()
    vs.build_index()


if __name__ == "__main__":
    main()