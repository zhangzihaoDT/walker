#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
汽车行业智能分析系统
使用LangGraph工作流和GLM模型对业务指标进行专业分析
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 导入项目模块
from llm.glm import get_glm_client
from langgraph.graph import StateGraph
from typing_extensions import Annotated, TypedDict

class AnalysisState(TypedDict):
    """分析状态定义"""
    raw_data: str  # 原始分析数据
    module_results: Dict[str, Any]  # 各模块分析结果
    current_module: str  # 当前分析模块
    analysis_reports: Dict[str, str]  # 生成的分析报告
    errors: List[str]  # 错误信息

class AutomotiveAnalyst:
    """汽车行业分析师"""
    
    def __init__(self):
        """初始化分析师"""
        self.glm_client = get_glm_client("flash")
        self.workflow = self._create_workflow()
        
    def _create_workflow(self) -> StateGraph:
        """创建LangGraph工作流"""
        workflow = StateGraph(AnalysisState)
        
        # 添加节点
        workflow.add_node("extract_data", self._extract_business_data)
        workflow.add_node("analyze_module4", self._analyze_module4)
        workflow.add_node("generate_report", self._generate_final_report)
        
        # 设置边
        workflow.set_entry_point("extract_data")
        workflow.add_edge("extract_data", "analyze_module4")
        workflow.add_edge("analyze_module4", "generate_report")
        workflow.set_finish_point("generate_report")
        
        return workflow.compile()
    
    def _extract_business_data(self, state: AnalysisState) -> AnalysisState:
        """提取业务数据"""
        try:
            # 运行业务指标分析脚本
            script_path = project_root / "tasks" / "analyze_business_metrics.py"
            
            if not script_path.exists():
                state["errors"].append(f"分析脚本不存在: {script_path}")
                return state
            
            # 执行脚本并捕获输出
            result = subprocess.run(
                [sys.executable, str(script_path)],
                cwd=str(script_path.parent),
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            
            if result.returncode == 0:
                state["raw_data"] = result.stdout
                print("✅ 业务数据提取成功")
            else:
                error_msg = f"脚本执行失败: {result.stderr}"
                state["errors"].append(error_msg)
                print(f"❌ {error_msg}")
                
        except Exception as e:
            error_msg = f"数据提取异常: {str(e)}"
            state["errors"].append(error_msg)
            print(f"❌ {error_msg}")
            
        return state
    
    def _analyze_module4(self, state: AnalysisState) -> AnalysisState:
        """分析模块4：预售发布会后3日指标横向对比"""
        try:
            # 提取模块4相关数据
            raw_data = state.get("raw_data", "")
            module4_data = self._extract_module4_data(raw_data)
            
            if not module4_data:
                state["errors"].append("未找到模块4相关数据")
                return state
            
            # 构建分析提示词
            prompt = self._build_module4_prompt(module4_data)
            
            # 调用GLM进行分析
            analysis_result = self.glm_client.generate_response(prompt)
            
            # 保存分析结果
            state["module_results"]["module4"] = {
                "raw_data": module4_data,
                "analysis": analysis_result,
                "timestamp": datetime.now().isoformat()
            }
            
            state["current_module"] = "module4"
            print("✅ 模块4分析完成")
            
        except Exception as e:
            error_msg = f"模块4分析异常: {str(e)}"
            state["errors"].append(error_msg)
            print(f"❌ {error_msg}")
            
        return state
    
    def _extract_module4_data(self, raw_data: str) -> str:
        """提取模块4相关数据"""
        lines = raw_data.split('\n')
        module4_lines = []
        in_module4 = False
        
        for line in lines:
            # 检测模块4开始
            if "预售发布会后3日指标横向对比分析" in line or "Module 4" in line:
                in_module4 = True
                module4_lines.append(line)
            elif in_module4:
                # 检测模块结束
                if line.startswith("="*40) and len(module4_lines) > 10:
                    # 如果下一行是新模块的开始，则结束当前模块
                    break
                module4_lines.append(line)
        
        return '\n'.join(module4_lines)
    
    def _build_module4_prompt(self, module4_data: str) -> str:
        """构建模块4分析提示词"""
        prompt = f"""
你是一位资深的汽车行业数据分析师，专门负责预售发布会效果评估和竞品对比分析。

请基于以下预售发布会后3日指标数据，从汽车行业专业角度进行深度分析：

=== 原始数据 ===
{module4_data}

=== 分析要求 ===
请从以下几个维度进行专业分析：

1. **预售效果评估**
   - 各车型预售发布会的市场反响对比
   - 关键指标表现的优劣势分析
   - 预售策略的有效性评估

2. **竞品对比分析**
   - CM2与其他车型的竞争优势
   - 市场定位和目标客群差异
   - 营销策略的差异化分析

3. **市场洞察**
   - 消费者行为趋势分析
   - 市场接受度和品牌认知度
   - 潜在的市场机会和风险

4. **策略建议**
   - 基于数据的营销优化建议
   - 产品定位和推广策略调整
   - 后续发布会的改进方向

请用专业、客观的语言进行分析，提供具体的数据支撑和可操作的建议。
分析报告应该结构清晰，逻辑严谨，适合向高级管理层汇报。
"""
        return prompt
    
    def _generate_final_report(self, state: AnalysisState) -> AnalysisState:
        """生成最终报告"""
        try:
            module4_result = state["module_results"].get("module4", {})
            
            if not module4_result:
                state["errors"].append("没有模块4分析结果")
                return state
            
            # 生成报告
            report_content = self._format_module4_report(module4_result)
            
            # 保存报告
            report_path = project_root / "tasks" / "automotive_analysis_report_module4.md"
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            state["analysis_reports"]["module4"] = str(report_path)
            print(f"✅ 模块4报告已生成: {report_path}")
            
        except Exception as e:
            error_msg = f"报告生成异常: {str(e)}"
            state["errors"].append(error_msg)
            print(f"❌ {error_msg}")
            
        return state
    
    def _format_module4_report(self, module4_result: Dict[str, Any]) -> str:
        """格式化模块4报告"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        report = f"""
# 汽车行业预售发布会效果分析报告 - 模块4

**生成时间**: {timestamp}
**分析模块**: 预售发布会后3日指标横向对比分析
**分析师视角**: 汽车行业数据分析专家

---

## 原始数据概览

```
{module4_result.get('raw_data', '数据缺失')[:1000]}...
```

---

## 专业分析报告

{module4_result.get('analysis', '分析结果缺失')}

---

## 报告说明

- **数据来源**: 业务日常指标数据分析系统
- **分析方法**: 基于GLM大语言模型的智能分析
- **分析时间**: {module4_result.get('timestamp', '未知')}
- **报告用途**: 为管理层决策提供数据支撑

---

*本报告由汽车行业智能分析系统自动生成*
"""
        return report
    
    def run_analysis(self) -> Dict[str, Any]:
        """运行完整分析流程"""
        print("🚗 启动汽车行业智能分析系统...")
        
        # 初始化状态
        initial_state = AnalysisState(
            raw_data="",
            module_results={},
            current_module="",
            analysis_reports={},
            errors=[]
        )
        
        # 运行工作流
        try:
            final_state = self.workflow.invoke(initial_state)
            
            # 输出结果摘要
            print("\n" + "="*60)
            print("📊 分析完成摘要")
            print("="*60)
            
            if final_state["errors"]:
                print("❌ 发现错误:")
                for error in final_state["errors"]:
                    print(f"   - {error}")
            
            if final_state["analysis_reports"]:
                print("✅ 生成的报告:")
                for module, path in final_state["analysis_reports"].items():
                    print(f"   - {module}: {path}")
            
            return final_state
            
        except Exception as e:
            print(f"❌ 工作流执行失败: {e}")
            return {"error": str(e)}

def main():
    """主函数"""
    try:
        # 创建分析师实例
        analyst = AutomotiveAnalyst()
        
        # 运行分析
        result = analyst.run_analysis()
        
        # 检查结果
        if "error" in result:
            print(f"\n❌ 分析失败: {result['error']}")
            return 1
        
        print("\n🎉 汽车行业智能分析完成！")
        return 0
        
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断分析")
        return 1
    except Exception as e:
        print(f"\n❌ 系统异常: {e}")
        return 1

if __name__ == "__main__":
    exit(main())