#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Intent Parser - 意图识别模块

负责识别用户输入的意图，包括数据查询、数据分析、一般对话等类型。
支持新的query_only意图类型，用于直接SQL查询。
"""

import logging
from typing import Dict, Any
from pathlib import Path
import sys

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from llm.glm import get_glm_client
from llm.prompts import INTENT_RECOGNITION_PROMPT

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IntentParser:
    """
    意图识别解析器类
    
    负责解析用户输入的意图，支持以下意图类型：
    - query_only: 直接SQL查询类
    - data_analysis: 数据分析类
    - general_chat: 一般对话类
    """
    
    def __init__(self):
        """初始化意图解析器"""
        self.glm_client = get_glm_client()
        logger.info("意图解析器初始化成功")
    
    def parse_intent(self, user_question: str) -> Dict[str, Any]:
        """
        解析用户问题的意图
        
        Args:
            user_question: 用户输入的问题
            
        Returns:
            包含意图信息的字典，格式如下：
            {
                "intent": "data_query",  # 意图类型
                "confidence": 0.9,        # 置信度
                "reason": "...",          # 识别原因
                "need_data_analysis": True # 是否需要数据分析
            }
        """
        try:
            prompt = INTENT_RECOGNITION_PROMPT.format(user_question=user_question)
            result = self.glm_client.parse_json_response(prompt)
            
            # 如果解析失败，使用默认值
            if "error" in result:
                logger.warning(f"意图识别JSON解析失败，使用默认值: {result}")
                result = {
                    "intent": "general_chat",
                    "confidence": 0.5,
                    "reason": "JSON解析失败，使用默认意图",
                    "need_data_analysis": False
                }
            
            logger.info(f"意图识别结果: {result}")
            return result
            
        except Exception as e:
            logger.error(f"意图识别失败: {e}")
            return {
                "intent": "general_chat",
                "confidence": 0.0,
                "reason": f"识别过程出错: {str(e)}",
                "need_data_analysis": False
            }
    

    def create_intent_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建用于状态图的意图识别节点函数
        
        Args:
            state: 工作流状态
            
        Returns:
            更新后的状态
        """
        try:
            user_question = state["user_question"]
            intent_result = self.parse_intent(user_question)
            state["intent_result"] = intent_result
            
        except Exception as e:
            logger.error(f"意图识别节点执行失败: {e}")
            state["intent_result"] = {
                "intent": "general_chat",
                "confidence": 0.0,
                "reason": f"节点执行出错: {str(e)}",
                "need_data_analysis": False
            }
            state["error_message"] = str(e)
        
        return state

# 全局意图解析器实例
_intent_parser = None

def get_intent_parser() -> IntentParser:
    """
    获取全局意图解析器实例
    
    Returns:
        意图解析器实例
    """
    global _intent_parser
    if _intent_parser is None:
        _intent_parser = IntentParser()
    return _intent_parser

if __name__ == "__main__":
    # 简单测试
    parser = IntentParser()
    
    test_questions = [
        "你有什么数据？",
        "查询用户表中年龄大于25的记录",
        "分析销售数据的趋势",
        "你好，今天天气怎么样？"
    ]
    
    for question in test_questions:
        print(f"\n问题: {question}")
        result = parser.parse_intent(question)
        print(f"结果: {result}")