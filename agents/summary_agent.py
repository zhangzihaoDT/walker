#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Summary Agent - 负责跨模块结果的综合解读

生成面向用户的总结与后续建议，支持用户反馈决定是否进入新一轮Walker策略分析。
"""

import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
import sys
import json
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from llm.glm import get_glm_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SummaryAgent:
    """综合解读代理类"""
    
    def __init__(self, mock_client=None):
        """初始化Summary Agent
        
        Args:
            mock_client: 可选的模拟客户端，用于测试
        """
        self._glm_client = mock_client
        self._client_initialized = mock_client is not None
        logger.info("Summary Agent初始化成功")
    
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
    
    def generate_comprehensive_summary(
        self, 
        user_question: str,
        intent_result: Dict[str, Any],
        execution_results: List[Dict[str, Any]],
        walker_strategy: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        生成综合分析总结
        
        Args:
            user_question: 用户原始问题
            intent_result: 意图解析结果
            execution_results: 模块执行结果列表
            walker_strategy: Walker策略信息
            
        Returns:
            综合总结结果
        """
        try:
            # 分析执行结果
            analysis_summary = self._analyze_execution_results(execution_results)
            
            # 生成主要发现
            key_findings = self._extract_key_findings(execution_results, intent_result)
            
            # 生成后续建议
            follow_up_suggestions = self._generate_follow_up_suggestions(
                user_question, intent_result, analysis_summary, walker_strategy
            )
            
            # 生成用户友好的总结
            user_summary = self._generate_user_friendly_summary(
                user_question, key_findings, analysis_summary
            )
            
            # 构建完整的总结结果
            summary_result = {
                "user_question": user_question,
                "analysis_summary": analysis_summary,
                "key_findings": key_findings,
                "user_summary": user_summary,
                "follow_up_suggestions": follow_up_suggestions,
                "execution_metadata": {
                    "modules_executed": [result.get("module_id", "unknown") for result in execution_results],
                    "execution_time": datetime.now().isoformat(),
                    "success_rate": self._calculate_success_rate(execution_results),
                    "total_steps": len(execution_results)
                },
                "walker_context": {
                    "strategy_used": walker_strategy.get("strategy_type", "unknown"),
                    "databases_accessed": walker_strategy.get("databases", []),
                    "complexity_level": intent_result.get("complexity", "simple")
                }
            }
            
            logger.info(f"综合总结生成成功，包含{len(key_findings)}个关键发现")
            return summary_result
            
        except Exception as e:
            logger.error(f"综合总结生成失败: {e}")
            return self._generate_fallback_summary(user_question, str(e))
    
    def _analyze_execution_results(self, execution_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        分析执行结果
        
        Args:
            execution_results: 执行结果列表
            
        Returns:
            分析总结
        """
        successful_modules = []
        failed_modules = []
        total_records_processed = 0
        insights_generated = []
        
        for result in execution_results:
            module_id = result.get("module_id", "unknown")
            
            if result.get("success", False):
                successful_modules.append(module_id)
                
                # 提取处理的记录数
                if "metadata" in result and "records_processed" in result["metadata"]:
                    total_records_processed += result["metadata"]["records_processed"]
                
                # 提取洞察
                if "insights" in result:
                    insights_generated.extend(result["insights"])
            else:
                failed_modules.append({
                    "module_id": module_id,
                    "error": result.get("error", "未知错误")
                })
        
        return {
            "successful_modules": successful_modules,
            "failed_modules": failed_modules,
            "total_records_processed": total_records_processed,
            "insights_generated": insights_generated,
            "success_rate": len(successful_modules) / len(execution_results) if execution_results else 0
        }
    
    def _extract_key_findings(self, execution_results: List[Dict[str, Any]], intent_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        提取关键发现
        
        Args:
            execution_results: 执行结果列表
            intent_result: 意图解析结果
            
        Returns:
            关键发现列表
        """
        key_findings = []
        
        for result in execution_results:
            if not result.get("success", False):
                continue
            
            module_id = result.get("module_id", "unknown")
            module_output = result.get("output", {})
            
            # 根据模块类型提取不同的关键发现
            if module_id == "param_segmenter":
                findings = self._extract_segmentation_findings(module_output)
            elif module_id == "trend_analysis":
                findings = self._extract_trend_findings(module_output)
            elif module_id == "yoy_comparison":
                findings = self._extract_comparison_findings(module_output)
            else:
                findings = self._extract_generic_findings(module_output)
            
            for finding in findings:
                finding["source_module"] = module_id
                key_findings.append(finding)
        
        # 按重要性排序
        key_findings.sort(key=lambda x: x.get("importance", 0), reverse=True)
        
        return key_findings[:10]  # 最多返回10个关键发现
    
    def _extract_segmentation_findings(self, output: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        提取细分分析的关键发现
        
        Args:
            output: 模块输出
            
        Returns:
            关键发现列表
        """
        findings = []
        
        segments = output.get("segments", {})
        statistics = output.get("statistics", {})
        
        # 数据分布发现
        if segments:
            segment_count = len(segments)
            findings.append({
                "type": "data_distribution",
                "title": "数据细分结果",
                "description": f"数据被成功细分为{segment_count}个不同的段",
                "value": segment_count,
                "importance": 8
            })
        
        # 覆盖率发现
        coverage_rate = statistics.get("coverage_rate", 0)
        if coverage_rate > 0:
            findings.append({
                "type": "coverage_analysis",
                "title": "数据覆盖率",
                "description": f"细分分析覆盖了{coverage_rate:.1%}的原始数据",
                "value": coverage_rate,
                "importance": 7
            })
        
        return findings
    
    def _extract_trend_findings(self, output: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        提取趋势分析的关键发现
        
        Args:
            output: 模块输出
            
        Returns:
            关键发现列表
        """
        findings = []
        
        trend_direction = output.get("trend_direction", "unknown")
        trend_strength = output.get("trend_strength", 0)
        
        # 趋势方向发现
        if trend_direction != "unknown":
            direction_desc = {
                "increasing": "上升",
                "decreasing": "下降",
                "stable": "平稳"
            }.get(trend_direction, trend_direction)
            
            findings.append({
                "type": "trend_direction",
                "title": "趋势方向",
                "description": f"数据呈现{direction_desc}趋势，强度为{trend_strength:.2f}",
                "value": trend_direction,
                "importance": 9
            })
        
        # 拐点发现
        turning_points = output.get("turning_points", [])
        if turning_points:
            findings.append({
                "type": "turning_points",
                "title": "趋势拐点",
                "description": f"检测到{len(turning_points)}个重要的趋势拐点",
                "value": len(turning_points),
                "importance": 8
            })
        
        return findings
    
    def _extract_comparison_findings(self, output: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        提取对比分析的关键发现
        
        Args:
            output: 模块输出
            
        Returns:
            关键发现列表
        """
        findings = []
        
        avg_growth_rate = output.get("average_growth_rate", 0)
        latest_growth_rate = output.get("latest_growth_rate", 0)
        
        # 平均增长率发现
        if avg_growth_rate != 0:
            growth_desc = "增长" if avg_growth_rate > 0 else "下降"
            findings.append({
                "type": "average_growth",
                "title": "平均增长率",
                "description": f"平均同比{growth_desc}{abs(avg_growth_rate):.1%}",
                "value": avg_growth_rate,
                "importance": 9
            })
        
        # 最新增长率发现
        if latest_growth_rate != 0:
            growth_desc = "增长" if latest_growth_rate > 0 else "下降"
            findings.append({
                "type": "latest_growth",
                "title": "最新增长率",
                "description": f"最近期同比{growth_desc}{abs(latest_growth_rate):.1%}",
                "value": latest_growth_rate,
                "importance": 8
            })
        
        return findings
    
    def _extract_generic_findings(self, output: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        提取通用发现
        
        Args:
            output: 模块输出
            
        Returns:
            关键发现列表
        """
        findings = []
        
        # 通用统计信息
        if "summary" in output:
            findings.append({
                "type": "general_summary",
                "title": "分析总结",
                "description": str(output["summary"])[:200],  # 限制长度
                "value": output["summary"],
                "importance": 5
            })
        
        return findings
    
    def _generate_follow_up_suggestions(self, user_question: str, intent_result: Dict[str, Any],
                                       analysis_summary: Dict[str, Any], walker_strategy: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        生成后续分析建议
        
        Args:
            user_question: 用户问题
            intent_result: 意图解析结果
            analysis_summary: 分析总结
            walker_strategy: Walker策略
            
        Returns:
            后续建议列表
        """
        suggestions = []
        
        # 基于成功的模块生成建议
        successful_modules = analysis_summary.get("successful_modules", [])
        executed_modules = set(successful_modules)
        
        # 定义可用的分析模块
        available_modules = {"data_describe", "param_segmenter", "trend_analysis", "yoy_comparison"}
        missing_modules = available_modules - executed_modules
        
        # 智能推荐缺失的分析维度
        if "trend_analysis" not in executed_modules and "yoy_comparison" not in executed_modules:
            suggestions.append({
                "type": "trend_analysis",
                "title": "趋势分析建议",
                "description": "深入分析数据的时间趋势变化，识别增长模式和拐点",
                "action": "进行趋势分析以了解数据变化规律",
                "priority": "high",
                "trigger_analysis": True,
                "suggested_modules": ["trend_analysis"]
            })
        
        if "yoy_comparison" not in executed_modules and ("trend_analysis" in executed_modules or "2024" in user_question):
            suggestions.append({
                "type": "yoy_comparison",
                "title": "同比分析建议",
                "description": "进行年度对比分析，量化增长幅度和变化趋势",
                "action": "进行同比分析以了解年度增长情况",
                "priority": "high",
                "trigger_analysis": True,
                "suggested_modules": ["yoy_comparison"]
            })
        
        if "param_segmenter" not in executed_modules and len(executed_modules) >= 2:
            suggestions.append({
                "type": "segmentation_analysis",
                "title": "细分分析建议",
                "description": "按不同维度对数据进行细分，发现各细分市场的表现差异",
                "action": "进行参数细分分析以了解不同维度的表现",
                "priority": "medium",
                "trigger_analysis": True,
                "suggested_modules": ["param_segmenter"]
            })
        
        # 基于已执行模块的组合建议
        if "trend_analysis" in executed_modules and "param_segmenter" not in executed_modules:
            suggestions.append({
                "type": "combined_analysis",
                "title": "组合分析建议",
                "description": "结合趋势分析和细分分析，深入了解不同细分市场的趋势差异",
                "action": "进行细分趋势组合分析",
                "priority": "high",
                "trigger_analysis": True,
                "suggested_modules": ["param_segmenter", "trend_analysis"]
            })
        
        if "yoy_comparison" in executed_modules and "trend_analysis" not in executed_modules:
            suggestions.append({
                "type": "trend_comparison",
                "title": "趋势对比建议",
                "description": "结合同比分析和趋势分析，全面了解增长模式和趋势变化",
                "action": "进行趋势对比分析",
                "priority": "high",
                "trigger_analysis": True,
                "suggested_modules": ["trend_analysis", "yoy_comparison"]
            })
        
        # 基于分析结果的深度建议
        if len(executed_modules) >= 3:
            suggestions.append({
                "type": "comprehensive_insight",
                "title": "综合洞察建议",
                "description": "基于多维度分析结果，生成综合性的商业洞察和决策建议",
                "action": "生成综合商业洞察报告",
                "priority": "medium",
                "trigger_analysis": False
            })
        
        # 数据质量和完整性建议
        if analysis_summary.get("success_rate", 1) < 1:
            suggestions.append({
                "type": "data_quality",
                "title": "数据质量优化",
                "description": "部分分析模块执行失败，建议检查数据质量和完整性",
                "action": "检查和清理数据质量问题",
                "priority": "high",
                "trigger_analysis": False
            })
        
        # 如果只执行了基础分析，强烈建议深入分析
        if len(executed_modules) == 1 and "data_describe" in executed_modules:
            suggestions.insert(0, {
                "type": "deep_dive_analysis",
                "title": "深度分析建议",
                "description": "当前只进行了基础数据描述，强烈建议进行更深入的分析以获得有价值的洞察",
                "action": "进行多维度深度分析",
                "priority": "high",
                "trigger_analysis": True,
                "suggested_modules": ["trend_analysis", "yoy_comparison"]
            })
        
        # 按优先级排序并限制数量
        priority_order = {"high": 3, "medium": 2, "low": 1}
        suggestions.sort(key=lambda x: priority_order.get(x["priority"], 0), reverse=True)
        
        return suggestions[:6]  # 最多返回6个建议
    
    def _generate_user_friendly_summary(self, user_question: str, key_findings: List[Dict[str, Any]], 
                                       analysis_summary: Dict[str, Any]) -> str:
        """
        生成用户友好的总结
        
        Args:
            user_question: 用户问题
            key_findings: 关键发现
            analysis_summary: 分析总结
            
        Returns:
            用户友好的总结文本
        """
        try:
            # 构建总结提示词
            findings_text = "\n".join([f"- {finding['title']}: {finding['description']}" for finding in key_findings[:5]])
            
            prompt = f"""
请基于以下分析结果，为用户生成一个简洁、易懂的总结回答。

用户问题：{user_question}

关键发现：
{findings_text}

分析概况：
- 成功执行的模块：{', '.join(analysis_summary.get('successful_modules', []))}
- 处理的数据记录数：{analysis_summary.get('total_records_processed', 0)}
- 执行成功率：{analysis_summary.get('success_rate', 0):.1%}

请生成一个自然、友好的回答，直接回应用户的问题，突出最重要的发现和洞察。
回答应该：
1. 直接回应用户的问题
2. 用通俗易懂的语言解释关键发现
3. 提供具体的数据支撑
4. 保持简洁明了

请直接返回回答内容，不要包含格式标记。
"""
            
            response = self.glm_client.generate_response(prompt)
            return response
            
        except Exception as e:
            logger.error(f"生成用户友好总结失败: {e}")
            # 降级到简单的模板总结
            return self._generate_template_summary(user_question, key_findings, analysis_summary)
    
    def _generate_template_summary(self, user_question: str, key_findings: List[Dict[str, Any]], 
                                 analysis_summary: Dict[str, Any]) -> str:
        """
        生成模板化总结（降级方案）
        
        Args:
            user_question: 用户问题
            key_findings: 关键发现
            analysis_summary: 分析总结
            
        Returns:
            模板化总结文本
        """
        summary_parts = []
        
        # 开头
        summary_parts.append(f"针对您的问题「{user_question}」，我进行了数据分析，以下是主要发现：")
        
        # 关键发现
        if key_findings:
            summary_parts.append("\n主要发现：")
            for i, finding in enumerate(key_findings[:3], 1):
                summary_parts.append(f"{i}. {finding['description']}")
        
        # 分析概况
        successful_modules = analysis_summary.get('successful_modules', [])
        if successful_modules:
            summary_parts.append(f"\n本次分析使用了{len(successful_modules)}个分析模块，处理了{analysis_summary.get('total_records_processed', 0)}条数据记录。")
        
        return "\n".join(summary_parts)
    
    def _calculate_success_rate(self, execution_results: List[Dict[str, Any]]) -> float:
        """
        计算执行成功率
        
        Args:
            execution_results: 执行结果列表
            
        Returns:
            成功率
        """
        if not execution_results:
            return 0.0
        
        successful_count = sum(1 for result in execution_results if result.get("success", False))
        return successful_count / len(execution_results)
    
    def _generate_fallback_summary(self, user_question: str, error_message: str) -> Dict[str, Any]:
        """
        生成降级总结
        
        Args:
            user_question: 用户问题
            error_message: 错误信息
            
        Returns:
            降级总结结果
        """
        return {
            "user_question": user_question,
            "analysis_summary": {
                "successful_modules": [],
                "failed_modules": [],
                "total_records_processed": 0,
                "insights_generated": [],
                "success_rate": 0
            },
            "key_findings": [],
            "user_summary": f"抱歉，在处理您的问题「{user_question}」时遇到了技术问题：{error_message}。请稍后重试或联系技术支持。",
            "follow_up_suggestions": [
                {
                    "type": "retry",
                    "title": "重试建议",
                    "description": "建议稍后重新提问或简化问题",
                    "action": "重新提问",
                    "priority": "high"
                }
            ],
            "execution_metadata": {
                "modules_executed": [],
                "execution_time": datetime.now().isoformat(),
                "success_rate": 0,
                "total_steps": 0
            },
            "walker_context": {
                "strategy_used": "error",
                "databases_accessed": [],
                "complexity_level": "unknown"
            }
        }
    
    def generate_follow_up_questions(self, summary_result: Dict[str, Any]) -> List[str]:
        """
        基于总结结果生成后续问题建议
        
        Args:
            summary_result: 总结结果
            
        Returns:
            后续问题列表
        """
        questions = []
        
        # 基于关键发现生成问题
        key_findings = summary_result.get("key_findings", [])
        for finding in key_findings[:3]:
            finding_type = finding.get("type", "")
            
            if finding_type == "trend_direction":
                questions.append("这个趋势的原因是什么？")
                questions.append("未来趋势会如何发展？")
            elif finding_type == "data_distribution":
                questions.append("各个细分段的表现有什么差异？")
                questions.append("哪个细分段表现最好？")
            elif finding_type == "average_growth":
                questions.append("增长的主要驱动因素是什么？")
                questions.append("不同时期的增长率有什么变化？")
        
        # 基于后续建议生成问题
        suggestions = summary_result.get("follow_up_suggestions", [])
        for suggestion in suggestions[:2]:
            if suggestion.get("type") == "deep_analysis":
                questions.append("能否对各个细分进行更详细的分析？")
            elif suggestion.get("type") == "comparison_analysis":
                questions.append("能否进行同比分析？")
        
        # 去重并限制数量
        unique_questions = list(dict.fromkeys(questions))  # 去重
        return unique_questions[:5]  # 最多返回5个问题

# 全局Summary Agent实例
_summary_agent = None

def get_summary_agent() -> SummaryAgent:
    """
    获取全局Summary Agent实例
    
    Returns:
        Summary Agent实例
    """
    global _summary_agent
    if _summary_agent is None:
        _summary_agent = SummaryAgent()
    return _summary_agent

if __name__ == "__main__":
    # 简单测试
    agent = SummaryAgent()
    
    # 模拟测试数据
    test_execution_results = [
        {
            "module_id": "param_segmenter",
            "success": True,
            "output": {
                "segments": {"A": 100, "B": 200},
                "statistics": {"coverage_rate": 0.95}
            },
            "metadata": {"records_processed": 300}
        },
        {
            "module_id": "trend_analysis",
            "success": True,
            "output": {
                "trend_direction": "increasing",
                "trend_strength": 0.85,
                "turning_points": ["2023-06", "2023-09"]
            },
            "metadata": {"records_processed": 300}
        }
    ]
    
    test_intent = {
        "intent": "data_analysis",
        "complexity": "medium",
        "analysis_type": "trend_analysis"
    }
    
    test_strategy = {
        "strategy_type": "multi_module",
        "databases": ["sales_data"]
    }
    
    result = agent.generate_comprehensive_summary(
        "分析一下销售趋势",
        test_intent,
        test_execution_results,
        test_strategy
    )
    
    print("✅ Summary Agent测试完成")
    print(f"生成了{len(result['key_findings'])}个关键发现")
    print(f"生成了{len(result['follow_up_suggestions'])}个后续建议")