# API密钥401错误问题解决记录

## 问题描述

在运行意图识别测试时，出现了HTTP 401 Unauthorized错误：

```
INFO:httpx:HTTP Request: POST https://open.bigmodel.cn/api/paas/v4/chat/completions "HTTP/1.1 401 Unauthorized"
ERROR:llm.glm:GLM调用失败: Error code: 401 - {'error': {'code': '401', 'message': '令牌已过期或验证不正确'}}
```

## 问题分析

### 1. 初步排查

- ✅ `.env` 文件存在且包含正确的API密钥
- ✅ `llm/glm.py` 中正确使用 `os.getenv("ZHIPU_API_KEY")` 获取密钥
- ❌ 测试脚本中缺少环境变量加载

### 2. 深入调查

通过创建 `test_api_key.py` 测试脚本发现：
- 程序读取到的API密钥是 `your_zhipu_api_key_here`（占位符）
- 而不是 `.env` 文件中的真实密钥

### 3. 根本原因

**系统环境变量覆盖了.env文件中的配置**

```bash
$ echo $ZHIPU_API_KEY
your_zhipu_api_key_here
```

系统环境变量中存在一个占位符值，优先级高于 `.env` 文件，导致程序使用了无效的API密钥。

## 解决方案

### 1. 清除系统环境变量

```bash
unset ZHIPU_API_KEY
```

### 2. 修复测试脚本

为所有测试脚本添加环境变量加载：

```python
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()
```

修复的文件：
- `test/test_intent_parser.py`
- `test/test_simplified_intent.py` 
- `test/demo_intent_architecture.py`

### 3. 创建API密钥测试工具

创建了 `test/test_api_key.py` 用于验证API密钥配置：
- 检查 `.env` 文件存在性
- 验证环境变量加载
- 测试API密钥有效性

## 验证结果

### 修复前
```
📋 完整API密钥: your_zhipu_api_key_here
📡 HTTP状态码: 401
❌ API调用失败: 401
```

### 修复后
```
📋 完整API密钥: 16f012cbe6554ae8b4db0b4fef781745.5pVowskhanMVRXzO
📡 HTTP状态码: 200
✅ API密钥有效！
🤖 响应: 你好👋！很高兴见到你，有什么可以帮助你的吗？
```

### 意图识别测试恢复正常
```
INFO:httpx:HTTP Request: POST https://open.bigmodel.cn/api/paas/v4/chat/completions "HTTP/1.1 200 OK"
INFO:llm.glm:GLM调用成功，使用tokens: 283
INFO:llm.glm:JSON解析成功: {'intent': 'data_analysis', 'confidence': 0.9, 'reason': '用户询问数据相关信息', 'need_data_analysis': True}
```

## 经验总结

### 环境变量优先级
1. **系统环境变量** (最高优先级)
2. `.env` 文件
3. 代码中的默认值

### 最佳实践
1. **测试脚本必须加载环境变量**：所有独立运行的测试脚本都应该包含 `load_dotenv()`
2. **环境变量冲突检查**：在部署前检查系统环境变量是否与配置文件冲突
3. **API密钥验证工具**：创建专门的测试工具来验证API配置
4. **错误信息分析**：401错误不一定是密钥过期，也可能是配置问题

### 预防措施
1. 在项目README中说明环境变量配置要求
2. 提供环境检查脚本
3. 在CI/CD中包含环境配置验证步骤

## 相关文件

- 🔧 **修复文件**：
  - `test/test_intent_parser.py`
  - `test/test_simplified_intent.py`
  - `test/demo_intent_architecture.py`

- 🆕 **新增文件**：
  - `test/test_api_key.py` - API密钥测试工具
  - `devlog/api_key_issue_resolution.md` - 本文档

- 📋 **配置文件**：
  - `.env` - 环境变量配置
  - `llm/glm.py` - GLM客户端

---

**解决时间**: 2024年12月
**问题类型**: 环境配置
**影响范围**: 所有依赖GLM API的功能
**解决状态**: ✅ 已解决