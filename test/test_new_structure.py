#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试新的模块结构是否正常工作
"""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """测试模块导入"""
    print("🔍 测试模块导入...")
    
    try:
        from core.graph_builder import GraphBuilder, get_graph_builder, WorkflowState
        print("✅ graph_builder 模块导入成功")
    except Exception as e:
        print(f"❌ graph_builder 模块导入失败: {e}")
        return False
    
    try:
        from core.router import DataChatRouter, get_router, get_workflow, DataChatWorkflow
        print("✅ router 模块导入成功")
    except Exception as e:
        print(f"❌ router 模块导入失败: {e}")
        return False
    
    return True

@patch('core.graph_builder.get_glm_client')
@patch('modules.run_data_describe.DataAnalyzer')
def test_backward_compatibility(mock_analyzer, mock_glm):
    """测试向后兼容性"""
    print("\n🔍 测试向后兼容性...")
    
    try:
        # Mock GLM 客户端
        mock_glm_instance = MagicMock()
        mock_glm.return_value = mock_glm_instance
        
        # Mock 数据分析器
        mock_analyzer_instance = MagicMock()
        mock_analyzer.return_value = mock_analyzer_instance
        
        from core.router import get_workflow, DataChatWorkflow
        
        # 测试旧的接口是否还能工作
        workflow = get_workflow()
        print("✅ get_workflow() 函数正常工作")
        
        # 测试旧的类是否还能实例化
        old_workflow = DataChatWorkflow()
        print("✅ DataChatWorkflow 类正常工作")
        
        # 测试旧的方法是否存在
        if hasattr(old_workflow, 'process_user_question'):
            print("✅ process_user_question 方法存在")
        else:
            print("❌ process_user_question 方法不存在")
            return False
            
        if hasattr(old_workflow, 'recognize_intent'):
            print("✅ recognize_intent 方法存在")
        else:
            print("❌ recognize_intent 方法不存在")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ 向后兼容性测试失败: {e}")
        return False

@patch('core.graph_builder.get_glm_client')
@patch('modules.run_data_describe.DataAnalyzer')
def test_new_structure(mock_analyzer, mock_glm):
    """测试新的结构"""
    print("\n🔍 测试新的模块结构...")
    
    try:
        # Mock GLM 客户端
        mock_glm_instance = MagicMock()
        mock_glm.return_value = mock_glm_instance
        
        # Mock 数据分析器
        mock_analyzer_instance = MagicMock()
        mock_analyzer.return_value = mock_analyzer_instance
        
        from core.router import DataChatRouter
        from core.graph_builder import GraphBuilder, WorkflowState
        
        # 测试路由器
        router = DataChatRouter()
        print("✅ DataChatRouter 初始化成功")
        
        # 测试图构建器
        builder = GraphBuilder()
        print("✅ GraphBuilder 初始化成功")
        
        # 测试状态创建
        initial_state = router.create_initial_state("测试问题")
        if initial_state and 'user_question' in initial_state:
            print("✅ 状态创建功能正常")
        else:
            print("❌ 状态创建功能异常")
            return False
        
        # 测试状态类型
        if isinstance(initial_state, dict):
            print("✅ WorkflowState 类型正常")
        else:
            print("❌ WorkflowState 类型异常")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ 新结构测试失败: {e}")
        return False

def test_file_structure():
    """测试文件结构"""
    print("\n🔍 测试文件结构...")
    
    try:
        # 检查新文件是否存在
        graph_builder_path = project_root / "core" / "graph_builder.py"
        router_path = project_root / "core" / "router.py"
        old_workflow_path = project_root / "core" / "workflow.py"
        
        if graph_builder_path.exists():
            print("✅ core/graph_builder.py 文件存在")
        else:
            print("❌ core/graph_builder.py 文件不存在")
            return False
        
        if router_path.exists():
            print("✅ core/router.py 文件存在")
        else:
            print("❌ core/router.py 文件不存在")
            return False
        
        if not old_workflow_path.exists():
            print("✅ 旧的 core/workflow.py 文件已删除")
        else:
            print("❌ 旧的 core/workflow.py 文件仍然存在")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 文件结构测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始测试新的模块结构...\n")
    
    success = True
    
    # 测试导入
    if not test_imports():
        success = False
    
    # 测试文件结构
    if not test_file_structure():
        success = False
    
    # 测试向后兼容性
    if not test_backward_compatibility():
        success = False
    
    # 测试新结构
    if not test_new_structure():
        success = False
    
    print("\n" + "="*50)
    if success:
        print("🎉 所有测试通过！新的模块结构工作正常。")
        print("\n📋 拆分总结:")
        print("  ✅ core/workflow.py 已拆分为:")
        print("     - core/graph_builder.py: 负责构建状态图")
        print("     - core/router.py: 负责系统主控入口")
        print("  ✅ 系统引用已更新:")
        print("     - gradio_app.py: core.workflow → core.router")
        print("     - test/test_data_chat_system.py: core.workflow → core.router")
        print("  ✅ 向后兼容性保持良好")
        print("  ✅ 旧文件已删除")
        print("\n🔧 新架构特点:")
        print("  - 支持 LangGraph 状态图执行")
        print("  - 提供降级执行模式")
        print("  - 保持完整的向后兼容性")
    else:
        print("❌ 部分测试失败，请检查错误信息。")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)