# 汽车行业智能分析系统工作流程图

## 系统架构概览

```mermaid
graph TB
    subgraph "前端界面层 (Gradio)"
        UI["🖥️ AutomotiveAnalysisUI"]
        TAB1["📊 模块4分析选项卡"]
        TAB2["📈 系统概览选项卡"]
        TAB3["ℹ️ 关于系统选项卡"]
        
        UI --> TAB1
        UI --> TAB2
        UI --> TAB3
    end
    
    subgraph "后端分析层 (LangGraph)"
        ANALYST["🚗 AutomotiveAnalyst"]
        WORKFLOW["📋 LangGraph工作流"]
        GLM["🤖 GLM客户端"]
        
        ANALYST --> WORKFLOW
        ANALYST --> GLM
    end
    
    subgraph "数据处理层"
        SCRIPT["📊 analyze_business_metrics.py"]
        DATA["📈 业务指标数据"]
        REPORT["📄 分析报告"]
        
        SCRIPT --> DATA
        DATA --> REPORT
    end
    
    TAB1 -.->|用户点击运行| ANALYST
    WORKFLOW -.->|调用脚本| SCRIPT
    GLM -.->|生成分析| REPORT
    ANALYST -.->|返回结果| TAB1
    TAB2 -.->|显示摘要| ANALYST
```

## LangGraph工作流详细流程

```mermaid
flowchart TD
    START(["🚀 开始分析"]) --> INIT["初始化AnalysisState"]
    
    INIT --> NODE1["📊 extract_data节点"]
    NODE1 --> SUBPROCESS["执行analyze_business_metrics.py"]
    SUBPROCESS --> CHECK1{"脚本执行成功?"}
    
    CHECK1 -->|是| SAVE_DATA["保存原始数据到state.raw_data"]
    CHECK1 -->|否| ERROR1["记录错误到state.errors"]
    
    SAVE_DATA --> NODE2["🔍 analyze_module4节点"]
    ERROR1 --> NODE2
    
    NODE2 --> EXTRACT["提取模块4相关数据"]
    EXTRACT --> CHECK2{"找到模块4数据?"}
    
    CHECK2 -->|是| BUILD_PROMPT["构建分析提示词"]
    CHECK2 -->|否| ERROR2["记录错误"]
    
    BUILD_PROMPT --> GLM_CALL["🤖 调用GLM进行分析"]
    GLM_CALL --> SAVE_RESULT["保存分析结果到state.module_results"]
    ERROR2 --> NODE3
    
    SAVE_RESULT --> NODE3["📝 generate_report节点"]
    NODE3 --> FORMAT["格式化模块4报告"]
    FORMAT --> WRITE_FILE["写入报告文件"]
    WRITE_FILE --> SAVE_PATH["保存报告路径到state.analysis_reports"]
    
    SAVE_PATH --> END(["✅ 分析完成"])
    
    style START fill:#e1f5fe
    style END fill:#e8f5e8
    style GLM_CALL fill:#fff3e0
    style ERROR1 fill:#ffebee
    style ERROR2 fill:#ffebee
```

## 数据流图

```mermaid
flowchart LR
    subgraph "输入数据"
        CSV["📊 CSV业务数据"]
        CONFIG["⚙️ 分析配置"]
    end
    
    subgraph "数据处理"
        SCRIPT["analyze_business_metrics.py"]
        EXTRACT["数据提取与清洗"]
        FILTER["模块4数据筛选"]
    end
    
    subgraph "AI分析"
        PROMPT["🎯 专业提示词构建"]
        GLM["🤖 GLM模型分析"]
        INSIGHT["💡 行业洞察生成"]
    end
    
    subgraph "输出结果"
        TABLE["📋 数据表格"]
        ANALYSIS["📄 分析报告"]
        SUMMARY["📊 结果摘要"]
    end
    
    CSV --> SCRIPT
    CONFIG --> SCRIPT
    SCRIPT --> EXTRACT
    EXTRACT --> FILTER
    
    FILTER --> PROMPT
    PROMPT --> GLM
    GLM --> INSIGHT
    
    FILTER --> TABLE
    INSIGHT --> ANALYSIS
    TABLE --> SUMMARY
    ANALYSIS --> SUMMARY
    
    style CSV fill:#e3f2fd
    style GLM fill:#fff8e1
    style ANALYSIS fill:#e8f5e8
```

## Gradio界面交互流程

```mermaid
sequenceDiagram
    participant User as 👤 用户
    participant UI as 🖥️ Gradio界面
    participant Backend as 🚗 AutomotiveAnalyst
    participant LG as 📋 LangGraph
    participant GLM as 🤖 GLM模型
    participant File as 📁 文件系统
    
    User->>UI: 点击\"运行模块4分析\"按钮
    UI->>Backend: 调用run_analysis()
    
    Backend->>LG: 启动工作流
    LG->>File: 执行analyze_business_metrics.py
    File-->>LG: 返回原始数据
    
    LG->>LG: 提取模块4数据
    LG->>GLM: 发送分析提示词
    GLM-->>LG: 返回分析结果
    
    LG->>File: 生成并保存报告
    File-->>LG: 确认保存成功
    
    LG-->>Backend: 返回完整结果
    Backend-->>UI: 返回(状态, 数据表格, 分析报告)
    
    UI-->>User: 显示分析结果
    
    Note over User,File: 整个流程约需30-60秒
```

## 状态管理图

```mermaid
stateDiagram-v2
    [*] --> 初始化
    
    初始化 --> 数据提取中
    数据提取中 --> 数据提取成功 : 脚本执行成功
    数据提取中 --> 数据提取失败 : 脚本执行失败
    
    数据提取成功 --> 模块4分析中
    数据提取失败 --> 模块4分析中
    
    模块4分析中 --> 分析成功 : 找到数据且GLM分析成功
    模块4分析中 --> 分析失败 : 未找到数据或GLM分析失败
    
    分析成功 --> 报告生成中
    分析失败 --> 报告生成中
    
    报告生成中 --> 完成 : 报告保存成功
    报告生成中 --> 完成 : 报告保存失败
    
    完成 --> [*]
    
    note right of 数据提取中
        执行subprocess调用
        analyze_business_metrics.py
    end note
    
    note right of 模块4分析中
        1. 提取模块4数据
        2. 构建专业提示词
        3. 调用GLM分析
    end note
    
    note right of 报告生成中
        格式化并保存
        Markdown报告文件
    end note
```

## 关键组件说明

### 1. AutomotiveAnalyst (核心分析引擎)
- **职责**: 协调整个分析流程
- **组件**: GLM客户端、LangGraph工作流
- **状态管理**: AnalysisState TypedDict

### 2. LangGraph工作流节点
- **extract_data**: 数据提取节点，执行业务指标分析脚本
- **analyze_module4**: 模块4分析节点，使用GLM进行专业分析
- **generate_report**: 报告生成节点，格式化并保存分析报告

### 3. AutomotiveAnalysisUI (前端界面)
- **职责**: 提供用户交互界面
- **布局**: 选项卡式界面（模块4分析、系统概览、关于系统）
- **交互**: 按钮点击触发分析，实时显示结果

### 4. 数据流转
1. **输入**: CSV业务数据 → analyze_business_metrics.py
2. **处理**: 原始数据 → 模块4数据筛选 → GLM分析
3. **输出**: 数据表格 + 专业分析报告 + Markdown文件

### 5. 错误处理
- 每个节点都有异常捕获机制
- 错误信息统一收集到state.errors
- 前端界面显示详细错误信息

---

*此图表展示了汽车行业智能分析系统的完整工作流程，包括前端交互、后端处理、AI分析和数据流转的全过程。*