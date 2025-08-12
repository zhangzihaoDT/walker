#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
核心工作流模块 - 处理用户请求的完整流程
"""

import os
import sys
import json
import logging
import traceback
from pathlib import Path
from typing import Dict, Any, Tuple
from io import StringIO

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from llm.glm import get_glm_client
from llm.prompts import (
    INTENT_RECOGNITION_PROMPT,
    DATA_ANALYSIS_EXPLANATION_PROMPT,
    GENERAL_CHAT_PROMPT,
    ERROR_HANDLING_PROMPT
)
from modules.run_data_describe import DataAnalyzer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataChatWorkflow:
    """数据聊天工作流类"""
    
    def __init__(self):
        """
        初始化工作流
        """
        self.glm_client = get_glm_client()
        self.data_analyzer = DataAnalyzer()
        logger.info("数据聊天工作流初始化成功")
    
    def recognize_intent(self, user_question: str) -> Dict[str, Any]:
        """
        识别用户意图
        
        Args:
            user_question: 用户问题
            
        Returns:
            意图识别结果
        """
        try:
            prompt = INTENT_RECOGNITION_PROMPT.format(user_question=user_question)
            result = self.glm_client.parse_json_response(prompt)
            
            # 如果解析失败，使用默认值
            if "error" in result:
                logger.warning(f"意图识别JSON解析失败，使用默认值: {result}")
                return {
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
    
    def run_data_analysis(self) -> Tuple[bool, str]:
        """
        运行数据分析
        
        Returns:
            (是否成功, 分析结果或错误信息)
        """
        try:
            # 捕获数据分析的输出
            old_stdout = sys.stdout
            sys.stdout = captured_output = StringIO()
            
            try:
                # 运行数据分析
                self.data_analyzer.analyze_all_data()
                analysis_result = captured_output.getvalue()
                
                if analysis_result.strip():
                    logger.info("数据分析执行成功")
                    return True, analysis_result
                else:
                    return False, "数据分析没有产生输出结果"
                    
            finally:
                sys.stdout = old_stdout
                
        except Exception as e:
            logger.error(f"数据分析执行失败: {e}")
            return False, f"数据分析执行出错: {str(e)}\n{traceback.format_exc()}"
    
    def generate_response(self, user_question: str, intent_result: Dict[str, Any], 
                         analysis_result: str = None) -> str:
        """
        生成最终响应
        
        Args:
            user_question: 用户问题
            intent_result: 意图识别结果
            analysis_result: 数据分析结果（可选）
            
        Returns:
            最终响应内容
        """
        try:
            intent = intent_result.get("intent", "general_chat")
            
            if intent in ["data_query", "data_analysis"] and analysis_result:
                # 数据相关问题，使用分析结果生成回答
                prompt = DATA_ANALYSIS_EXPLANATION_PROMPT.format(
                    user_question=user_question,
                    analysis_result=analysis_result
                )
                response = self.glm_client.generate_response(prompt)
                
            elif intent == "general_chat":
                # 一般对话
                prompt = GENERAL_CHAT_PROMPT.format(user_question=user_question)
                response = self.glm_client.generate_response(prompt)
                
            else:
                # 其他情况或错误处理
                response = "抱歉，我无法理解您的问题。请尝试询问关于数据的问题，比如'你有什么数据'或'数据范围有哪些'。"
            
            logger.info("响应生成成功")
            return response
            
        except Exception as e:
            logger.error(f"响应生成失败: {e}")
            error_prompt = ERROR_HANDLING_PROMPT.format(
                user_question=user_question,
                error_message=str(e)
            )
            try:
                return self.glm_client.generate_response(error_prompt)
            except:
                return f"抱歉，处理您的请求时出现错误：{str(e)}"
    
    def process_user_question(self, user_question: str) -> Dict[str, Any]:
        """
        处理用户问题的完整流程
        
        Args:
            user_question: 用户问题
            
        Returns:
            包含处理结果的字典
        """
        logger.info(f"开始处理用户问题: {user_question}")
        
        # 步骤1: 意图识别
        intent_result = self.recognize_intent(user_question)
        
        # 步骤2: 根据意图决定是否需要数据分析
        analysis_result = None
        analysis_success = False
        
        if intent_result.get("need_data_analysis", False):
            logger.info("需要执行数据分析")
            analysis_success, analysis_result = self.run_data_analysis()
            
            if not analysis_success:
                logger.warning(f"数据分析失败: {analysis_result}")
        
        # 步骤3: 生成最终响应
        final_response = self.generate_response(
            user_question, 
            intent_result, 
            analysis_result if analysis_success else None
        )
        
        # 返回完整的处理结果
        result = {
            "user_question": user_question,
            "intent": intent_result,
            "data_analysis": {
                "executed": intent_result.get("need_data_analysis", False),
                "success": analysis_success,
                "result": analysis_result if analysis_success else None,
                "error": analysis_result if not analysis_success and analysis_result else None
            },
            "final_response": final_response,
            "timestamp": str(Path(__file__).stat().st_mtime)  # 简单的时间戳
        }
        
        logger.info("用户问题处理完成")
        return result
    



# 全局工作流实例
_workflow = None

def get_workflow() -> DataChatWorkflow:
    """
    获取全局工作流实例
    
    Returns:
        工作流实例
    """
    global _workflow
    if _workflow is None:
        _workflow = DataChatWorkflow()
    return _workflow


if __name__ == "__main__":
    # 简单测试
    workflow = DataChatWorkflow()
    print("✅ 工作流初始化成功")