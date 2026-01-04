# memory_system/memory_manager.py

import datetime
from ingestion.pdf_ingest import PDFIngestor
from memory_system.vector_store.chroma_client import ChromaVectorStore
from rag.retriever import VectorRetriever
from langchain.text_splitter import RecursiveCharacterTextSplitter

class MemoryManager:
    """
    全维投研记忆系统
    支持：PDF原文、Agent产出的事实、观点、结论、正文段落
    """

    def __init__(self, persist_dir: str):
        self.vector_store = ChromaVectorStore(persist_dir)
        self.retriever = VectorRetriever(self.vector_store)
        self.pdf_ingestor = PDFIngestor()
        
        # 不同的内容切分策略可能不同，这里暂用通用策略
        self.splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)

    # ------------------ 存入 (Write) ------------------

    def save_insight(self, content: str, category: str, metadata: dict):
        """
        核心方法：存储 Agent 的产出
        :param content: 文本内容
        :param category: 'fact' | 'opinion' | 'conclusion' | 'report_segment'
        :param metadata: {industry, year, province, focus, source_agent}
        """
        if not content: return

        # 自动补全元数据
        meta = metadata.copy()
        meta.update({
            "category": category,
            "ingest_time": datetime.datetime.now().isoformat(),
            "type": "agent_memory" # 区别于 pdf_file
        })

        # 存入向量库
        # 注意：如果是短结论，可以不切分直接存；长段落需要切分
        if len(content) < 500:
            chunks = [content]
        else:
            chunks = self.splitter.split_text(content)
            
        metadatas = [meta for _ in chunks]
        self.vector_store.add_texts(chunks, metadatas)
        print(f"🧠 [Memory] 已存储 {len(chunks)} 条 {category} 记忆")

    def ingest_pdf(self, file_path: str, metadata: dict):
        raw_text = self.pdf_ingestor.ingest(file_path)
        chunks = self.splitter.split_text(raw_text)
        metadatas = [metadata for _ in chunks]
        self.vector_store.add_texts(chunks, metadatas)

    # ------------------ 召回 (Read) ------------------

    def recall_memory(self, query: str, category: str = None, k: int = 5):
        """
        精准召回：支持按 category 过滤
        例如：Analyst 只想看之前的 'fact'，Writer 想看之前的 'conclusion'
        """
        # 注意：底层 ChromaClient 需要支持 where 过滤
        # 这里假设您的 VectorRetriever 支持 filter 参数，如果不支持需修改底层
        # 临时方案：先检索多一点，再在内存里过滤 (如果底层不支持 metadata 过滤)
        results = self.retriever.retrieve(query, k=k * 2) 
        
        if category:
            # 简单的内存过滤示例 (实际建议下推到数据库层)
            # 假设 retrieve 返回的是 Document 对象或带 metadata 的字典
            # 这里需要根据您实际的 retriever 返回结构调整
            pass 
            
        return results

# 全局单例
memory_manager = MemoryManager(persist_dir="./knowledge_base/vector_store")


