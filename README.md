# W33_utils_3 项目架构

本项目 `W33_utils_3` 是一个工具库，主要包含以下模块和文件：

## 目录结构

- `.env`: 环境变量配置文件。
- `.gitignore`: Git 版本控制忽略文件。
- `README.md`: 项目说明文件。
- `agents/`: 可能包含各种智能代理或自动化脚本。
- `core/`: 核心功能模块，可能包含项目的基础类、函数或通用工具。
- `data/`: 数据存储目录，可能包含数据集、配置文件或其他运行时数据。
- `devlog/`: 开发日志或记录。
- `llm/`: 大语言模型相关模块。
  - `glm.py`: 可能包含与 GLM (General Language Model) 相关的实现。
  - `prompts.py`: 可能包含用于 LLM 的提示词定义。
- `modules/`: 其他功能模块，可能包含特定功能的独立组件。
- `pyproject.toml`: Python 项目的构建系统配置，使用 UV 管理依赖和项目元数据。
- `test/`: 测试文件和测试用例，用于验证项目功能的正确性。

## 核心功能（推测）

根据目录结构，本项目可能是一个基于 Python 的工具集合，尤其关注于大语言模型（LLM）相关的应用和开发。`agents` 和 `modules` 目录表明项目可能包含模块化的功能和自动化代理。`core` 目录则承载了项目的核心逻辑和通用工具。

## 安装和使用方法

### 1. 环境准备

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate  # macOS/Linux
# 或者在 Windows 上使用: venv\Scripts\activate

# 安装依赖
pip install pandas duckdb pyarrow
```

### 2. 数据分析功能

项目提供了自动化的数据分析工具，可以读取 `data/` 目录下的各种格式数据文件：

- **支持的文件格式**：CSV、Parquet、DuckDB
- **分析内容**：数据形状、列信息、缺失值统计、数值列描述统计、文本列基本信息

#### 快速开始

```bash
# 激活虚拟环境
source venv/bin/activate

# 运行数据分析
python run_data_analysis.py
```

#### 编程方式使用

```python
from modules.run_data_describe import DataAnalyzer

# 创建分析器实例
analyzer = DataAnalyzer()

# 分析所有数据文件
analyzer.analyze_all_data()

# 或者指定特定目录
analyzer = DataAnalyzer(data_dir="/path/to/your/data")
analyzer.analyze_all_data()
```

### 3. 项目结构说明

- `modules/run_data_describe.py`：核心数据描述模块，帮助用户理解数据现状
- `run_data_analysis.py`：命令行运行脚本
- `pyproject.toml`：项目依赖和配置
- `data/`：存放待分析的数据文件

# walker

```mermaid
flowchart TD
    U[用户输入问题：question] --> W[Walker 遍历所有模块]
    W --> M[调用匹配模块并执行]
    M --> R[组合模块结果，形成整体 strategy]
    R --> A[分析 Agent 汇总多个结果]
    A --> S[生成综合解读 summary]
    S --> WF[Walker 遍历生成后续分析建议：allow_followup]
    WF --> U2{用户是否触发后续分析？}
    U2 -- 是 --> M
    U2 -- 否 --> End[结束分析会话]
```
