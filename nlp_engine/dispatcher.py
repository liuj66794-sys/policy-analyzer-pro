import multiprocessing
import concurrent.futures
from typing import Dict, Any

# 延迟导入，防止在主进程预先加载消耗内存
# from nlp_engine.core_algorithms import PolicyNLPEngine

# 【进程隔离区】：此类全局变量仅存在于各个独立的子进程内存空间中
_worker_engine_instance = None


def _initializer_worker():
    """
    【CPython 内存池与 IPC 优化】
    子进程初始化函数。
    如果在主进程实例化 PolicyNLPEngine（包含数百MB的模型权重），
    再通过多进程传递给子进程，不仅会因为 Pickle 序列化失败报错，
    还会造成灾难性的内存复制和极高的 IPC（进程间通信）延迟。

    正确的做法：主进程只下发轻量级的纯文本（String），
    大模型在各个子进程启动时独立初始化一次，驻留在子进程内存中。
    """
    global _worker_engine_instance
    from nlp_engine.core_algorithms import PolicyNLPEngine
    _worker_engine_instance = PolicyNLPEngine()


def _worker_analyze_task(report_text: str, history_texts: list[str]) -> Dict[str, Any]:
    """
    子进程实际执行的任务函数。由 ProcessPoolExecutor 调度。
    """
    global _worker_engine_instance

    # 简单的按句切分预处理 (实际应用中可引入基于正则的复杂分句)
    curr_sentences = [s.strip() for s in report_text.split('。') if len(s.strip()) > 5]
    hist_sentences = [s.strip() for s in "".join(history_texts).split('。') if len(s.strip()) > 5]

    # 依次调用五大分析原则
    wording_changes = _worker_engine_instance.analyze_wording_changes(curr_sentences, hist_sentences)
    new_terms = _worker_engine_instance.extract_new_terms(report_text)
    priority = _worker_engine_instance.calculate_priority(curr_sentences[:20])  # 取前20句做优先级演示

    return {
        "wording_changes": wording_changes,
        "new_terms": new_terms,
        "priority_outline": priority
    }


class ParallelAnalyzer:
    """多进程调度外观类 (Facade)"""

    def __init__(self, max_workers: int = None):
        # 默认使用系统物理核心数减 1，留一个核心给 FastAPI 处理网络 I/O 及其它系统常驻任务
        self.max_workers = max_workers or max(1, multiprocessing.cpu_count() - 1)

        self.pool = concurrent.futures.ProcessPoolExecutor(
            max_workers=self.max_workers,
            initializer=_initializer_worker
        )

    async def run_analysis_async(self, report_text: str, history_texts: list[str]) -> Dict[str, Any]:
        """
        【FastAPI 事件循环桥接】
        使用 asyncio.get_running_loop().run_in_executor 将阻塞的 CPU 密集型任务
        抛入多进程池中执行，并以 await 等待。
        这样既绕过了 GIL 实现了多核并行，又保证了 FastAPI 异步网络层 100% 的非阻塞。
        """
        import asyncio
        loop = asyncio.get_running_loop()

        # 将参数打包投递给子进程
        result = await loop.run_in_executor(
            self.pool,
            _worker_analyze_task,
            report_text,
            history_texts
        )
        return result