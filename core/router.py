# -*- coding: utf-8 -*-
"""
系统主控路由器 - 接收输入、构造状态上下文，调用 LangGraph 执行
"""

import logging
from typing import Dict, Any
from pathlib import Path
import sys
import traceback

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.graph_builder import get_graph_builder, WorkflowState

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataChatRouter:
    """数据聊天路由器类 - 系统主控入口"""
    
    def __init__(self):
        """
        初始化路由器
        """
        self.graph_builder = get_graph_builder()
        self.workflow_graph = self.graph_builder.build_graph()
        logger.info("数据聊天路由器初始化成功")
    
    def create_initial_state(self, user_question: str) -> WorkflowState:
        """
        创建初始状态上下文
        
        Args:
            user_question: 用户问题
            
        Returns:
            初始化的工作流状态
        """
        return WorkflowState(
            user_question=user_question,
            intent_result={},
            analysis_result="",
            analysis_success=False,
            final_response="",
            error_message=""
        )
    
    def execute_with_langgraph(self, user_question: str) -> Dict[str, Any]:
        """
        使用 LangGraph 执行工作流
        
        Args:
            user_question: 用户问题
            
        Returns:
            执行结果
        """
        try:
            if self.workflow_graph is None:
                raise Exception("工作流图未初始化，可能缺少 LangGraph 依赖")
            
            # 创建初始状态
            initial_state = self.create_initial_state(user_question)
            
            # 执行工作流
            logger.info(f"开始执行 LangGraph 工作流: {user_question}")
            final_state = self.workflow_graph.invoke(initial_state)
            
            # 构建返回结果
            result = {
                "user_question": user_question,
                "intent": final_state.get("intent_result", {}),
                "data_analysis": {
                    "executed": final_state.get("intent_result", {}).get("need_data_analysis", False),
                    "success": final_state.get("analysis_success", False),
                    "result": final_state.get("analysis_result") if final_state.get("analysis_success") else None,
                    "error": final_state.get("error_message") if not final_state.get("analysis_success") else None
                },
                "final_response": final_state.get("final_response", ""),
                "timestamp": str(Path(__file__).stat().st_mtime),
                "execution_mode": "langgraph"
            }
            
            logger.info("LangGraph 工作流执行完成")
            return result
            
        except Exception as e:
            logger.error(f"LangGraph 工作流执行失败: {e}")
            return {
                "user_question": user_question,
                "intent": {"intent": "error", "confidence": 0.0},
                "data_analysis": {
                    "executed": False,
                    "success": False,
                    "result": None,
                    "error": f"工作流执行失败: {str(e)}"
                },
                "final_response": f"抱歉，处理您的请求时出现错误：{str(e)}",
                "timestamp": str(Path(__file__).stat().st_mtime),
                "execution_mode": "error",
                "error": str(e)
            }
    
    def execute_fallback(self, user_question: str) -> Dict[str, Any]:
        """
        降级执行模式 - 当 LangGraph 不可用时使用
        
        Args:
            user_question: 用户问题
            
        Returns:
            执行结果
        """
        try:
            logger.info(f"使用降级模式处理用户问题: {user_question}")
            
            # 创建初始状态
            state = self.create_initial_state(user_question)
            
            # 手动执行各个步骤
            # 步骤1: 意图识别
            state = self.graph_builder.recognize_intent_node(state)
            
            # 步骤2: 条件判断是否需要数据分析
            next_step = self.graph_builder.should_analyze_data(state)
            
            # 步骤3: 数据分析（如果需要）
            if next_step == "data_analysis":
                state = self.graph_builder.data_analysis_node(state)
            
            # 步骤4: 响应生成
            state = self.graph_builder.response_generation_node(state)
            
            # 构建返回结果
            result = {
                "user_question": user_question,
                "intent": state.get("intent_result", {}),
                "data_analysis": {
                    "executed": state.get("intent_result", {}).get("need_data_analysis", False),
                    "success": state.get("analysis_success", False),
                    "result": state.get("analysis_result") if state.get("analysis_success") else None,
                    "error": state.get("error_message") if not state.get("analysis_success") else None
                },
                "final_response": state.get("final_response", ""),
                "timestamp": str(Path(__file__).stat().st_mtime),
                "execution_mode": "fallback"
            }
            
            logger.info("降级模式执行完成")
            return result
            
        except Exception as e:
            logger.error(f"降级模式执行失败: {e}")
            return {
                "user_question": user_question,
                "intent": {"intent": "error", "confidence": 0.0},
                "data_analysis": {
                    "executed": False,
                    "success": False,
                    "result": None,
                    "error": f"降级模式执行失败: {str(e)}"
                },
                "final_response": f"抱歉，处理您的请求时出现错误：{str(e)}",
                "timestamp": str(Path(__file__).stat().st_mtime),
                "execution_mode": "error",
                "error": str(e)
            }
    
    def process_user_question(self, user_question: str) -> Dict[str, Any]:
        """
        处理用户问题的完整流程 - 主入口方法
        
        Args:
            user_question: 用户问题
            
        Returns:
            包含处理结果的字典
        """
        logger.info(f"路由器开始处理用户问题: {user_question}")
        
        try:
            # 优先尝试使用 LangGraph
            if self.workflow_graph is not None:
                return self.execute_with_langgraph(user_question)
            else:
                logger.warning("LangGraph 不可用，使用降级模式")
                return self.execute_fallback(user_question)
                
        except Exception as e:
            logger.error(f"路由器处理失败: {e}")
            # 最后的降级尝试
            try:
                return self.execute_fallback(user_question)
            except Exception as fallback_error:
                logger.error(f"降级模式也失败: {fallback_error}")
                return {
                    "user_question": user_question,
                    "intent": {"intent": "error", "confidence": 0.0},
                    "data_analysis": {
                        "executed": False,
                        "success": False,
                        "result": None,
                        "error": f"所有执行模式都失败: {str(e)}, {str(fallback_error)}"
                    },
                    "final_response": "抱歉，系统暂时无法处理您的请求，请稍后再试。",
                    "timestamp": str(Path(__file__).stat().st_mtime),
                    "execution_mode": "critical_error",
                    "error": f"Critical failure: {str(e)}, {str(fallback_error)}"
                }

# 全局路由器实例
_router = None

def get_router() -> DataChatRouter:
    """
    获取全局路由器实例
    
    Returns:
        路由器实例
    """
    global _router
    if _router is None:
        _router = DataChatRouter()
    return _router

# 为了保持向后兼容性，提供旧的接口
def get_workflow():
    """
    向后兼容接口 - 返回路由器实例
    
    Returns:
        路由器实例（兼容旧的工作流接口）
    """
    return get_router()

class DataChatWorkflow:
    """
    向后兼容类 - 包装路由器以保持旧接口
    """
    
    def __init__(self):
        self.router = get_router()
    
    def process_user_question(self, user_question: str) -> Dict[str, Any]:
        """向后兼容的处理方法"""
        return self.router.process_user_question(user_question)
    
    def recognize_intent(self, user_question: str) -> Dict[str, Any]:
        """向后兼容的意图识别方法"""
        state = self.router.create_initial_state(user_question)
        state = self.router.graph_builder.recognize_intent_node(state)
        return state.get("intent_result", {})
    
    def run_data_analysis(self):
        """向后兼容的数据分析方法"""
        state = self.router.create_initial_state("")
        state = self.router.graph_builder.data_analysis_node(state)
        return state.get("analysis_success", False), state.get("analysis_result", "")
    
    def generate_response(self, user_question: str, intent_result: Dict[str, Any], analysis_result: str = None) -> str:
        """向后兼容的响应生成方法"""
        state = self.router.create_initial_state(user_question)
        state["intent_result"] = intent_result
        if analysis_result:
            state["analysis_result"] = analysis_result
            state["analysis_success"] = True
        state = self.router.graph_builder.response_generation_node(state)
        return state.get("final_response", "")

if __name__ == "__main__":
    # 简单测试
    router = DataChatRouter()
    print("✅ 路由器初始化成功")
    
    # 测试向后兼容性
    workflow = DataChatWorkflow()
    print("✅ 向后兼容接口测试成功")