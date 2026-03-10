# memory_system/memory_manager.py

from __future__ import annotations

import datetime
import re
from typing import Callable, Dict, Any, List

from ingestion.pdf_ingest import PDFIngestor
from memory_system.vector_store.chroma_client import ChromaVectorStore
from rag.retriever import VectorRetriever
from langchain.text_splitter import RecursiveCharacterTextSplitter


class MemoryManager:
    """
    全维投研记忆系统
    支持：重要性筛选、时效性管理、长短期记忆协同
    """

    def __init__(self, persist_dir: str, importance_judge: Callable[[str], int] | None = None):
        self.vector_store = ChromaVectorStore(persist_dir)
        self.retriever = VectorRetriever(self.vector_store)
        self.pdf_ingestor = PDFIngestor()
        self.importance_judge = importance_judge

        self.splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        self.ttl_days_by_category = {
            "fact": 365,
            "opinion": 90,
            "conclusion": 180,
            "report_segment": 730,
        }

    def _estimate_importance(self, message: str) -> int:
        """兜底评分：无LLM时通过启发式评估重要性（1-10）。"""
        score = 4
        if re.search(r"\d{4}|\d+%|\d+亿|\d+万", message):
            score += 2
        if any(k in message for k in ["结论", "建议", "风险", "投资", "政策", "市场规模"]):
            score += 2
        if len(message) > 120:
            score += 1
        return max(1, min(10, score))

    def should_store_in_long_term(self, message: str, threshold: int = 7) -> bool:
        if not message:
            return False
        try:
            if self.importance_judge:
                importance = int(self.importance_judge(message))
            else:
                importance = self._estimate_importance(message)
        except Exception:
            importance = self._estimate_importance(message)

        return importance >= threshold

    @staticmethod
    def _iso_now() -> str:
        return datetime.datetime.now(datetime.timezone.utc).isoformat()

    @staticmethod
    def _build_expires_at(now_iso: str, ttl_days: int) -> str:
        ts = datetime.datetime.fromisoformat(now_iso)
        return (ts + datetime.timedelta(days=ttl_days)).isoformat()

    def save_insight(self, content: str, category: str, metadata: dict):
        if not content:
            return

        if not self.should_store_in_long_term(content):
            print("🧠 [Memory] 重要性不足，已跳过长期存储")
            return

        now_iso = self._iso_now()
        ttl_days = self.ttl_days_by_category.get(category, 180)

        meta = metadata.copy()
        meta.update(
            {
                "category": category,
                "ingest_time": now_iso,
                "expires_at": self._build_expires_at(now_iso, ttl_days),
                "importance_threshold": 7,
                "type": "agent_memory",
            }
        )

        chunks = [content] if len(content) < 500 else self.splitter.split_text(content)
        enriched_metas = []
        for i, chunk in enumerate(chunks):
            chunk_meta = meta.copy()
            chunk_meta["chunk_index"] = i
            chunk_meta["raw_content"] = chunk
            enriched_metas.append(chunk_meta)

        self.vector_store.add_texts(chunks, enriched_metas)
        print(f"🧠 [Memory] 已存储 {len(chunks)} 条 {category} 记忆")

    def ingest_pdf(self, file_path: str, metadata: dict):
        raw_text = self.pdf_ingestor.ingest(file_path)
        chunks = self.splitter.split_text(raw_text)

        now_iso = self._iso_now()
        metadatas = []
        for idx, chunk in enumerate(chunks):
            m = metadata.copy()
            m.update(
                {
                    "ingest_time": now_iso,
                    "expires_at": self._build_expires_at(now_iso, 3650),
                    "chunk_index": idx,
                    "type": "pdf_file",
                    "raw_content": chunk,
                }
            )
            metadatas.append(m)

        self.vector_store.add_texts(chunks, metadatas)

    def recall_memory(self, query: str, category: str | None = None, k: int = 5) -> List[str]:
        now = datetime.datetime.now(datetime.timezone.utc)
        where: Dict[str, Any] | None = {"type": "agent_memory"}
        if category:
            where["category"] = category

        results = self.retriever.retrieve(query, k=k * 2, where=where)

        valid_results = []
        for item in results:
            metadata = item.get("metadata", {})
            expires_at = metadata.get("expires_at")
            if expires_at:
                try:
                    expire_ts = datetime.datetime.fromisoformat(expires_at)
                    if expire_ts < now:
                        continue
                except Exception:
                    pass
            valid_results.append(item["content"])

        return valid_results[:k]


memory_manager = MemoryManager(persist_dir="./knowledge_base/vector_store")
