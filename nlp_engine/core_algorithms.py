import os
# 【核心修正】：在导入任何 AI 库之前，强制锁定离线模式，从根源断绝 403 报错
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import math
import numpy as np
import jieba
import jieba.analyse
from typing import List, Dict  # 删除了无用的 Tuple, Set, lru_cache
from sentence_transformers import SentenceTransformer, util

class PolicyNLPEngine:
    def __init__(self, model_name: str = "hfl/chinese-roberta-wwm-ext"):
        # 增加 local_files_only=True，双重保险禁止联网
        self.encoder = SentenceTransformer(model_name, model_kwargs={"local_files_only": True})

    def analyze_wording_changes(self, current_sentences: List[str], history_sentences: List[str]) -> List[Dict]:
        if not current_sentences or not history_sentences:
            return []
        curr_embeddings = self.encoder.encode(current_sentences, convert_to_tensor=True)
        hist_embeddings = self.encoder.encode(history_sentences, convert_to_tensor=True)
        cosine_scores = util.cos_sim(curr_embeddings, hist_embeddings)

        changes = []
        for i, curr_sentence in enumerate(current_sentences):
            best_match_idx = int(np.argmax(cosine_scores[i].cpu().numpy()))
            score = float(cosine_scores[i][best_match_idx])
            if 0.6 < score < 0.9:
                changes.append({
                    "current": curr_sentence,
                    "historical_match": history_sentences[best_match_idx],
                    "change_intensity": round(1.0 - score, 3)
                })
        return changes

    @staticmethod  # 增加静态方法装饰器
    def extract_new_terms(text: str) -> List[str]:
        current_keywords = set(jieba.analyse.extract_tags(text, topK=30, withWeight=False))
        # 模拟基线（正式环境建议从文件读取）
        baseline_vocab = {"高质量发展", "宏观调控", "乡村振兴", "坚持", "推进", "建设"}
        new_terms = list(current_keywords - baseline_vocab)
        return new_terms

    @staticmethod  # 增加静态方法装饰器
    def detect_dynamic_missing(old_text: str, new_text: str) -> List[str]:
        """
        【硬核算法实现】：真正的动态删减与弱化监测
        """
        warnings = []
        # 使用 TextRank 提取旧文档的 Top 15 核心议题
        old_keywords = jieba.analyse.textrank(old_text, topK=15)
        for word in old_keywords:
            old_count = old_text.count(word)
            new_count = new_text.count(word)
            if old_count >= 2:
                if new_count == 0:
                    warnings.append(f"【彻底删减】往年核心词“{word}”在本次报告中完全消失。")
                elif new_count <= old_count * 0.3:
                    warnings.append(f"【明显弱化】往年重点“{word}”出现频次从 {old_count} 降至 {new_count}。")
        return warnings if warnings else ["政策延续性良好，未检测到显著删减。"]

    @staticmethod  # 增加静态方法装饰器
    def calculate_priority(paragraphs: List[str]) -> List[Dict]:
        prioritized = []
        for i, para in enumerate(paragraphs):
            weight = 1.0 / math.log2(i + 2)
            prioritized.append({"content": para[:60] + "...", "weight": round(weight, 3)})
        return sorted(prioritized, key=lambda x: x["weight"], reverse=True)
