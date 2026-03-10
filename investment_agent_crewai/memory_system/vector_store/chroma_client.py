# memory_system/vector_store/chroma_client.py
# 封装 Chroma + embedding，不让 Agent 知道底层细节
import os
import shutil
import datetime

from langchain_chroma import Chroma
from langchain.embeddings import HuggingFaceEmbeddings


class ChromaVectorStore:
    """带容错初始化的 Chroma 向量库封装。"""

    def __init__(self, persist_dir: str):
        self.persist_dir = persist_dir
        os.makedirs(self.persist_dir, exist_ok=True)

        self.embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-m3")
        self.db = self._init_db_with_recovery()

    def _rotate_corrupted_store(self) -> str:
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        broken_path = f"{self.persist_dir}_corrupted_{ts}"
        if os.path.exists(self.persist_dir):
            shutil.move(self.persist_dir, broken_path)
        os.makedirs(self.persist_dir, exist_ok=True)
        return broken_path

    def _init_db_with_recovery(self):
        try:
            return Chroma(persist_directory=self.persist_dir, embedding_function=self.embeddings)
        except BaseException as e:
            print(f"⚠️ Memory Chroma 初始化失败，尝试重建本地库: {e}")
            rotated = self._rotate_corrupted_store()
            print(f"🧹 已隔离损坏的向量库目录: {rotated}")
            return Chroma(persist_directory=self.persist_dir, embedding_function=self.embeddings)

    def add_texts(self, texts, metadatas):
        self.db.add_texts(texts=texts, metadatas=metadatas)

    def similarity_search_with_score(self, query, k=5, where=None):
        return self.db.similarity_search_with_score(query=query, k=k, filter=where)
