"""快速行业认知服务接口

定义 IIndustryResearchService 抽象接口，用于执行快速行业认知工作流。
领域层定义接口，基础设施层（LangGraph 工作流）提供具体实现。
"""

from abc import ABC, abstractmethod

from ..value_objects.industry_insight import IndustryInsight


class IIndustryResearchService(ABC):
    """快速行业认知服务接口

    定义快速行业认知工作流的执行契约。基础设施层通过 LangGraph
    5-Agent 协作工作流实现此接口，完成行业背景速览、市场热度分析、
    标的快速筛选、真实性批量验证和竞争格局速览。
    """

    @abstractmethod
    async def execute_research(
        self, query: str, progress_callback=None
    ) -> IndustryInsight:
        """执行快速行业认知工作流

        Args:
            query: 用户查询（如"快速了解合成生物学赛道"）
            progress_callback: 进度回调函数
                签名: (progress: int, agent_step: AgentStep) -> None

        Returns:
            IndustryInsight 值对象，包含行业认知的完整分析结果
        """
        pass
