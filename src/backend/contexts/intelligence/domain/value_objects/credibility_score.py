"""可信度评分值对象模块

包含 CredibilityScore 值对象，用于表示 0-100 的可信度评分及其等级。
"""


class CredibilityScore:
    """可信度评分（0-100）

    不可变值对象，封装可信度评分的验证逻辑和等级划分。
    评分范围为 0-100 的整数，根据分值自动划分为高/中/低可信度等级：
    - 80-100: 高可信度
    - 50-79: 中可信度
    - 0-49: 低可信度
    """

    def __init__(self, score: int):
        """初始化 CredibilityScore

        Args:
            score: 0-100 的整数评分

        Raises:
            ValueError: 如果 score 不是整数或不在 0-100 范围内
        """
        if not isinstance(score, int) or score < 0 or score > 100:
            raise ValueError(f"可信度评分必须是 0-100 的整数，收到: {score}")
        self._score = score

    @property
    def score(self) -> int:
        """获取评分值"""
        return self._score

    @property
    def level(self) -> str:
        """返回可信度等级

        Returns:
            "高可信度"（80-100）、"中可信度"（50-79）或 "低可信度"（0-49）
        """
        if self._score >= 80:
            return "高可信度"
        elif self._score >= 50:
            return "中可信度"
        else:
            return "低可信度"

    def to_dict(self) -> dict:
        """序列化为字典

        Returns:
            包含 score 和 level 的字典
        """
        return {"score": self._score, "level": self.level}

    @classmethod
    def from_dict(cls, data: dict) -> "CredibilityScore":
        """从字典反序列化创建 CredibilityScore

        Args:
            data: 包含 "score" 键的字典

        Returns:
            CredibilityScore 实例

        Raises:
            ValueError: 如果 score 值无效
            KeyError: 如果字典缺少 "score" 键
        """
        return cls(score=data["score"])

    def __eq__(self, other):
        """判断两个 CredibilityScore 是否相等"""
        return isinstance(other, CredibilityScore) and self._score == other._score

    def __hash__(self):
        """返回哈希值，支持在集合和字典中使用"""
        return hash(self._score)

    def __repr__(self):
        """返回字符串表示"""
        return f"CredibilityScore(score={self._score}, level='{self.level}')"
