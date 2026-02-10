"""接口层控制器模块

导出 Flask Blueprint 和初始化函数。
"""

from .intelligence_controller import (
    intelligence_bp,
    init_app,
    get_task_service,
)

__all__ = [
    'intelligence_bp',
    'init_app',
    'get_task_service',
]
