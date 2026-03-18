class PolicyAnalyzerError(Exception):
    """项目的全局基础异常类"""
    pass

class ComplianceError(PolicyAnalyzerError):
    """
    合规与安全异常
    当触发 robots.txt 限制或尝试访问涉密/未公开链接时抛出
    """
    pass