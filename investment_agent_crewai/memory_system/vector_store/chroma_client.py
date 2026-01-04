# memory_system/vector_store/chroma_client.py
# 封装 Chroma + embedding，不让 Agent 知道底层细节
from langchain_chroma import Chroma
from langchain.embeddings import HuggingFaceEmbeddings

class ChromaVectorStore:
    """
    【原 knowledge_engine.py 中的 Chroma 初始化 + 入库逻辑】
    """

    def __init__(self, persist_dir: str):
        self.embeddings = HuggingFaceEmbeddings(
            model_name="BAAI/bge-m3"
        )

        self.db = Chroma(
            persist_directory=persist_dir,
            embedding_function=self.embeddings
        )

    def add_texts(self, texts, metadatas):
        self.db.add_texts(
            texts=texts,
            metadatas=metadatas
        )
        # self.db.persist()  # 新版会自动保存，调用它会报错，所以这里注销调

    def similarity_search_with_score(self, query, k=5):
        return self.db.similarity_search_with_score(
            query=query,
            k=k
        )
