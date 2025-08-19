#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
汽车行业智能分析系统 - Gradio前端界面
使用选项卡布局展示各模块分析结果
"""

import os
import sys
import gradio as gr
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Tuple

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 导入分析系统
from automotive_analysis_app import AutomotiveAnalyst

class AutomotiveAnalysisUI:
    """汽车行业分析系统UI"""
    
    def __init__(self):
        """初始化UI"""
        self.analyst = AutomotiveAnalyst()
        self.latest_results = {}
        
    def run_module4_analysis(self) -> Tuple[str, str, str]:
        """运行模块4分析"""
        try:
            # 运行分析
            results = self.analyst.run_analysis()
            self.latest_results = results
            
            if "error" in results:
                return "❌ 分析失败", f"错误信息: {results['error']}", ""
            
            # 获取模块4结果
            module4_result = results.get("module_results", {}).get("module4", {})
            
            if not module4_result:
                return "❌ 未找到模块4分析结果", "", ""
            
            # 格式化输出
            status = "✅ 模块4分析完成"
            
            # 原始数据表格
            raw_data = module4_result.get("raw_data", "")
            data_table = self._format_data_table(raw_data)
            
            # 分析报告
            analysis = module4_result.get("analysis", "")
            
            return status, data_table, analysis
            
        except Exception as e:
            return f"❌ 分析异常: {str(e)}", "", ""
    
    def _format_data_table(self, raw_data: str) -> str:
        """格式化数据表格"""
        if not raw_data:
            return "暂无数据"
        
        lines = raw_data.split('\n')
        formatted_lines = []
        
        for line in lines:
            if line.strip():
                # 简单格式化，保持原有结构
                formatted_lines.append(line)
        
        return '\n'.join(formatted_lines[:50])  # 限制显示行数
    
    def get_analysis_summary(self) -> str:
        """获取分析摘要"""
        if not self.latest_results:
            return "尚未运行分析"
        
        summary = []
        summary.append("## 📊 分析摘要")
        summary.append(f"**分析时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 错误信息
        errors = self.latest_results.get("errors", [])
        if errors:
            summary.append("\n### ❌ 错误信息")
            for error in errors:
                summary.append(f"- {error}")
        
        # 生成的报告
        reports = self.latest_results.get("analysis_reports", {})
        if reports:
            summary.append("\n### ✅ 生成的报告")
            for module, path in reports.items():
                summary.append(f"- **{module}**: {path}")
        
        # 模块结果统计
        module_results = self.latest_results.get("module_results", {})
        if module_results:
            summary.append("\n### 📈 分析模块")
            for module, result in module_results.items():
                timestamp = result.get("timestamp", "未知")
                summary.append(f"- **{module}**: 完成于 {timestamp}")
        
        return '\n'.join(summary)
    
    def create_interface(self) -> gr.Blocks:
        """创建Gradio界面"""
        with gr.Blocks(
            title="🚗 汽车行业智能分析系统",
            theme=gr.themes.Soft(),
            css="""
            .gradio-container {
                max-width: 1200px !important;
            }
            .tab-nav {
                background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            }
            """
        ) as interface:
            
            # 标题
            gr.Markdown(
                """
                # 🚗 汽车行业智能分析系统
                
                **基于LangGraph工作流和GLM大语言模型的专业汽车行业数据分析平台**
                
                ---
                """
            )
            
            with gr.Tabs() as tabs:
                
                # 模块4：预售发布会后3日指标横向对比分析
                with gr.Tab("📊 模块4 - 预售发布会分析", id="module4"):
                    gr.Markdown(
                        """
                        ## 预售发布会后3日指标横向对比分析
                        
                        **分析师视角**: 汽车行业数据分析专家  
                        **分析重点**: 预售效果评估、竞品对比、市场洞察、策略建议
                        """
                    )
                    
                    with gr.Row():
                        run_btn = gr.Button(
                            "🚀 运行模块4分析", 
                            variant="primary", 
                            size="lg"
                        )
                    
                    with gr.Row():
                        status_output = gr.Textbox(
                            label="分析状态",
                            interactive=False,
                            lines=2
                        )
                    
                    with gr.Row():
                        with gr.Column(scale=1):
                            gr.Markdown("### 📋 原始数据")
                            data_output = gr.Textbox(
                                label="数据表格",
                                interactive=False,
                                lines=15,
                                max_lines=20
                            )
                        
                        with gr.Column(scale=2):
                            gr.Markdown("### 🎯 专业分析报告")
                            analysis_output = gr.Textbox(
                                label="分析解读",
                                interactive=False,
                                lines=15,
                                max_lines=20
                            )
                    
                    # 绑定事件
                    run_btn.click(
                        fn=self.run_module4_analysis,
                        outputs=[status_output, data_output, analysis_output]
                    )
                
                # 系统概览
                with gr.Tab("📈 系统概览", id="overview"):
                    gr.Markdown(
                        """
                        ## 系统概览
                        
                        查看最新的分析结果摘要和系统状态
                        """
                    )
                    
                    with gr.Row():
                        refresh_btn = gr.Button(
                            "🔄 刷新概览", 
                            variant="secondary"
                        )
                    
                    with gr.Row():
                        summary_output = gr.Markdown(
                            value="点击刷新按钮查看分析摘要"
                        )
                    
                    # 绑定事件
                    refresh_btn.click(
                        fn=self.get_analysis_summary,
                        outputs=[summary_output]
                    )
                
                # 关于系统
                with gr.Tab("ℹ️ 关于系统", id="about"):
                    gr.Markdown(
                        """
                        ## 关于汽车行业智能分析系统
                        
                        ### 🎯 系统特点
                        - **专业分析**: 基于汽车行业专家视角的深度数据分析
                        - **智能工作流**: 使用LangGraph构建的自动化分析流程
                        - **AI驱动**: 集成GLM大语言模型进行智能解读
                        - **可视化展示**: 直观的数据表格和分析报告展示
                        
                        ### 📊 分析模块
                        - **模块4**: 预售发布会后3日指标横向对比分析
                        - **更多模块**: 正在开发中...
                        
                        ### 🔧 技术架构
                        - **前端**: Gradio Web界面
                        - **后端**: Python + LangGraph工作流
                        - **AI模型**: GLM大语言模型
                        - **数据处理**: Pandas + 自定义分析脚本
                        
                        ### 📝 使用说明
                        1. 选择对应的分析模块选项卡
                        2. 点击"运行分析"按钮启动分析流程
                        3. 查看生成的数据表格和专业分析报告
                        4. 在"系统概览"中查看分析摘要
                        
                        ---
                        
                        **版本**: v1.0.0  
                        **更新时间**: 2025-08-19  
                        **开发团队**: 汽车行业数据分析团队
                        """
                    )
            
            return interface
    
    def launch(self, **kwargs):
        """启动界面"""
        interface = self.create_interface()
        interface.launch(**kwargs)

def main():
    """主函数"""
    try:
        print("🚗 启动汽车行业智能分析系统 Web界面...")
        
        # 创建UI实例
        ui = AutomotiveAnalysisUI()
        
        # 启动界面
        ui.launch(
            server_name="0.0.0.0",
            server_port=7860,
            share=False,
            show_error=True,
            quiet=False
        )
        
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断服务")
    except Exception as e:
        print(f"\n❌ 启动失败: {e}")

if __name__ == "__main__":
    main()