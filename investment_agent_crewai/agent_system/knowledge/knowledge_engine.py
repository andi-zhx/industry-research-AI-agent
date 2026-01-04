# 新建一个文件专门管理知识库。这个模块负责把文本变成向量存起来，以及把向量查出来
# knowledge_engine.py
import os
import chromadb
from chromadb.utils import embedding_functions
from langchain.text_splitter import RecursiveCharacterTextSplitter
from pypdf import PdfReader
import pdfplumber

# ===============================
# 1. 计算项目根目录
# knowledge_engine.py 所在路径：investment_agent_crewai/agent_system/knowledge/knowledge_engine.py
# ===============================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

PROJECT_ROOT = os.path.abspath(
    os.path.join(CURRENT_DIR, "../../")
)

# ===============================
# 2. ChromaDB 持久化目录
# ===============================
CHROMA_DATA_PATH = os.path.join(PROJECT_ROOT, "chroma_db")
os.makedirs(CHROMA_DATA_PATH, exist_ok=True)

# ===============================
# 3. 初始化 Chroma Client
# ===============================
client = chromadb.PersistentClient(path=CHROMA_DATA_PATH)

# 2. 设置向量模型 (使用开源免费的 huggingface 模型，支持中文)
# 第一次运行会自动下载模型，约 500MB
emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="BAAI/bge-m3" # 这是一个非常强大的支持中英文的 Embedding 模型
)

# 3. 获取或创建集合 (Collection)
collection = client.get_or_create_collection(
    name="industry_research_db",
    embedding_function=emb_fn
)

class KnowledgeBaseManager:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,  # 每个切片500字
            chunk_overlap=50 # 切片之间重叠50字，防止语义断裂
        )
        
    # --- 核心功能：让 Agent 变聪明的“吃书”过程 ---
    # 废弃通用的 read_pdf 用于“寻找数据”。将 read_pdf 改造成 get_table_of_contents (读取目录) 工具。
    # Agent 先看目录，知道哪一章讲财务，然后再用 RAG 去搜那一章的细节。
    def ingest_pdf(self, file_path):
        """读取PDF -> 切片 -> 向量化 -> 存入DB"""
        print(f"📥 正在深度解析文件 (含表格): {file_path} ...")
        full_text = ""
        
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                # 1. 提取纯文本
                text = page.extract_text() or ""
                
                # 2. 提取表格 (这是 pypdf 做不到的)
                tables = page.extract_tables()
                table_text = ""
                for table in tables:
                    # 将表格转换为 Markdown 格式，方便 LLM 理解
                    # 简单处理：过滤 None，转字符串
                    cleaned_table = [[str(cell) if cell else "" for cell in row] for row in table]
                    # 这里可以写一个函数把 list 转 markdown table string
                    table_text += f"\n[表格数据]: {str(cleaned_table)}\n"
                
                full_text += text + "\n" + table_text
        
        # 2. 文本切片
        chunks = self.text_splitter.split_text(full_text)
        
        # 3. 构造元数据 (Metadata)，方便后续过滤
        filename = os.path.basename(file_path)
        ids = [f"{filename}_{i}" for i in range(len(chunks))]
        metadatas = [{"source": filename, "type": "report"} for _ in range(len(chunks))]
        
        # 4. 存入 ChromaDB (会自动调用 embedding 模型转向量)
        collection.add(
            documents=chunks,
            ids=ids,
            metadatas=metadatas
        )
        print(f"✅ 已存入 {len(chunks)} 个知识片段。")

    # --- 核心功能：让 Agent 变聪明的“回忆”过程 ---
   # 你使用了 BAAI/bge-m3 进行向量检索。向量检索是基于“语义相似度”的。 问题：
   # 当你问“2024年营收是多少”时，向量检索可能会找回来“2023年营收”或者“2024年利润”，因为它们在语义上很像。
   # 金融分析需要精确匹配。投资人不能接受“大概是这个数”。
   # 代码体现：knowledge_engine.py 中只有 collection.query（纯向量搜索）。
   # 改进方案：混合检索 (Hybrid Search) 同时进行关键词检索（BM25）和向量检索，并进行重排序（Rerank）。
   # `哪怕不做那么复杂，至少要在 Tool 里增加关键词过滤。
    def query_knowledge(self, query, n_results=5, keyword_filter=None):
        """
        根据问题，在数据库中寻找最相关的证据
        keyword_filter: 强制要求结果中包含特定词（如年份、指标名）
        增加关键词过滤能力
        """
        results = collection.query(
            query_texts=[query],
            n_results=n_results * 2 # 多取一点用来过滤
        )
        
        docs = results['documents'][0]
        metadatas = results['metadatas'][0]
        
        final_results = []
        for doc, meta in zip(docs, metadatas):
            # 简单的硬过滤：如果指定了关键词，必须包含
            if keyword_filter and keyword_filter not in doc:
                continue
            
            # 拼凑引用来源，解决信任问题（痛点二）
            source_info = f"[来源: {meta['source']}]" 
            final_results.append(f"{source_info}\n{doc}")
            
        return "\n\n".join(final_results[:n_results])

# 实例化
kb_manager = KnowledgeBaseManager()

