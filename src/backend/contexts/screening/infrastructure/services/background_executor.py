"""后台任务执行器

使用单例模式和 ThreadPoolExecutor 在后台线程中执行策略筛选任务。

Requirements: 3.1, 3.6
"""
import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Callable

logger = logging.getLogger(__name__)


class BackgroundExecutor:
    """后台任务执行器（单例）"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, max_workers: int = 3):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._executor = ThreadPoolExecutor(
                        max_workers=max_workers,
                        thread_name_prefix="screening_executor",
                    )
                    cls._instance._tasks = {}
        return cls._instance

    def submit(self, task_id: str, fn: Callable, *args, **kwargs) -> None:
        """提交任务到线程池"""
        future = self._executor.submit(fn, *args, **kwargs)
        self._tasks[task_id] = future

        def cleanup(f):
            self._tasks.pop(task_id, None)

        future.add_done_callback(cleanup)

    def cancel(self, task_id: str) -> bool:
        """尝试取消任务"""
        future = self._tasks.get(task_id)
        if future:
            return future.cancel()
        return False

    def shutdown(self, wait: bool = True) -> None:
        """关闭执行器"""
        self._executor.shutdown(wait=wait)

    @classmethod
    def reset(cls):
        """重置单例（仅用于测试）"""
        with cls._lock:
            if cls._instance is not None:
                cls._instance._executor.shutdown(wait=False)
                cls._instance = None
