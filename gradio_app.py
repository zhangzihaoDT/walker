#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gradio聊天应用 - 数据分析助手
"""

import os
import sys
import gradio as gr
import logging
from pathlib import Path
from typing import List, Tuple
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# LangSmith监控配置
if os.getenv('ENABLE_LANGSMITH', '').lower() == 'true':
    try:
        from langsmith import Client
        from langsmith.wrappers import wrap_openai
        
        # 配置LangSmith
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_PROJECT"] = "W33_DataChat_Assistant"
        os.environ["LANGCHAIN_API_KEY"] = os.getenv('LangSmith_API_KEY')
        
        langsmith_client = Client()
        print("✅ LangSmith监控已启用")
        LANGSMITH_ENABLED = True
    except ImportError:
        print("⚠️ LangSmith库未安装，跳过监控功能")
        LANGSMITH_ENABLED = False
    except Exception as e:
        print(f"⚠️ LangSmith配置失败: {e}")
        LANGSMITH_ENABLED = False
else:
    LANGSMITH_ENABLED = False
    print("ℹ️ LangSmith监控未启用")

from core.router import get_workflow

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataChatApp:
    """数据聊天应用类"""
    
    def __init__(self):
        """
        初始化应用
        """
        self.workflow = get_workflow()
        self.chat_history = []
        logger.info("数据聊天应用初始化成功")
    
    def process_message(self, message: str, history: List[List[str]]) -> Tuple[str, List[List[str]]]:
        """
        处理用户消息
        
        Args:
            message: 用户输入的消息
            history: 聊天历史
            
        Returns:
            (空字符串, 更新后的聊天历史)
        """
        if not message.strip():
            return "", history
        
        try:
            # 使用LangSmith监控（如果启用）
            if LANGSMITH_ENABLED:
                try:
                    # 创建trace记录
                    trace_data = {
                        "name": "data_chat_interaction",
                        "inputs": {"user_message": message},
                        "project_name": "W33_DataChat_Assistant"
                    }
                    
                    result = self.workflow.process_user_question(message)
                    
                    # 记录输出和元数据
                    trace_data["outputs"] = {"response": result["final_response"]}
                    trace_data["metadata"] = {
                        "intent": result["intent"]["intent"],
                        "confidence": result["intent"]["confidence"],
                        "data_analysis_executed": result["data_analysis"]["executed"]
                    }
                    
                    # 发送到LangSmith（简化版本）
                    logger.info(f"LangSmith trace: {trace_data['name']}")
                    
                except Exception as langsmith_error:
                    logger.warning(f"LangSmith监控失败: {langsmith_error}")
                    result = self.workflow.process_user_question(message)
            else:
                result = self.workflow.process_user_question(message)
            
            response = result["final_response"]
            
            # 更新聊天历史
            history.append([message, response])
            
            logger.info(f"处理消息成功: {message[:50]}...")
            return "", history
            
        except Exception as e:
            error_msg = f"抱歉，处理您的消息时出现错误：{str(e)}"
            history.append([message, error_msg])
            logger.error(f"处理消息失败: {e}")
            return "", history
    
    def clear_chat(self) -> List[List[str]]:
        """
        清空聊天记录
        
        Returns:
            空的聊天历史
        """
        self.chat_history = []
        logger.info("聊天记录已清空")
        return []
    
    def get_example_questions(self) -> List[str]:
        """
        获取示例问题
        
        Returns:
            示例问题列表
        """
        return [
            "你好，请介绍一下你自己",
            "你有什么数据？",
            "数据范围有哪些？",
            "请分析一下数据的基本情况",
            "数据质量如何？",
            "有多少条记录？",
            "数据包含哪些字段？"
        ]
    
    def _get_system_status(self) -> str:
        """
        获取系统状态
        
        Returns:
            系统状态信息
        """
        status = []
        status.append(f"🔧 系统版本: {os.getenv('APP_VERSION', '0.1.0')}")
        status.append(f"🤖 LLM模型: GLM (智谱AI)")
        
        # 检查数据目录
        data_dir = Path("data")
        if data_dir.exists():
            data_files = list(data_dir.glob("*.csv")) + list(data_dir.glob("*.parquet"))
            status.append(f"📊 数据文件: {len(data_files)}个文件")
        else:
            status.append("📊 数据文件: 未配置")
        
        # 检查工作流状态
        try:
            if hasattr(self, 'workflow') and self.workflow:
                status.append("📋 工作流: 已初始化")
            else:
                status.append("📋 工作流: 未初始化")
        except:
            status.append("📋 工作流: 状态未知")
        
        status.append(f"🔍 LangSmith监控: {'启用' if LANGSMITH_ENABLED else '禁用'}")
        status.append(f"🌐 服务状态: 正常运行")
        
        return "\n".join(status)
    
    def create_interface(self) -> gr.Blocks:
        """
        创建Gradio界面
        
        Returns:
            Gradio Blocks界面
        """
        with gr.Blocks(
            title="数据分析助手",
            theme=gr.themes.Soft(),
            css="""
            .gradio-container {
                width: 1200px !important;
                max-width: 1600px !important;
                margin: auto !important;
            }
            .chat-message {
                padding: 10px;
                margin: 5px 0;
                border-radius: 10px;
            }
            """
        ) as interface:
            
            # 标题和描述
            gr.Markdown(
                """
                # 🚗 汽车数据智能分析系统
                
                """
            )
            
            # 聊天界面 - 上半部分
            chatbot = gr.Chatbot(
                label="对话记录",
                height=450,
                show_label=True,
                container=True,
                bubble_full_width=False
            )
            
            # 输入区域
            with gr.Row():
                msg_input = gr.Textbox(
                    label="输入消息",
                    placeholder="请输入您的问题...",
                    scale=4,
                    container=False
                )
                send_btn = gr.Button(
                    "发送",
                    variant="primary",
                    scale=1
                )
                clear_btn = gr.Button(
                    "清空对话",
                    variant="secondary",
                    scale=1
                )
            
            # 示例问题区域
            with gr.Accordion("💡 示例问题", open=True):
                gr.Examples(
                    examples=[
                        "你好，请介绍一下你自己",
                        "你知道的数据范围有哪些",
                        "你有什么数据",
                        "请分析一下数据的基本情况",
                        "有多少条记录？",
                        "数据包含哪些字段？"
                    ],
                    inputs=msg_input,
                    label="点击使用示例问题"
                )
            
            # 系统状态 - 折叠组件
            with gr.Accordion("📋 系统信息", open=False):
                system_status = gr.Markdown(
                    value=self._get_system_status(),
                    every=5  # 每5秒更新一次
                )
            
            # 事件绑定
            msg_input.submit(
                self.process_message,
                inputs=[msg_input, chatbot],
                outputs=[msg_input, chatbot]
            )
            
            send_btn.click(
                self.process_message,
                inputs=[msg_input, chatbot],
                outputs=[msg_input, chatbot]
            )
            
            clear_btn.click(
                self.clear_chat,
                outputs=chatbot
            )
        
        return interface


def main():
    """
    主函数
    """
    try:
        # 创建应用实例
        app = DataChatApp()
        
        # 工作流已初始化
        
        print("✅ 应用初始化成功")
        
        # 创建界面
        interface = app.create_interface()
        
        # 启动服务
        server_name = os.getenv('GRADIO_SERVER_NAME', 'localhost')
        server_port = int(os.getenv('GRADIO_SERVER_PORT', 7860))
        share = os.getenv('GRADIO_SHARE', 'false').lower() == 'true'
        
        # 尝试启动服务，如果端口被占用则自动寻找可用端口
        max_attempts = 10
        for attempt in range(max_attempts):
            try:
                current_port = server_port + attempt
                logger.info(f"尝试启动服务: http://{server_name}:{current_port}")
                
                interface.launch(
                    server_name=server_name,
                    server_port=current_port,
                    share=share,
                    show_error=True,
                    quiet=False
                )
                break  # 成功启动，退出循环
            except OSError as e:
                if "Cannot find empty port" in str(e) and attempt < max_attempts - 1:
                    logger.warning(f"端口 {current_port} 被占用，尝试下一个端口...")
                    continue
                else:
                    logger.error(f"启动失败: {e}")
                    raise
        
    except KeyboardInterrupt:
        logger.info("用户中断，正在关闭服务...")
    except Exception as e:
        logger.error(f"启动失败: {e}")
        raise


if __name__ == "__main__":
    main()