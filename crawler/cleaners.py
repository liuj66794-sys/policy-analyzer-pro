import re
import io
import pdfplumber
from docx import Document

class PolicyTextCleaner:
    @staticmethod
    def clean_html_noise(text: str) -> str:
        # 保持原有逻辑
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    @staticmethod
    def extract_from_pdf(content: bytes) -> str:
        """从 PDF 字节流提取文本"""
        text = ""
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            for page in pdf.pages:
                text += (page.extract_text() or "") + "\n"
        return text

    @staticmethod
    def extract_from_docx(content: bytes) -> str:
        """从 Word 字节流提取文本"""
        doc = Document(io.BytesIO(content))
        return "\n".join([para.text for para in doc.paragraphs])

    @staticmethod
    def chunk_by_paragraph(text: str):
        paragraphs = [p.strip() for p in text.split('\n') if len(p.strip()) > 20]
        for p in paragraphs:
            yield p
