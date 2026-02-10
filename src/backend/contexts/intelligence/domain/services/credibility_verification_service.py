"""概念可信度验证服务接口

定义 ICredibilityVerificationService 抽象接口，用于执行概念可信度验证工作流。
领域层定义接口，基础设施层（LangGraph 工作流）提供具体实现。
"""

from abc import ABC, abstractmethod

from shared_kernel.value_objects.stock_code import StockCode
from ..value_objects.credibility_report import CredibilityReport


class ICredibilityVerificationService(ABC):
    """概念可信度验证服务接口

    定义概念可信度验证工作流的执行契约。基础设施层通过 LangGraph
    工作流实现此接口，从主营业务匹配度、实质证据、历史蹭热点记录
    和供应链逻辑四个维度分析股票与概念的可信度。
    """

    @abstractmethod
    async def verify_credibility(
        self, stock_code: StockCode, concept: str, progress_callback=None
    ) -> CredibilityReport:
        """执行概念可信度验证

        Args:
            stock_code: 股票代码值对象
            concept: 被验证的概念（如"固态电池"）
            progress_callback: 进度回调函数
                签名: (progress: int, agent_step: AgentStep) -> None

        Returns:
            CredibilityReport 值对象，包含可信度验证的完整分析结果
        """
        pass
