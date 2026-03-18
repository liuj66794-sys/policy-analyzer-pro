import re
from typing import Generator


class PolicyTextCleaner:
    """
    政策文本清洗与预处理核心类
    """

    @staticmethod
    def clean_html_noise(raw_text: str) -> str:
        """基础去噪：去除不可见字符、多余空白及残留的 HTML 标签"""
        text = re.sub(r'<[^>]+>', '', raw_text)  # 剥离 HTML 标签
        text = re.sub(r'\s+', ' ', text)  # 合并连续空白字符
        return text.strip()

    @staticmethod
    def chunk_by_paragraph(cleaned_text: str) -> Generator[str, None, None]:
        """
        【CPython 内存优化点】:
        使用 yield 构造生成器按段落切分长文本。
        按需生成（Lazy Evaluation）可以保证在后续送入 NLP 模型分析时，
        一次只在内存中持有一段文本的对象，处理完毕后其引用计数归零，
        使得 CPython 的垃圾回收器（GC）能立即回收内存，防止 OOM（内存溢出）。
        """
        # 政策报告通常以换行符或特定空格缩进作为段落标志
        paragraphs = re.split(r'\n+', cleaned_text)
        for para in paragraphs:
            para = para.strip()
            if len(para) > 10:  # 过滤掉过短的无意义噪音（如单独的页码）
                yield para