"""领域层枚举定义

定义智能分析上下文中使用的所有枚举类型，包括任务类型、任务状态、
Agent 步骤状态和风险标签。
"""

from enum import Enum


class TaskType(Enum):
    """调研任务类型"""
    INDUSTRY_RESEARCH = "industry_research"                # 快速行业认知
    CREDIBILITY_VERIFICATION = "credibility_verification"  # 概念可信度验证


class TaskStatus(Enum):
    """调研任务状态"""
    PENDING = "pending"      # 等待中
    RUNNING = "running"      # 执行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"        # 失败
    CANCELLED = "cancelled"  # 已取消


class AgentStepStatus(Enum):
    """LangGraph 工作流中单个 Agent 步骤的执行状态"""
    PENDING = "pending"      # 等待中
    RUNNING = "running"      # 执行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"        # 失败
    SKIPPED = "skipped"      # 跳过


class RiskLabel(Enum):
    """可信度验证风险标签"""
    PURE_HYPE = "pure_hype"                              # 纯蹭热点
    WEAK_EVIDENCE = "weak_evidence"                      # 证据不足
    BUSINESS_MISMATCH = "business_mismatch"              # 主业不匹配
    HIGH_DEBT = "high_debt"                              # 高负债风险
    FREQUENT_CONCEPT_CHANGE = "frequent_concept_change"  # 频繁概念切换
    SUPPLY_CHAIN_RISK = "supply_chain_risk"              # 供应链风险
