# rag/retriever.py

from __future__ import annotations

import re
from typing import List, Dict, Any
from memory_system.vector_store.chroma_client import ChromaVectorStore


class VectorRetriever:
    """
    混合检索器：向量检索 + 关键词重排
    支持多表示索引：优先检索优化表示(retrieval_text)，返回原文(raw_content)
    """

    def __init__(self, vector_store: ChromaVectorStore):
        self.vector_store = vector_store

    @staticmethod
    def _tokenize(query: str) -> List[str]:
        tokens = re.findall(r"[\u4e00-\u9fffA-Za-z0-9]{2,}", query.lower())
        return list(dict.fromkeys(tokens))

    def _keyword_score(self, text: str, tokens: List[str]) -> float:
        if not tokens:
            return 0.0
        low = text.lower()
        hit = sum(1 for t in tokens if t in low)
        return hit / len(tokens)

    def retrieve(
        self,
        query: str,
        k: int = 5,
        where: Dict[str, Any] | None = None,
    ) -> List[Dict[str, Any]]:
        vector_results = self.vector_store.similarity_search_with_score(
            query=query,
            k=max(k * 3, 10),
            where=where,
        )

        tokens = self._tokenize(query)
        scored = []

        for doc, vector_distance in vector_results:
            metadata = doc.metadata or {}
            retrieval_text = doc.page_content or ""
            raw_content = metadata.get("raw_content", retrieval_text)

            keyword_score = self._keyword_score(retrieval_text, tokens)
            vector_score = 1 / (1 + max(vector_distance, 0))
            final_score = 0.7 * vector_score + 0.3 * keyword_score

            scored.append(
                {
                    "content": raw_content,
                    "retrieval_text": retrieval_text,
                    "metadata": metadata,
                    "score": round(final_score, 6),
                    "vector_distance": float(vector_distance),
                    "keyword_score": round(keyword_score, 6),
                }
            )

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:k]
