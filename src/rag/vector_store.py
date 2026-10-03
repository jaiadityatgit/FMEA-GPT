"""ChromaDB vector store manager for FMEA-GPT aerospace RAG."""
import os
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

from .config import RAGConfig
from .chunker import TextChunk


class ChromaVectorStore:
    """Manages the local persistent ChromaDB collection for aerospace documents."""

    def __init__(self, config: Optional[RAGConfig] = None):
        self.config = config or RAGConfig()
        self.config.ensure_directories()
        
        # Initialize persistent client
        self.client = chromadb.PersistentClient(
            path=str(self.config.chroma_dir),
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Setup embedding function
        self.embedding_fn = self._get_embedding_function()
        
        # Initialize or get collection
        self.collection = self.client.get_or_create_collection(
            name=self.config.collection_name,
            embedding_function=self.embedding_fn,
            metadata={"hnsw:space": "cosine"}
        )

    def _get_embedding_function(self):
        """Initialize local ONNX embedding function (all-MiniLM-L6-v2)."""
        # Uses onnxruntime for fast local CPU inference without PyTorch/AppLocker DLL conflicts
        return embedding_functions.DefaultEmbeddingFunction()

    def add_chunks(self, chunks: List[TextChunk], batch_size: int = 64) -> int:
        """Add discrete text chunks into the vector store in batches."""
        if not chunks:
            return 0

        total_added = 0
        total_chunks = len(chunks)
        print(f"Indexing {total_chunks} chunks into ChromaDB collection '{self.config.collection_name}'...")

        for i in range(0, total_chunks, batch_size):
            batch = chunks[i : i + batch_size]
            
            ids = [c.chunk_id for c in batch]
            documents = [c.text for c in batch]
            metadatas = []
            
            for c in batch:
                meta = {
                    "doc_id": c.doc_id,
                    "source_file": c.source_file,
                    "doc_title": c.doc_title,
                    "publisher": c.publisher,
                    "document_type": c.document_type,
                    "page_number": int(c.page_number),
                    "chunk_index": int(c.chunk_index),
                }
                # Include extra metadata fields if primitive types
                for k, v in c.metadata.items():
                    if isinstance(v, (str, int, float, bool)):
                        meta[k] = v
                metadatas.append(meta)

            # Upsert into ChromaDB
            self.collection.upsert(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )
            total_added += len(batch)
            print(f"  Indexed batch {i // batch_size + 1}: {total_added}/{total_chunks} chunks")

        return total_added

    def query(
        self,
        query_text: str,
        top_k: int = 5,
        where: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Query the vector store for semantic similarity."""
        results = self.collection.query(
            query_texts=[query_text],
            n_results=top_k,
            where=where,
            include=["documents", "metadatas", "distances"]
        )
        return results

    def get_stats(self) -> Dict[str, Any]:
        """Return collection count and storage info."""
        count = self.collection.count()
        return {
            "collection_name": self.config.collection_name,
            "document_count": count,
            "storage_path": str(self.config.chroma_dir),
            "embedding_model": self.config.embedding_model_name
        }

    def reset(self) -> None:
        """Reset/clear the collection for re-indexing."""
        self.client.delete_collection(self.config.collection_name)
        self.collection = self.client.create_collection(
            name=self.config.collection_name,
            embedding_function=self.embedding_fn,
            metadata={"hnsw:space": "cosine"}
        )
