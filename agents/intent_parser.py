#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
意图解析器 - 负责解析用户输入的意图和需求

提取用户核心需求，识别数据分析意图，为Walker策略提供输入。
"""

import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
import sys
import json
import re

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from llm.glm import get_glm_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IntentParser:
    """意图解析器类"""
    
    def __init__(self, mock_client=None):
        """
        初始化意图解析器
        
        Args:
            mock_client: 可选的模拟客户端，用于测试
        """
        self._glm_client = mock_client
        self._client_initialized = mock_client is not None
        logger.info("意图解析器初始化完成")
    
    @property
    def glm_client(self):
        """
        延迟初始化GLM客户端
        """
        if not self._client_initialized:
            try:
                self._glm_client = get_glm_client()
                self._client_initialized = True
            except Exception as e:
                logger.error(f"GLM客户端初始化失败: {e}")
                raise
        return self._glm_client
    
    def parse_intent(self, user_question: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        解析用户意图
        
        Args:
            user_question: 用户问题
            context: 上下文信息（可选）
            
        Returns:
            意图解析结果
        """
        try:
            # 构建意图识别提示词
            prompt = self._build_intent_prompt(user_question, context)
            
            # 调用LLM进行意图识别
            result = self.glm_client.parse_json_response(prompt)
            
            # 验证和标准化结果
            parsed_result = self._validate_and_normalize_result(result, user_question)
            
            logger.info(f"意图解析完成: {parsed_result['intent']} (置信度: {parsed_result['confidence']})")
            return parsed_result
            
        except Exception as e:
            logger.error(f"意图解析失败: {e}")
            return self._get_fallback_result(user_question, str(e))
    
    def _build_intent_prompt(self, user_question: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        构建意图识别提示词
        
        Args:
            user_question: 用户问题
            context: 上下文信息
            
        Returns:
            构建的提示词
        """
        context_info = ""
        if context:
            context_info = f"\n\n上下文信息：\n{json.dumps(context, ensure_ascii=False, indent=2)}"
        
        prompt = f"""
你是一个专业的数据分析意图识别专家。请分析用户的问题，识别其意图和需求。

用户问题：{user_question}{context_info}

请分析并返回JSON格式的结果，包含以下字段：

{{
    "intent": "意图类型",
    "confidence": 置信度(0.0-1.0),
    "reason": "判断理由",
    "need_data_analysis": true/false,
    "analysis_type": "分析类型",
    "target_fields": ["目标字段列表"],
    "time_dimension": "时间维度",
    "grouping_fields": ["分组字段列表"],
    "comparison_type": "对比类型",
    "keywords": ["关键词列表"],
    "complexity": "复杂度等级"
}}

重要判断规则：
1. 涉及销量、表现、业绩、数据查看等关键词时，need_data_analysis应设为true
2. 询问具体公司、产品、时间段的数据时，应触发数据分析
3. 只有纯粹的问候、闲聊才设为false

意图类型包括：
- data_query: 数据查询（查看数据、了解数据结构等）
- data_analysis: 数据分析（趋势分析、对比分析、统计分析等）
- data_comparison: 数据对比（同比、环比、分组对比等）
- data_segmentation: 数据细分（按维度切分、分组统计等）
- general_chat: 一般对话（问候、闲聊等）
- help_request: 帮助请求（功能说明、使用指导等）

分析类型包括：
- trend_analysis: 趋势分析
- yoy_comparison: 同比分析
- segmentation: 参数细分
- statistical_summary: 统计汇总
- correlation_analysis: 相关性分析
- none: 无需分析

复杂度等级：
- simple: 简单（单一维度、基础统计）
- medium: 中等（多维度、基础分析）
- complex: 复杂（多模块串联、深度分析）

请仔细分析用户问题的语义和意图，给出准确的判断。
"""
        return prompt
    
    def _validate_and_normalize_result(self, result: Dict[str, Any], user_question: str) -> Dict[str, Any]:
        """
        验证和标准化解析结果
        
        Args:
            result: 原始解析结果
            user_question: 用户问题
            
        Returns:
            标准化后的结果
        """
        # 如果解析失败，使用规则方法
        if "error" in result:
            logger.warning(f"LLM解析失败，使用规则方法: {result}")
            return self._rule_based_parsing(user_question)
        
        # 标准化字段
        normalized = {
            "intent": result.get("intent", "general_chat"),
            "confidence": float(result.get("confidence", 0.5)),
            "reason": result.get("reason", "基于语义分析"),
            "need_data_analysis": bool(result.get("need_data_analysis", False)),
            "analysis_type": result.get("analysis_type", "none"),
            "target_fields": result.get("target_fields", []),
            "time_dimension": result.get("time_dimension", ""),
            "grouping_fields": result.get("grouping_fields", []),
            "comparison_type": result.get("comparison_type", ""),
            "keywords": result.get("keywords", []),
            "complexity": result.get("complexity", "simple")
        }
        
        # 验证置信度范围
        if not 0.0 <= normalized["confidence"] <= 1.0:
            normalized["confidence"] = 0.5
        
        # 验证意图类型
        valid_intents = ["data_query", "data_analysis", "data_comparison", 
                        "data_segmentation", "general_chat", "help_request"]
        if normalized["intent"] not in valid_intents:
            normalized["intent"] = "general_chat"
        
        return normalized
    
    def _rule_based_parsing(self, user_question: str) -> Dict[str, Any]:
        """
        基于规则的意图解析（备用方法）
        
        Args:
            user_question: 用户问题
            
        Returns:
            解析结果
        """
        question_lower = user_question.lower()
        
        # 数据查询关键词
        query_keywords = ["数据", "有什么", "查看", "显示", "列出", "销量", "表现", "业绩", "data", "show", "list", "sales", "performance"]
        
        # 分析关键词
        analysis_keywords = ["分析", "趋势", "变化", "增长", "下降", "analysis", "trend", "growth"]
        
        # 对比关键词
        comparison_keywords = ["对比", "比较", "同比", "环比", "compare", "comparison", "yoy"]
        
        # 细分关键词
        segmentation_keywords = ["分组", "细分", "按", "分类", "segment", "group", "category"]
        
        # 判断意图
        if any(keyword in question_lower for keyword in comparison_keywords):
            intent = "data_comparison"
            analysis_type = "yoy_comparison"
            need_analysis = True
            complexity = "medium"
        elif any(keyword in question_lower for keyword in segmentation_keywords):
            intent = "data_segmentation"
            analysis_type = "segmentation"
            need_analysis = True
            complexity = "medium"
        elif any(keyword in question_lower for keyword in analysis_keywords):
            intent = "data_analysis"
            analysis_type = "trend_analysis"
            need_analysis = True
            complexity = "medium"
        elif any(keyword in question_lower for keyword in query_keywords):
            intent = "data_query"
            analysis_type = "statistical_summary"
            need_analysis = True
            complexity = "simple"
        else:
            intent = "general_chat"
            analysis_type = "none"
            need_analysis = False
            complexity = "simple"
        
        return {
            "intent": intent,
            "confidence": 0.7,
            "reason": "基于关键词规则匹配",
            "need_data_analysis": need_analysis,
            "analysis_type": analysis_type,
            "target_fields": [],
            "time_dimension": "",
            "grouping_fields": [],
            "comparison_type": "",
            "keywords": self._extract_keywords(user_question),
            "complexity": complexity
        }
    
    def _extract_keywords(self, text: str) -> List[str]:
        """
        提取关键词
        
        Args:
            text: 输入文本
            
        Returns:
            关键词列表
        """
        # 简单的关键词提取
        keywords = []
        
        # 常见的数据分析关键词
        data_keywords = [
            "销售", "收入", "利润", "用户", "订单", "产品", "类别", "地区", "时间", "日期",
            "sales", "revenue", "profit", "user", "order", "product", "category", "region", "time", "date"
        ]
        
        text_lower = text.lower()
        for keyword in data_keywords:
            if keyword in text_lower:
                keywords.append(keyword)
        
        return keywords
    
    def _get_fallback_result(self, user_question: str, error_message: str) -> Dict[str, Any]:
        """
        获取降级结果（使用规则解析）
        
        Args:
            user_question: 用户问题
            error_message: 错误信息
            
        Returns:
            降级结果
        """
        logger.warning(f"LLM解析失败，使用规则解析: {error_message}")
        # 使用规则解析作为降级方案
        rule_result = self._rule_based_parsing(user_question)
        rule_result["reason"] = f"LLM解析失败，使用规则解析: {error_message}"
        rule_result["confidence"] = 0.6  # 规则解析的置信度
        return rule_result
    
    def extract_analysis_requirements(self, intent_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        从意图结果中提取分析需求
        
        Args:
            intent_result: 意图解析结果
            
        Returns:
            分析需求
        """
        requirements = {
            "modules_needed": [],
            "execution_order": [],
            "parameters": {},
            "data_requirements": {
                "fields": intent_result.get("target_fields", []),
                "time_field": intent_result.get("time_dimension", ""),
                "grouping_fields": intent_result.get("grouping_fields", [])
            }
        }
        
        analysis_type = intent_result.get("analysis_type", "none")
        complexity = intent_result.get("complexity", "simple")
        intent_type = intent_result.get("intent", "general_chat")
        keywords = intent_result.get("keywords", [])
        
        # 始终包含数据描述模块作为基础
        if intent_result.get("need_data_analysis", False):
            requirements["modules_needed"].append("data_describe")
            requirements["execution_order"].append("data_describe")
        
        # 根据关键词和意图类型智能推断需要的模块
        performance_keywords = ["销量", "表现", "业绩", "增长", "下降", "变化", "趋势"]
        comparison_keywords = ["对比", "比较", "同比", "环比", "年度", "月度"]
        segmentation_keywords = ["分类", "细分", "按", "分组", "维度"]
        
        has_performance = any(keyword in ' '.join(keywords) for keyword in performance_keywords)
        has_comparison = any(keyword in ' '.join(keywords) for keyword in comparison_keywords)
        has_segmentation = any(keyword in ' '.join(keywords) for keyword in segmentation_keywords)
        
        # 根据分析类型确定需要的模块
        if analysis_type == "trend_analysis" or has_performance:
            if "trend_analysis" not in requirements["modules_needed"]:
                requirements["modules_needed"].append("trend_analysis")
                requirements["execution_order"].append("trend_analysis")
        
        if analysis_type == "yoy_comparison" or has_comparison:
            if "yoy_comparison" not in requirements["modules_needed"]:
                requirements["modules_needed"].append("yoy_comparison")
                requirements["execution_order"].append("yoy_comparison")
        
        if analysis_type == "segmentation" or has_segmentation:
            if "param_segmenter" not in requirements["modules_needed"]:
                requirements["modules_needed"].append("param_segmenter")
                requirements["execution_order"].append("param_segmenter")
        
        # 对于复杂的业绩分析问题，自动组合多个模块
        if (intent_type == "data_analysis" and 
            (has_performance or "表现" in ' '.join(keywords) or "销量" in ' '.join(keywords))):
            
            # 添加趋势分析模块
            if "trend_analysis" not in requirements["modules_needed"]:
                requirements["modules_needed"].append("trend_analysis")
                requirements["execution_order"].append("trend_analysis")
            
            # 如果涉及时间维度，添加同比分析
            if ("2024" in ' '.join(keywords) or "年" in ' '.join(keywords) or 
                intent_result.get("time_dimension")):
                if "yoy_comparison" not in requirements["modules_needed"]:
                    requirements["modules_needed"].append("yoy_comparison")
                    requirements["execution_order"].append("yoy_comparison")
        
        # 复杂分析增强逻辑
        if complexity == "complex" or len(requirements["modules_needed"]) > 2:
            # 确保有参数细分模块用于多维度分析
            if "param_segmenter" not in requirements["modules_needed"]:
                requirements["modules_needed"].insert(-1, "param_segmenter")
                requirements["execution_order"].insert(-1, "param_segmenter")
        
        # 如果没有识别到特定模块，至少保证有数据描述
        if not requirements["modules_needed"] and intent_result.get("need_data_analysis", False):
            requirements["modules_needed"] = ["data_describe"]
            requirements["execution_order"] = ["data_describe"]
        
        logger.info(f"提取的分析需求: 模块={requirements['modules_needed']}, 执行顺序={requirements['execution_order']}")
        return requirements

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
        "分析一下销售趋势",
        "按产品类别对比销售额",
        "今年和去年的销售对比"
    ]
    
    for question in test_questions:
        result = parser.parse_intent(question)
        print(f"问题: {question}")
        print(f"意图: {result['intent']} (置信度: {result['confidence']})")
        print(f"需要分析: {result['need_data_analysis']}")
        print("---")
    
    print("✅ 意图解析器测试完成")