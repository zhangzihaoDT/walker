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

class GraphBuilder:
    """状态图构建器类"""
    
    def __init__(self):
        """初始化构建器"""
        self.glm_client = get_glm_client()
        self.data_analyzer = DataAnalyzer()
        self.walker = get_walker()
        self.module_executor = get_module_executor()
        logger.info("状态图构建器初始化成功")
    
    def recognize_intent_node(self, state: WorkflowState) -> WorkflowState:
        """
        意图识别节点
        
        Args:
            state: 当前状态
            
        Returns:
            更新后的状态
        """
        try:
            user_question = state["user_question"]
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
            state["intent_result"] = result
            
        except Exception as e:
            logger.error(f"意图识别失败: {e}")
            state["intent_result"] = {
                "intent": "general_chat",
                "confidence": 0.0,
                "reason": f"识别过程出错: {str(e)}",
                "need_data_analysis": False
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
            
            # 使用walker生成策略
            strategy = self.walker.generate_strategy(
                question=user_question,
                intent=intent_result
            )
            
            state["walker_strategy"] = strategy
            logger.info(f"Walker策略生成成功: {strategy}")
            
        except Exception as e:
            logger.error(f"Walker策略生成失败: {e}")
            state["walker_strategy"] = {"error": str(e)}
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
                
            elif intent == "general_chat":
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
        
        # 对于复杂的数据查询和分析，使用Walker策略
        if need_analysis and intent in ["data_query", "data_analysis"]:
            logger.info("使用Walker策略进行智能分析")
            return "walker_strategy"
        elif need_analysis:
            logger.info("使用传统数据分析")
            return "data_analysis"
        else:
            logger.info("跳过数据分析，直接生成响应")
            return "response_generation"
    
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
            workflow.add_edge("module_execution", "response_generation")
            
            # 添加传统流程的边
            workflow.add_edge("data_analysis", "response_generation")
            workflow.add_edge("response_generation", END)
            
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