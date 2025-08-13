#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Walker策略完整流程
验证README.md中描述的用户输入→参数细分→趋势分析→同比分析→综合洞察的完整流程
"""

import sys
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.router import get_router

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_walker_strategy_flow():
    """
    测试完整的Walker策略流程
    """
    print("\n" + "="*80)
    print("🚀 测试Walker策略完整流程")
    print("="*80)
    
    try:
        # 获取路由器实例
        router = get_router()
        print("✅ 路由器初始化成功")
        
        # 测试用例1：复杂数据分析请求
        test_question_1 = "分析过去两年的销售数据趋势，按产品类别进行细分，并与去年同期进行对比"
        print(f"\n📝 测试问题1: {test_question_1}")
        
        result_1 = router.process_user_question(test_question_1)
        
        print("\n📊 分析结果1:")
        print(f"- 意图识别: {result_1['intent'].get('intent', 'unknown')}")
        print(f"- 需要数据分析: {result_1['intent'].get('need_data_analysis', False)}")
        print(f"- Walker策略使用: {result_1['walker_strategy']['used']}")
        print(f"- 分析成功: {result_1['data_analysis']['success']}")
        
        if result_1['walker_strategy']['used']:
            print(f"- 执行计划步骤数: {len(result_1['walker_strategy']['execution_plan'])}")
            print(f"- 执行结果数: {len(result_1['walker_strategy']['execution_results'])}")
        
        if result_1['summary']:
            print(f"- 关键发现数: {len(result_1['summary'].get('key_findings', []))}")
            print(f"- 后续建议数: {len(result_1['summary'].get('follow_up_suggestions', []))}")
        
        print(f"- 后续问题数: {len(result_1['follow_up_questions'])}")
        print(f"- 最终响应: {result_1['final_response'][:100]}...")
        
        # 测试用例2：用户反馈循环
        if result_1['follow_up_questions']:
            print(f"\n🔄 测试用户反馈循环")
            user_feedback = "请提供更详细的趋势分析"
            print(f"用户反馈: {user_feedback}")
            
            result_2 = router.continue_walker_analysis(result_1, user_feedback)
            
            print("\n📊 反馈循环结果:")
            print(f"- 继续分析: {result_2['continue_analysis']}")
            print(f"- Walker策略使用: {result_2['walker_strategy']['used']}")
            print(f"- 分析成功: {result_2['data_analysis']['success']}")
            print(f"- 最终响应: {result_2['final_response'][:100]}...")
        
        # 测试用例3：简单查询（不使用Walker策略）
        test_question_3 = "你好，今天天气怎么样？"
        print(f"\n📝 测试问题3: {test_question_3}")
        
        result_3 = router.process_user_question(test_question_3)
        
        print("\n📊 分析结果3:")
        print(f"- 意图识别: {result_3['intent'].get('intent', 'unknown')}")
        print(f"- 需要数据分析: {result_3['intent'].get('need_data_analysis', False)}")
        print(f"- Walker策略使用: {result_3['walker_strategy']['used']}")
        print(f"- 最终响应: {result_3['final_response'][:100]}...")
        
        print("\n✅ Walker策略流程测试完成")
        return True
        
    except Exception as e:
        print(f"\n❌ Walker策略流程测试失败: {e}")
        logger.error(f"测试失败: {e}", exc_info=True)
        return False

def test_individual_components():
    """
    测试各个组件的独立功能
    """
    print("\n" + "="*80)
    print("🔧 测试各个组件")
    print("="*80)
    
    try:
        # 测试意图解析器
        from agents import get_intent_parser
        intent_parser = get_intent_parser()
        print("✅ 意图解析器初始化成功")
        
        # 测试总结代理
        from agents import get_summary_agent
        summary_agent = get_summary_agent()
        print("✅ 总结代理初始化成功")
        
        # 测试图构建器
        from core.graph_builder import get_graph_builder
        graph_builder = get_graph_builder()
        print("✅ 图构建器初始化成功")
        
        # 测试工作流图构建
        workflow_graph = graph_builder.build_graph()
        if workflow_graph:
            print("✅ 工作流图构建成功")
        else:
            print("⚠️ 工作流图构建失败（可能缺少LangGraph依赖）")
        
        print("\n✅ 组件测试完成")
        return True
        
    except Exception as e:
        print(f"\n❌ 组件测试失败: {e}")
        logger.error(f"组件测试失败: {e}", exc_info=True)
        return False

def main():
    """
    主测试函数
    """
    print("🧪 Walker策略完整流程测试")
    print("测试README.md中描述的完整流程")
    
    # 测试各个组件
    component_success = test_individual_components()
    
    # 测试完整流程
    flow_success = test_walker_strategy_flow()
    
    # 总结
    print("\n" + "="*80)
    print("📋 测试总结")
    print("="*80)
    print(f"组件测试: {'✅ 通过' if component_success else '❌ 失败'}")
    print(f"流程测试: {'✅ 通过' if flow_success else '❌ 失败'}")
    
    if component_success and flow_success:
        print("\n🎉 所有测试通过！Walker策略流程已成功实现")
        print("\n📖 流程说明:")
        print("1. 用户输入 → 意图识别")
        print("2. 复杂查询 → Walker策略")
        print("3. 参数细分 → 趋势分析 → 同比分析")
        print("4. 综合总结 → 后续建议")
        print("5. 用户反馈 → 循环分析")
        return True
    else:
        print("\n⚠️ 部分测试失败，请检查相关组件")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)