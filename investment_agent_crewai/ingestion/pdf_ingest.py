# ingestion/pdf_ingest.py
# PDF → 原始文本 + 表格文本
import pdfplumber

class PDFIngestor:
    # 原 knowledge_engine.py 中的 PDF 解析逻辑
    def ingest(self, file_path: str) -> str:
        full_text = ""

        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"

                # 原有表格提取逻辑
                tables = page.extract_tables()
                for table in tables:
                    for row in table:
                        full_text += " | ".join(row) + "\n"

        return full_text


