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
    DATA_ANALYSIS_EXPLANATION_PROMPT,
    GENERAL_CHAT_PROMPT,
    ERROR_HANDLING_PROMPT
)
from modules.run_data_describe import DataAnalyzer
from .walker import get_walker
from agents.module_executor import get_module_executor
from agents.intent_parser import get_intent_parser

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
    sql_result: str

class GraphBuilder:
    """状态图构建器类"""
    
    def __init__(self):
        """初始化构建器"""
        self.glm_client = get_glm_client()
        self.data_analyzer = DataAnalyzer()
        self.walker = get_walker()
        self.module_executor = get_module_executor()
        self.intent_parser = get_intent_parser()
        logger.info("状态图构建器初始化成功")
    
    def recognize_intent_node(self, state: WorkflowState) -> WorkflowState:
        """
        意图识别节点
        
        Args:
            state: 当前状态
            
        Returns:
            更新后的状态
        """
        return self.intent_parser.create_intent_node(state)
    
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
    
    def sql_agent_node(self, state: WorkflowState) -> WorkflowState:
        """
        SQL Agent节点 - 智能路由到不同业务模块
        根据业务维度自动选择合适的模块处理查询
        
        Args:
            state: 当前状态
            
        Returns:
            更新后的状态
        """
        try:
            user_question = state["user_question"]
            logger.info(f"SQL Agent智能路由查询: {user_question}")
            
            # 业务维度识别和模块路由
            module_info = self._identify_business_module(user_question)
            module_name = module_info['module']
            module_params = module_info['params']
            
            logger.info(f"路由到模块: {module_name}")
            
            if module_name == 'sales_query':
                # 销量查询模块
                result = self._execute_sales_query(user_question, module_params)
            elif module_name == 'data_describe':
                # 数据描述模块
                result = self._execute_data_describe(user_question, module_params)
            else:
                # 通用查询处理
                result = self._execute_general_query(user_question)
            
            # 统一处理执行结果
            self._process_query_result(state, result, module_name)
            
        except Exception as e:
            logger.error(f"SQL Agent查询失败: {e}")
            state["analysis_success"] = False
            state["error_message"] = f"SQL查询执行出错: {str(e)}"
            state["sql_result"] = f"查询执行失败：{str(e)}"
        
        return state
    
    def _identify_business_module(self, user_question: str) -> Dict[str, Any]:
        """
        识别业务维度并选择合适的模块
        
        Args:
            user_question: 用户问题
            
        Returns:
            包含模块名称和参数的字典
        """
        # 销量相关关键词
        sales_keywords = ['销量', '销售', '上险', '品牌', '车型', '地区', '省份', '城市', '燃料', '电动', '混动', '排量', '厂商']
        
        # 数据描述相关关键词
        describe_keywords = ['数据概览', '数据结构', '字段', '列名', '数据类型', '数据范围', '有什么数据']
        
        # 检查销量查询
        if any(keyword in user_question for keyword in sales_keywords):
            return {
                'module': 'sales_query',
                'params': {
                    'module_id': 'sales_query',
                    'data_source': 'data/乘用车上险量_0723.parquet',
                    'user_question': user_question
                }
            }
        
        # 检查数据描述查询
        elif any(keyword in user_question for keyword in describe_keywords):
            return {
                'module': 'data_describe',
                'params': {
                    'module_id': 'data_describe',
                    'data_source': 'data/乘用车上险量_0723.parquet',
                    'user_question': user_question
                }
            }
        
        # 默认通用查询
        else:
            return {
                'module': 'general',
                'params': {'user_question': user_question}
            }
    
    def _execute_sales_query(self, user_question: str, module_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行销量查询模块
        
        Args:
            user_question: 用户问题
            module_params: 模块参数
            
        Returns:
            执行结果
        """
        try:
            logger.info("执行销量查询模块")
            module_executor = get_module_executor()
            
            # 加载销量查询模块配置
            module_config = self._load_module_config('sales_query')
            if not module_config:
                return {'success': False, 'error': '无法加载销量查询模块配置'}
            
            result = module_executor.execute_module(
                module_id='sales_query',
                parameters=module_params,
                module_config=module_config
            )
            return result
        except Exception as e:
            logger.error(f"销量查询模块执行失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def _load_module_config(self, module_id: str) -> Dict[str, Any]:
        """
        加载模块配置
        
        Args:
            module_id: 模块ID
            
        Returns:
            模块配置字典或None
        """
        try:
            import json
            config_file = project_root / "modules" / "analysis_config.json"
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            for module in config['modules']:
                if module['module_id'] == module_id:
                    return module
            
            logger.error(f"未找到模块配置: {module_id}")
            return None
            
        except Exception as e:
            logger.error(f"加载模块配置失败: {e}")
            return None
    
    def _execute_data_describe(self, user_question: str, module_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行数据描述模块
        
        Args:
            user_question: 用户问题
            module_params: 模块参数
            
        Returns:
            执行结果
        """
        try:
            logger.info("执行数据描述模块")
            # 使用DataAnalyzer进行数据描述
            analyzer = DataAnalyzer()
            result = analyzer.analyze_data(module_params.get('data_source', ''))
            return {'success': True, 'data': result, 'summary': '数据描述完成'}
        except Exception as e:
            logger.error(f"数据描述模块执行失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def _execute_general_query(self, user_question: str) -> Dict[str, Any]:
        """
        执行通用查询处理
        
        Args:
            user_question: 用户问题
            
        Returns:
            执行结果
        """
        logger.info("执行通用查询处理")
        result_text = f"通用查询结果：针对问题'{user_question}'的查询已处理。\n\n注意：当前主要支持销量相关查询，如需其他类型的数据分析，请使用数据分析功能。"
        return {
            'success': True,
            'data': [],
            'summary': result_text
        }
    
    def _process_query_result(self, state: WorkflowState, result: Dict[str, Any], module_name: str) -> None:
        """
        统一处理查询结果
        
        Args:
            state: 工作流状态
            result: 查询结果
            module_name: 模块名称
        """
        if result.get('success', False):
            # 格式化查询结果
            data = result.get('data', [])
            summary = result.get('summary', '')
            
            if data and isinstance(data, list) and len(data) > 0:
                # 构建结构化的查询结果
                query_result = {
                    'type': module_name,
                    'data': data,
                    'summary': summary,
                    'total_records': len(data),
                    'analysis': result.get('analysis', {}),
                    'insights': result.get('insights', [])
                }
                
                # 生成简洁的文本结果用于响应生成
                if len(data) <= 5:
                    # 数据量少，显示详细结果
                    text_result = f"{summary}\n\n详细数据：\n"
                    for i, record in enumerate(data, 1):
                        text_result += f"{i}. {record}\n"
                else:
                    # 数据量多，只显示摘要和前几条
                    text_result = f"{summary}\n\n前5条数据：\n"
                    for i, record in enumerate(data[:5], 1):
                        text_result += f"{i}. {record}\n"
                    text_result += f"\n... 共{len(data)}条记录"
                
                state["sql_result"] = text_result
                state["analysis_result"] = str(query_result)  # 保存完整结果
                state["analysis_success"] = True
                
                # 设置execution_results字段供测试框架使用
                state["execution_results"] = [{
                    'success': True,
                    'module': module_name,
                    'data': data,
                    'summary': summary,
                    'total_records': len(data),
                    'analysis': result.get('analysis', {}),
                    'insights': result.get('insights', []),
                    'visualization': result.get('visualization', {})
                }]
                
                logger.info(f"{module_name}查询执行成功，返回{len(data)}条记录")
            else:
                # 无数据或只有摘要
                state["sql_result"] = summary or "查询完成，但未找到符合条件的数据。"
                state["analysis_success"] = True
                
                # 设置execution_results字段供测试框架使用
                state["execution_results"] = [{
                    'success': True,
                    'module': module_name,
                    'data': [],
                    'summary': summary or "查询完成，但未找到符合条件的数据。",
                    'total_records': 0,
                    'analysis': result.get('analysis', {}),
                    'insights': result.get('insights', []),
                    'visualization': result.get('visualization', {})
                }]
                
                logger.info(f"{module_name}查询执行成功，但无数据返回")
        else:
            # 执行失败
            error_msg = result.get('error', '未知错误')
            state["sql_result"] = f"{module_name}查询执行失败：{error_msg}"
            state["analysis_success"] = False
            state["error_message"] = f"{module_name}模块执行失败: {error_msg}"
            
            # 设置execution_results字段供测试框架使用
            state["execution_results"] = [{
                'success': False,
                'module': module_name,
                'error': error_msg,
                'data': [],
                'total_records': 0,
                'analysis': result.get('analysis', {}),
                'insights': result.get('insights', []),
                'visualization': result.get('visualization', {})
            }]
            
            logger.error(f"{module_name}模块执行失败: {error_msg}")

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
            
            if intent == "data_analysis" and analysis_success and analysis_result:
                # 数据相关问题，使用分析结果生成回答
                prompt = DATA_ANALYSIS_EXPLANATION_PROMPT.format(
                    user_question=user_question,
                    analysis_result=analysis_result
                )
                response = self.glm_client.generate_response(prompt)
                
            elif intent == "query_only":
                # 直接查询类型，使用SQL查询结果
                sql_result = state.get("sql_result", "")
                if sql_result:
                    response = sql_result
                else:
                    response = "抱歉，查询未返回结果。请检查您的查询条件。"
                
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
        条件路由：判断使用哪种处理策略
        
        Args:
            state: 当前状态
            
        Returns:
            下一个节点名称
        """
        intent_result = state.get("intent_result", {})
        need_analysis = intent_result.get("need_data_analysis", False)
        intent = intent_result.get("intent", "general_chat")
        
        # 对于直接查询类型，使用SQL Agent
        if intent == "query_only":
            logger.info("使用SQL Agent进行直接查询")
            return "sql_agent"
        # 对于数据分析类型，使用Walker策略
        elif intent == "data_analysis":
            logger.info("使用Walker策略进行智能分析")
            return "walker_strategy"
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
            workflow.add_node("sql_agent", self.sql_agent_node)
            workflow.add_node("response_generation", self.response_generation_node)
            
            # 设置入口点
            workflow.set_entry_point("intent_recognition")
            
            # 添加条件边
            workflow.add_conditional_edges(
                "intent_recognition",
                self.should_use_walker,
                {
                    "walker_strategy": "walker_strategy",
                    "sql_agent": "sql_agent",
                    "response_generation": "response_generation"
                }
            )
            
            # 添加Walker流程的边
            workflow.add_edge("walker_strategy", "execution_planning")
            workflow.add_edge("execution_planning", "module_execution")
            workflow.add_edge("module_execution", "response_generation")
            
            # 添加SQL Agent流程的边
            workflow.add_edge("sql_agent", "response_generation")
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