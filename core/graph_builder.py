#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Graph Builder - 使用LangGraph构建状态图

负责构建和管理数据聊天系统的状态图，包括意图识别、数据分析和响应生成节点。
集成Walker模块进行智能策略生成和执行。
"""

import logging
from typing import Dict, Any, TypedDict, Annotated, List
from pathlib import Path
import sys

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
from .walker import get_walker
from agents.module_executor import get_module_executor
from agents.intent_parser import get_intent_parser
from agents.summary_agent import get_summary_agent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 定义状态类型
class WorkflowState(TypedDict):
    """工作流状态定义"""
    user_question: str
    intent_result: Dict[str, Any]
    analysis_result: str
    analysis_success: bool
    final_response: str
    error_message: str
    walker_strategy: Dict[str, Any]
    execution_plan: List[Dict[str, Any]]
    execution_results: List[Dict[str, Any]]
    summary_result: Dict[str, Any]
    follow_up_questions: List[str]
    user_feedback: str
    continue_analysis: bool

class GraphBuilder:
    """状态图构建器类"""
    
    def __init__(self, intent_parser=None, summary_agent=None, mock_mode=False):
        """初始化构建器"""
        if not mock_mode:
            self.glm_client = get_glm_client()
        else:
            self.glm_client = None
        self.data_analyzer = DataAnalyzer()
        self.walker = get_walker()
        self.module_executor = get_module_executor()
        self.intent_parser = intent_parser or get_intent_parser()
        self.summary_agent = summary_agent or get_summary_agent()
        logger.info("状态图构建器初始化成功")
    
    def recognize_intent_node(self, state: WorkflowState) -> WorkflowState:
        """
        意图识别节点（使用新的IntentParser）
        
        Args:
            state: 当前状态
            
        Returns:
            更新后的状态
        """
        try:
            user_question = state["user_question"]
            
            # 使用新的意图解析器
            intent_result = self.intent_parser.parse_intent(user_question)
            
            logger.info(f"意图识别结果: {intent_result['intent']} (置信度: {intent_result['confidence']})")
            state["intent_result"] = intent_result
            
        except Exception as e:
            logger.error(f"意图识别失败: {e}")
            state["intent_result"] = {
                "intent": "general_chat",
                "confidence": 0.0,
                "reason": f"识别过程出错: {str(e)}",
                "need_data_analysis": False,
                "analysis_type": "none",
                "complexity": "simple"
            }
            state["error_message"] = str(e)
        
        return state
    
    def walker_strategy_node(self, state: WorkflowState) -> WorkflowState:
        """
        Walker策略生成节点
        
        Args:
            state: 当前状态
            
        Returns:
            更新后的状态
        """
        try:
            user_question = state["user_question"]
            intent_result = state["intent_result"]
            
            # 从意图解析器获取分析需求
            analysis_requirements = self.intent_parser.extract_analysis_requirements(intent_result)
            
            # 构建用户意图字典，用于复杂策略生成
            user_intent = {
                "action": "analyze",
                "target": intent_result.get("analysis_type", "data_description"),
                "parameters": {
                    "complexity": intent_result.get("complexity", "simple"),
                    "intent_type": intent_result.get("intent", "data_analysis"),
                    "target_fields": intent_result.get("target_fields", []),
                    "time_dimension": intent_result.get("time_dimension", ""),
                    "grouping_fields": intent_result.get("grouping_fields", []),
                    "comparison_type": intent_result.get("comparison_type", "")
                },
                "data_source": "auto_detect",
                "preferences": {
                    "include_visualization": True,
                    "detailed_analysis": intent_result.get("complexity", "simple") != "simple",
                    "keywords": intent_result.get("keywords", [])
                },
                "analysis_requirements": analysis_requirements  # 添加分析需求
            }
            
            logger.info(f"分析需求: {analysis_requirements}")
            
            # 使用walker生成复杂策略集
            strategies = self.walker.generate_strategies(
                user_intent=user_intent,
                max_strategies=5,
                min_compatibility_score=0.3
            )
            
            # 构建策略结果
            strategy_result = {
                "strategies": [{
                    "module_id": s.module_id,
                    "module_name": s.module_name,
                    "parameters": s.parameters,
                    "database_info": s.database_info,
                    "compatibility_score": s.compatibility_score,
                    "priority": s.priority,
                    "estimated_execution_time": s.estimated_execution_time
                } for s in strategies],
                "reasoning": f"为{intent_result.get('intent', 'data_analysis')}意图生成了{len(strategies)}个策略",
                "confidence": max([s.compatibility_score for s in strategies]) if strategies else 0.0,
                "user_intent": user_intent,
                "analysis_requirements": analysis_requirements,
                "strategy_objects": strategies  # 保留原始策略对象供后续使用
            }
            
            state["walker_strategy"] = strategy_result
            logger.info(f"Walker策略生成成功: 生成了{len(strategies)}个策略，最高置信度: {strategy_result['confidence']:.2f}")
            
        except Exception as e:
            logger.error(f"Walker策略生成失败: {e}")
            state["walker_strategy"] = {"error": str(e), "strategies": []}
            state["error_message"] = str(e)
        
        return state
    
    def execution_planning_node(self, state: WorkflowState) -> WorkflowState:
        """
        执行计划生成节点
        
        Args:
            state: 当前状态
            
        Returns:
            更新后的状态
        """
        try:
            walker_strategy = state["walker_strategy"]
            
            # 根据策略生成执行计划
            execution_plan = self.module_executor.create_execution_plan(walker_strategy)
            
            state["execution_plan"] = execution_plan
            logger.info(f"执行计划生成成功: {len(execution_plan)} 个步骤")
            
        except Exception as e:
            logger.error(f"执行计划生成失败: {e}")
            state["execution_plan"] = []
            state["error_message"] = str(e)
        
        return state
    
    def module_execution_node(self, state: WorkflowState) -> WorkflowState:
        """
        模块执行节点
        
        Args:
            state: 当前状态
            
        Returns:
            更新后的状态
        """
        try:
            execution_plan = state["execution_plan"]
            
            # 执行计划中的所有步骤
            execution_results = self.module_executor.execute_plan(execution_plan)
            
            state["execution_results"] = execution_results
            
            # 检查执行是否成功
            success = all(result.get("success", False) for result in execution_results)
            state["analysis_success"] = success
            
            # 合并所有执行结果
            combined_result = "\n".join(
                result.get("output", "") for result in execution_results
                if result.get("output")
            )
            state["analysis_result"] = combined_result
            
            logger.info(f"模块执行完成，成功: {success}")
            
        except Exception as e:
            logger.error(f"模块执行失败: {e}")
            state["analysis_success"] = False
            state["execution_results"] = []
            state["error_message"] = str(e)
        
        return state
    
    def data_analysis_node(self, state: WorkflowState) -> WorkflowState:
        """
        数据分析节点（保留原有功能作为备用）
        
        Args:
            state: 当前状态
            
        Returns:
            更新后的状态
        """
        try:
            from io import StringIO
            import sys
            
            # 捕获数据分析的输出
            old_stdout = sys.stdout
            sys.stdout = captured_output = StringIO()
            
            try:
                # 运行数据分析
                self.data_analyzer.analyze_all_data()
                analysis_result = captured_output.getvalue()
                
                if analysis_result.strip():
                    logger.info("数据分析执行成功")
                    state["analysis_success"] = True
                    state["analysis_result"] = analysis_result
                else:
                    state["analysis_success"] = False
                    state["error_message"] = "数据分析没有产生输出结果"
                    
            finally:
                sys.stdout = old_stdout
                
        except Exception as e:
            logger.error(f"数据分析执行失败: {e}")
            state["analysis_success"] = False
            state["error_message"] = f"数据分析执行出错: {str(e)}"
        
        return state
    
    def summary_generation_node(self, state: WorkflowState) -> WorkflowState:
        """
        综合总结生成节点
        
        Args:
            state: 当前状态
            
        Returns:
            更新后的状态
        """
        try:
            user_question = state["user_question"]
            intent_result = state["intent_result"]
            execution_results = state.get("execution_results", [])
            walker_strategy = state.get("walker_strategy", {})
            
            # 生成综合总结
            summary_result = self.summary_agent.generate_comprehensive_summary(
                user_question, intent_result, execution_results, walker_strategy
            )
            
            state["summary_result"] = summary_result
            
            # 生成后续问题建议
            follow_up_questions = self.summary_agent.generate_follow_up_questions(summary_result)
            state["follow_up_questions"] = follow_up_questions
            
            # 设置分析成功状态
            state["analysis_success"] = summary_result["execution_metadata"]["success_rate"] > 0
            state["analysis_result"] = summary_result["user_summary"]
            
            logger.info(f"综合总结生成成功，包含{len(summary_result['key_findings'])}个关键发现")
            
        except Exception as e:
            logger.error(f"综合总结生成失败: {e}")
            state["summary_result"] = {
                "user_summary": f"抱歉，生成总结时出现错误：{str(e)}",
                "key_findings": [],
                "follow_up_suggestions": []
            }
            state["follow_up_questions"] = []
            state["analysis_success"] = False
            state["error_message"] = str(e)
        
        return state
    
    def user_feedback_node(self, state: WorkflowState) -> WorkflowState:
        """
        用户反馈处理节点
        
        Args:
            state: 当前状态
            
        Returns:
            更新后的状态
        """
        try:
            user_feedback = state.get("user_feedback", "")
            
            # 分析用户反馈，判断是否需要继续分析
            continue_keywords = ["继续", "更多", "详细", "深入", "进一步", "continue", "more", "detail"]
            stop_keywords = ["结束", "停止", "够了", "谢谢", "end", "stop", "thanks"]
            
            user_feedback_lower = user_feedback.lower()
            
            if any(keyword in user_feedback_lower for keyword in continue_keywords):
                state["continue_analysis"] = True
                logger.info("用户选择继续分析")
            elif any(keyword in user_feedback_lower for keyword in stop_keywords):
                state["continue_analysis"] = False
                logger.info("用户选择结束分析")
            else:
                # 默认不继续，除非明确表示要继续
                state["continue_analysis"] = False
                logger.info("用户反馈不明确，默认结束分析")
            
        except Exception as e:
            logger.error(f"用户反馈处理失败: {e}")
            state["continue_analysis"] = False
            state["error_message"] = str(e)
        
        return state
    
    def response_generation_node(self, state: WorkflowState) -> WorkflowState:
        """
        响应生成节点
        
        Args:
            state: 当前状态
            
        Returns:
            更新后的状态
        """
        try:
            user_question = state["user_question"]
            intent_result = state["intent_result"]
            analysis_result = state.get("analysis_result")
            analysis_success = state.get("analysis_success", False)
            
            intent = intent_result.get("intent", "general_chat")
            
            if intent in ["data_query", "data_analysis"] and analysis_success and analysis_result:
                # 数据相关问题，使用分析结果生成回答
                prompt = DATA_ANALYSIS_EXPLANATION_PROMPT.format(
                    user_question=user_question,
                    analysis_result=analysis_result
                )
                response = self.glm_client.generate_response(prompt)
                
            elif intent in ["general_chat", "general_conversation"]:
                # 一般对话
                prompt = GENERAL_CHAT_PROMPT.format(user_question=user_question)
                response = self.glm_client.generate_response(prompt)
                
            else:
                # 其他情况或错误处理
                response = "抱歉，我无法理解您的问题。请尝试询问关于数据的问题，比如'你有什么数据'或'数据范围有哪些'。"
            
            state["final_response"] = response
            logger.info("响应生成成功")
            
        except Exception as e:
            logger.error(f"响应生成失败: {e}")
            error_prompt = ERROR_HANDLING_PROMPT.format(
                user_question=state["user_question"],
                error_message=str(e)
            )
            try:
                state["final_response"] = self.glm_client.generate_response(error_prompt)
            except:
                state["final_response"] = f"抱歉，处理您的请求时出现错误：{str(e)}"
            state["error_message"] = str(e)
        
        return state
    
    def should_use_walker(self, state: WorkflowState) -> str:
        """
        条件路由：判断是否使用Walker策略
        
        Args:
            state: 当前状态
            
        Returns:
            下一个节点名称
        """
        intent_result = state.get("intent_result", {})
        need_analysis = intent_result.get("need_data_analysis", False)
        intent = intent_result.get("intent", "general_chat")
        complexity = intent_result.get("complexity", "simple")
        
        # 对于需要数据分析的请求，使用Walker策略
        if need_analysis and intent in ["data_query", "data_analysis", "data_comparison", "data_segmentation"]:
            logger.info(f"使用Walker策略进行智能分析 (复杂度: {complexity})")
            return "walker_strategy"
        elif need_analysis:
            logger.info("使用传统数据分析")
            return "data_analysis"
        else:
            logger.info("跳过数据分析，直接生成响应")
            return "response_generation"
    
    def should_continue_analysis(self, state: WorkflowState) -> str:
        """
        条件路由：判断是否继续分析
        
        Args:
            state: 当前状态
            
        Returns:
            下一个节点名称
        """
        continue_analysis = state.get("continue_analysis", False)
        
        if continue_analysis:
            logger.info("用户选择继续分析，重新进入Walker策略")
            return "walker_strategy"
        else:
            logger.info("分析流程结束")
            return "END"
    
    def build_graph(self):
        """
        构建状态图
        
        Returns:
            构建好的状态图
        """
        try:
            from langgraph.graph import StateGraph, END
            
            # 创建状态图
            workflow = StateGraph(WorkflowState)
            
            # 添加节点
            workflow.add_node("intent_recognition", self.recognize_intent_node)
            workflow.add_node("walker_strategy", self.walker_strategy_node)
            workflow.add_node("execution_planning", self.execution_planning_node)
            workflow.add_node("module_execution", self.module_execution_node)
            workflow.add_node("data_analysis", self.data_analysis_node)
            workflow.add_node("summary_generation", self.summary_generation_node)
            workflow.add_node("user_feedback", self.user_feedback_node)
            workflow.add_node("response_generation", self.response_generation_node)
            
            # 设置入口点
            workflow.set_entry_point("intent_recognition")
            
            # 添加条件边
            workflow.add_conditional_edges(
                "intent_recognition",
                self.should_use_walker,
                {
                    "walker_strategy": "walker_strategy",
                    "data_analysis": "data_analysis",
                    "response_generation": "response_generation"
                }
            )
            
            # 添加Walker流程的边
            workflow.add_edge("walker_strategy", "execution_planning")
            workflow.add_edge("execution_planning", "module_execution")
            workflow.add_edge("module_execution", "summary_generation")
            
            # 添加传统流程的边
            workflow.add_edge("data_analysis", "response_generation")
            
            # 添加总结和反馈流程的边
            workflow.add_edge("summary_generation", "response_generation")
            workflow.add_edge("response_generation", "user_feedback")
            
            # 添加反馈循环的条件边
            workflow.add_conditional_edges(
                "user_feedback",
                self.should_continue_analysis,
                {
                    "walker_strategy": "walker_strategy",
                    "END": END
                }
            )
            
            # 编译图
            app = workflow.compile()
            logger.info("状态图构建成功")
            return app
            
        except ImportError:
            logger.warning("LangGraph 未安装，使用简化版本")
            return None
        except Exception as e:
            logger.error(f"状态图构建失败: {e}")
            return None

# 全局图构建器实例
_graph_builder = None

def get_graph_builder() -> GraphBuilder:
    """
    获取全局图构建器实例
    
    Returns:
        图构建器实例
    """
    global _graph_builder
    if _graph_builder is None:
        _graph_builder = GraphBuilder()
    return _graph_builder

if __name__ == "__main__":
    # 简单测试
    builder = GraphBuilder()
    graph = builder.build_graph()
    if graph:
        print("✅ 状态图构建成功")
    else:
        print("⚠️ 状态图构建失败，可能缺少 LangGraph 依赖")