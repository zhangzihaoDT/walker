# -*- coding: utf-8 -*-
"""
Agents模块 - 包含意图解析器和总结代理
"""

from .intent_parser import IntentParser
from .summary_agent import SummaryAgent

# 全局实例
_intent_parser = None
_summary_agent = None

def get_intent_parser(mock_client=None) -> IntentParser:
    """
    获取全局意图解析器实例
    
    Args:
        mock_client: 可选的模拟客户端，用于测试
    
    Returns:
        IntentParser实例
    """
    global _intent_parser
    if _intent_parser is None:
        _intent_parser = IntentParser(mock_client)
    return _intent_parser

def get_summary_agent(mock_client=None) -> SummaryAgent:
    """
    获取全局总结代理实例
    
    Args:
        mock_client: 可选的模拟客户端，用于测试
    
    Returns:
        SummaryAgent实例
    """
    global _summary_agent
    if _summary_agent is None:
        _summary_agent = SummaryAgent(mock_client)
    return _summary_agent

__all__ = [
    'IntentParser',
    'SummaryAgent', 
    'get_intent_parser',
    'get_summary_agent'
]