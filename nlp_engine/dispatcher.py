import multiprocessing
import concurrent.futures
import os
from typing import Dict, Any

# 显式声明为 Any 类型，防止 PyCharm 因为初始值是 None 而报错找不到方法
_worker_engine_instance: Any = None


def _initializer_worker():
    # 每个子进程启动时，也要锁死离线模式
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    global _worker_engine_instance
    from nlp_engine.core_algorithms import PolicyNLPEngine
    _worker_engine_instance = PolicyNLPEngine()


def _worker_analyze_task(report_text: str, history_texts: list[str]) -> Dict[str, Any]:
    global _worker_engine_instance
    curr_sentences = [s.strip() for s in report_text.split('。') if len(s.strip()) > 5]

    # 获取历史全文
    hist_full_text = "".join(history_texts)
    hist_sentences = [s.strip() for s in hist_full_text.split('。') if len(s.strip()) > 5]

    # 执行核心算法
    wording_changes = _worker_engine_instance.analyze_wording_changes(curr_sentences, hist_sentences)
    new_terms = _worker_engine_instance.extract_new_terms(report_text)
    priority = _worker_engine_instance.calculate_priority(curr_sentences[:15])

    # 执行真正的动态删减检测
    missing_content = _worker_engine_instance.detect_dynamic_missing(hist_full_text, report_text)

    return {
        "wording_changes": wording_changes,
        "new_terms": new_terms,
        "priority_outline": priority,
        "missing_content": missing_content
    }


class ParallelAnalyzer:
    def __init__(self, max_workers: int = None):
        self.max_workers = max_workers or max(1, multiprocessing.cpu_count() - 1)
        self.pool = concurrent.futures.ProcessPoolExecutor(
            max_workers=self.max_workers,
            initializer=_initializer_worker
        )

    async def run_analysis_async(self, report_text: str, history_texts: list[str]) -> Dict[str, Any]:
        import asyncio
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(self.pool, _worker_analyze_task, report_text, history_texts)
        return result
