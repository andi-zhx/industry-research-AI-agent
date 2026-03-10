# knowledge_engine.py
import os
import re
import shutil
import datetime
from typing import List, Tuple, Dict

import chromadb
from chromadb.utils import embedding_functions
from langchain.text_splitter import RecursiveCharacterTextSplitter
import pdfplumber

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "../../"))
CHROMA_DATA_PATH = os.path.join(PROJECT_ROOT, "chroma_db")
os.makedirs(CHROMA_DATA_PATH, exist_ok=True)

client = chromadb.PersistentClient(path=CHROMA_DATA_PATH)
emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="BAAI/bge-m3")
collection = client.get_or_create_collection(name="industry_research_db", embedding_function=emb_fn)


class KnowledgeBaseManager:
    """
    知识库管理器（稳定版）
    - 避免在 import 时初始化 Chroma，防止 Streamlit 启动阶段崩溃
    - 对损坏的本地 Chroma 数据目录进行自动隔离并重建
    """

    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=80)
        self._client = None
        self._collection = None
        self._emb_fn = None

    @staticmethod
    def _extract_keywords(text: str) -> List[str]:
        return list(dict.fromkeys(re.findall(r"[\u4e00-\u9fffA-Za-z0-9]{2,}", text.lower())))

    @staticmethod
    def _keyword_score(text: str, query: str) -> float:
        tokens = KnowledgeBaseManager._extract_keywords(query)
        if not tokens:
            return 0.0
        low = text.lower()
        hit = sum(1 for token in tokens if token in low)
        return hit / len(tokens)

    @staticmethod
    def _build_retrieval_text(chunk: str) -> str:
        """多表示索引：压缩为检索表示（关键词+数字+首句），提升召回性能。"""
        first_sentence = chunk.strip().split("。", 1)[0][:200]
        numbers = re.findall(r"\d{4}|\d+\.\d+%|\d+%|\d+亿|\d+万", chunk)
        keywords = KnowledgeBaseManager._extract_keywords(chunk)[:15]
        return f"摘要:{first_sentence}\n关键词:{' '.join(keywords)}\n关键数字:{' '.join(numbers[:8])}".strip()

    def _rotate_corrupted_store(self, base_path: str) -> str:
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        broken_path = f"{base_path}_corrupted_{ts}"
        if os.path.exists(base_path):
            shutil.move(base_path, broken_path)
        os.makedirs(base_path, exist_ok=True)
        return broken_path

    def _ensure_collection(self):
        if self._collection is not None:
            return self._collection

        if self._emb_fn is None:
            self._emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="BAAI/bge-m3")

        try:
            self._client = chromadb.PersistentClient(path=CHROMA_DATA_PATH)
            self._collection = self._client.get_or_create_collection(
                name="industry_research_db", embedding_function=self._emb_fn
            )
            return self._collection
        except BaseException as e:
            # 兼容 pyo3_runtime.PanicException（可能不继承 Exception）
            print(f"⚠️ Chroma 初始化失败，尝试隔离损坏库并重建: {e}")
            rotated = self._rotate_corrupted_store(CHROMA_DATA_PATH)
            print(f"🧹 已隔离旧库目录: {rotated}")

            self._client = chromadb.PersistentClient(path=CHROMA_DATA_PATH)
            self._collection = self._client.get_or_create_collection(
                name="industry_research_db", embedding_function=self._emb_fn
            )
            return self._collection

    def ingest_pdf(self, file_path: str):
        print(f"📥 正在深度解析文件 (含表格): {file_path} ...")
        full_text = ""

        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                tables = page.extract_tables()
                table_text = ""
                for table in tables:
                    cleaned_table = [[str(cell) if cell else "" for cell in row] for row in table]
                    table_text += f"\n[表格数据]: {str(cleaned_table)}\n"
                full_text += text + "\n" + table_text

        chunks = self.text_splitter.split_text(full_text)
        filename = os.path.basename(file_path)

        docs, ids, metadatas = [], [], []
        ingest_time = datetime.datetime.now(datetime.timezone.utc).isoformat()

        for i, chunk in enumerate(chunks):
            retrieval_text = self._build_retrieval_text(chunk)
            ids.append(f"{filename}_{i}")
            docs.append(retrieval_text)
            metadatas.append(
                {
                    "source": filename,
                    "type": "report",
                    "chunk_index": i,
                    "ingest_time": ingest_time,
                    "raw_content": chunk,
                    "keywords": " ".join(self._extract_keywords(chunk)[:25]),
                }
            )

        collection = self._ensure_collection()
        collection.add(documents=docs, ids=ids, metadatas=metadatas)
        print(f"✅ 已存入 {len(chunks)} 个知识片段（多表示索引）")

    def _rerank(self, docs: List[str], metas: List[dict], distances: List[float], query: str) -> List[Tuple[str, dict, float]]:
        ranked = []
        for doc, meta, dist in zip(docs, metas, distances):
            raw = (meta or {}).get("raw_content", doc)
            vector_score = 1 / (1 + max(dist or 0, 0))
            keyword_score = self._keyword_score(raw, query)
            final_score = 0.65 * vector_score + 0.35 * keyword_score
            ranked.append((raw, meta, final_score))
        ranked.sort(key=lambda x: x[2], reverse=True)
        return ranked

    def query_knowledge(self, query, n_results=5, keyword_filter=None):
        collection = self._ensure_collection()
        results = collection.query(query_texts=[query], n_results=n_results * 3)

        docs = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        reranked = self._rerank(docs, metadatas, distances, query)
        final_results = []
        for doc, meta, score in reranked:
            if keyword_filter and keyword_filter not in doc:
                continue
            source = (meta or {}).get("source", "unknown")
            final_results.append(f"[来源: {source}][score={score:.3f}]\n{doc}")

        return "\n\n".join(final_results[:n_results])

    def query_with_reasoning(self, query: str, n_results: int = 5, max_rounds: int = 2) -> str:
        """RAR: 检索 -> 评估 -> 再检索。"""
        history = []
        current_query = query

        for _ in range(max_rounds):
        for round_idx in range(max_rounds):
            evidence = self.query_knowledge(current_query, n_results=n_results)
            history.append((current_query, evidence))

            if evidence and len(evidence) > 400:
                break

            constraints = re.findall(r"\d{4}|市场规模|营收|利润|政策|上游|中游|下游", query)
            if constraints:
                current_query = f"{query} {' '.join(constraints)}"
            else:
                current_query = f"{query} 行业数据 龙头企业 政策"


            constraints = re.findall(r"\d{4}|市场规模|营收|利润|政策|上游|中游|下游", query)
            if constraints:
                current_query = f"{query} {' '.join(constraints)}"
            else:
                current_query = f"{query} 行业数据 龙头企业 政策"

        sections = []
        for i, (q, ev) in enumerate(history, start=1):
            sections.append(f"[RAR Round {i}] 查询: {q}\n{ev or '无有效证据'}")
        return "\n\n".join(sections)

    def recommend_sync_strategy(self) -> Dict[str, str]:
        """
        最佳方案：上传时增量更新 + 每晚定时校验
        - 上传触发：保证时效性（用户立刻可检索）
        - 夜间任务：做去重、重分块、索引健康检查
        """
        return {
            "recommended": "hybrid",
            "upload_time": "每次上传文件后，立即进行增量切分与索引更新",
            "nightly": "每日凌晨02:00执行增量重建（去重、失效清理、embedding回填）",
            "reason": "投研场景需要实时可查 + 离峰期做质量修复，兼顾时效与性能成本",
        }


kb_manager = KnowledgeBaseManager()
