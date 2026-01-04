# rag/retriever.py

from typing import List
from memory_system.vector_store.chroma_client import ChromaVectorStore


class VectorRetriever:
    """
    【原 knowledge_engine.py 中的 RAG 检索 + keyword filter】
    """

    def __init__(self, vector_store: ChromaVectorStore):
        self.vector_store = vector_store

    def retrieve(self, query: str, k: int = 5) -> List[str]:
        results = self.vector_store.similarity_search_with_score(
            query=query,
            k=k
        )

        filtered_docs = []

        for doc, score in results:
            # === 原 keyword_filter 逻辑复制 ===
            if query.lower() in doc.page_content.lower():
                filtered_docs.append(doc.page_content)

        if not filtered_docs:
            # fallback：返回原始 TopK
            filtered_docs = [doc.page_content for doc, _ in results]

        return filtered_docs
