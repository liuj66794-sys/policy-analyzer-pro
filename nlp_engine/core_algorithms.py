import math
import numpy as np
import jieba
import jieba.analyse
from functools import lru_cache
from typing import List, Dict, Tuple, Set
from sentence_transformers import SentenceTransformer, util


# 假定此处已加载自定义的《中国政策与政务专属词库》
# jieba.load_userdict("data/gov_dict.txt")

class PolicyNLPEngine:
    """
    政策文本核心 NLP 引擎
    注意：此类将在子进程中被实例化，避免主进程传递巨量模型数据导致 IPC（进程间通信）序列化开销过大。
    """

    def __init__(self, model_name: str = "hfl/chinese-roberta-wwm-ext"):
        # 延迟加载（Lazy Loading）：仅在实际进行分析的子进程中载入约 400MB 的 Transformer 模型
        self.encoder = SentenceTransformer(model_name)

    @staticmethod
    @lru_cache(maxsize=1)
    def _load_historical_baseline_vocab() -> Set[str]:
        """
        【CPython 内存与性能优化点：LRU Cache】
        加载历届政府报告的基线词汇表。使用 @lru_cache 确保这个可能包含数十万词的
        Set 只会在内存中被实例化一次。后续 O(1) 复杂度的哈希查找将极快。
        """
        # 模拟从本地文件或 SQLite 加载历年高频词
        return {"高质量发展", "新质生产力", "宏观调控", "乡村振兴"}  # 示例基线集

    def analyze_wording_changes(self, current_sentences: List[str], history_sentences: List[str]) -> List[Dict]:
        """
        原则一：措辞变化分析 (语义相似度比对)
        底层原理：将文本映射为高维稠密向量，计算余弦相似度。
        """
        # 【GIL 释放点】：PyTorch/Transformers 底层调用 C++ (如 ATen/MKL) 进行矩阵乘法时，
        # 会主动释放 Python GIL，此时多线程可并行。但为统一架构，我们仍在多进程中调用。
        curr_embeddings = self.encoder.encode(current_sentences, convert_to_tensor=True)
        hist_embeddings = self.encoder.encode(history_sentences, convert_to_tensor=True)

        # 计算余弦相似度矩阵
        cosine_scores = util.cos_sim(curr_embeddings, hist_embeddings)

        changes = []
        for i, curr_sentence in enumerate(current_sentences):
            # 找到历史中最相似的句子
            best_match_idx = int(np.argmax(cosine_scores[i].cpu().numpy()))
            score = float(cosine_scores[i][best_match_idx])

            # 若相似度在 0.6 到 0.9 之间，说明是“旧话新说”，存在表述微调
            if 0.6 < score < 0.9:
                changes.append({
                    "current": curr_sentence,
                    "historical_match": history_sentences[best_match_idx],
                    "change_intensity": 1.0 - score  # 差值即为变化强度
                })
        return changes

    def extract_new_terms(self, text: str) -> List[str]:
        """
        原则三：新提法识别 (TF-IDF 与基线碰撞)
        """
        # 使用 jieba 提取当前文本的 TF-IDF 核心词
        current_keywords = set(jieba.analyse.extract_tags(text, topK=50, withWeight=False))
        baseline_vocab = self._load_historical_baseline_vocab()

        # 集合的差集运算（底层为 C 实现，速度极快），找出不在历届基线中的新词
        new_terms = list(current_keywords - baseline_vocab)
        return new_terms

    def check_missing_content(self, current_topics: Set[str], historical_topics: Set[str]) -> List[str]:
        """
        原则四：缺失内容分析
        对比往年报告的主干框架（主题提取），找出本次跌出视野的重点。
        """
        missing = historical_topics - current_topics
        return list(missing)

    def calculate_priority(self, paragraphs: List[str]) -> List[Dict]:
        """
        原则二：排序优先级分析
        根据段落出现的绝对位置赋予权重。权重随位置呈对数衰减。
        """
        prioritized = []
        total_len = len(paragraphs)
        for i, para in enumerate(paragraphs):
            # 越靠前的段落权重越高，使用平滑的对数衰减公式
            weight = 1.0 / math.log2(i + 2)
            prioritized.append({"content": para[:50] + "...", "weight": round(weight, 3)})

        # 按权重降序排列
        return sorted(prioritized, key=lambda x: x["weight"], reverse=True)