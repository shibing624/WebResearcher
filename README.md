[**🇨🇳中文**](https://github.com/shibing624/webresearcher/blob/main/README.md) | [**🌐English**](https://github.com/shibing624/webresearcher/blob/main/README_EN.md) 


<p align="center">
  <img src="./docs/webresearcher.jpg" alt="WebResearcher Logo" height="150" alt="Logo"/>
</p>

---

# WebResearcher: An Iterative Deep-Research Agent
<p align="center">
  <a href="https://pypi.org/project/webresearcher/"><img src="https://img.shields.io/pypi/v/webresearcher.svg" alt="PyPI version"></a>
  <a href="https://pepy.tech/project/webresearcher"><img src="https://static.pepy.tech/badge/webresearcher" alt="Downloads"></a>
  <a href="https://github.com/shibing624/WebResearcher/blob/main/LICENSE"><img src="https://img.shields.io/github/license/shibing624/WebResearcher.svg" alt="License"></a>
  <a href="https://pypi.org/project/webresearcher/"><img src="https://img.shields.io/badge/Python-3.10%2B-green.svg" alt="Python versions"></a>
  <a href="https://arxiv.org/abs/2509.13309"><img src="https://img.shields.io/badge/arXiv-2509.13309-b31b1b.svg" alt="arXiv"></a>
  <a href="https://github.com/shibing624/WebResearcher"><img src="https://img.shields.io/badge/wechat-group-green.svg?logo=wechat" alt="Wechat Group"></a>
</p>

- 🧠 **迭代深度研究**: 通过周期性综合防止上下文溢出的新型范式
- 🔄 **无界推理**: 通过演化报告实现几乎无限的研究深度
- 🛠️ **丰富工具生态**: 网页搜索、学术论文、代码执行、文件解析
- 🎯 **生产就绪**: 零外部 Agent 框架依赖，完全自包含
- ⚡ **高性能**: 异步优先设计，智能 Token 管理，强大的错误处理
- 🎨 **易于使用**: 简洁的 CLI、清晰的 Python API、丰富的示例

## 📖 简介

**WebResearcher** 是迭代式深度研究智能体，基于 **IterResearch 范式**构建的自主研究智能体，旨在模拟专家级别的研究工作流。与遭受上下文溢出和噪音累积困扰的传统 Agent 不同，WebResearcher 将研究分解为离散的轮次，并进行迭代综合。

本项目提供两种研究智能体：
- **WebResearcher Agent**: 单智能体迭代研究，适合快速问答
- **WebWeaver Agent**: 双智能体协作研究，适合生成结构化长篇报告

### 传统 Agent 的问题

当前的开源研究 Agent 依赖于**单上下文、线性累积**模式：

1. **🚫 认知工作空间窒息**: 不断膨胀的上下文限制了深度推理能力
2. **🚫 不可逆的噪音污染**: 错误和无关信息不断累积
3. **🚫 缺乏周期性综合**: 无法暂停以提炼、重新评估和战略性规划

### WebResearcher 的解决方案

WebResearcher 实现了 **IterResearch 范式**，每轮通过**单次 LLM 调用**同时生成：

- **Think（思考）**: 内部推理和分析
- **Report（报告）**: 综合所有发现的更新研究摘要
- **Action（行动）**: 工具调用或最终答案

这种**一步式方法**（相比传统的两步式"思考→行动→综合"）带来了：
- ⚡ **速度提升 50%** - 每轮只需一次 LLM 调用而非两次
- 💰 **成本降低 40%** - 减少 Token 使用量
- 🧠 **推理更优** - Think、Report 和 Action 在统一上下文中生成

这实现了**无界的研究深度**，同时保持精简、聚焦的认知工作空间。

<p align="center">
  <img src="https://github.com/shibing624/WebResearcher/blob/main/docs/iterresearch.png" alt="范式对比" width="100%"/>
  <br>
  <em>图：单上下文范式（上）vs. 迭代深度研究范式（下）</em>
</p>

## 🏗️ 架构

### 核心组件

**IterResearch 范式 - 每轮单次 LLM 调用：**

```python
第 i 轮:
┌─────────────────────────────────────────────────────────┐
│  工作空间状态: (问题, 报告_{i-1}, 结果_{i-1})              │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  单次 LLM 调用 → 同时生成三部分：                          │
│  ├─ <think>: 分析当前状态                                │
│  ├─ <report>: 综合所有发现的更新报告                      │
│  └─ <tool_call> 或 <answer>: 下一步行动                  │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  如果是 <tool_call>: 执行工具                             │
│  如果是 <answer>: 返回最终答案                            │
└─────────────────────────────────────────────────────────┘
                          ↓
           使用更新后的报告和工具结果进入下一轮
```

**核心优势**: 报告在决定下一步行动*之前*就已完成综合，确保在统一上下文中进行连贯推理。

### 可用工具

| 工具 | 描述 | 使用场景 |
|------|------|----------|
| `search` | 通过 Serper API 的 Google 搜索 | 通用网页信息 |
| `google_scholar` | 学术论文搜索 | 科研文献查询 |
| `visit` | 网页内容提取 | 深度内容分析 |
| `python` | 沙盒代码执行 | 数据分析、计算 |
| `parse_file` | 多格式文件解析器 | 文档处理 |

## 🚀 快速开始

### 安装

```bash
pip install webresearcher
```

### 基础使用

```bash
# 设置 API 密钥
export OPENAI_API_KEY="your_key"
export SERPER_API_KEY="your_key"

# 运行研究查询
webresearcher "刘翔破纪录时候是多少岁?"
```

### Python API

```python
import asyncio
from webresearcher import WebResearcherAgent

# 配置
llm_config = {
    "model": "gpt-4o",
    "generate_cfg": {"temperature": 0.6}
}

# 创建 Agent
agent = WebResearcherAgent(
    llm_config=llm_config,
    function_list=["search", "google_scholar", "python"]
)

# 开始研究
async def main():
    result = await agent.run("您的研究问题")
    print(result['prediction'])

asyncio.run(main())
```

## 📚 高级用法

### 测试时扩展 (TTS)

对于需要最高准确性的关键问题，使用 TTS 模式（3-5倍成本）：

```bash
webresearcher "复杂问题" --use-tts --num-agents 3
```

```python
from webresearcher import TestTimeScalingAgent

agent = TestTimeScalingAgent(llm_config, function_list)
result = await agent.run("复杂问题", num_parallel_agents=3)
```

### 自定义工具

通过继承 `BaseTool` 创建您自己的工具：

```python
from webresearcher import BaseTool, WebResearcherAgent, TOOL_MAP

class MyCustomTool(BaseTool):
    name = "my_tool"
    description = "工具功能描述"
    parameters = {"type": "object", "properties": {...}}
    
    def call(self, params, **kwargs):
        # 您的工具逻辑
        return "结果"

# 注册并使用
TOOL_MAP['my_tool'] = MyCustomTool()
agent = WebResearcherAgent(llm_config, function_list=["my_tool", "search"])
```

查看 [examples/custom_agent.py](./examples/custom_agent.py) 获取完整示例。

### 批量处理

高效处理多个问题：

```python
from webresearcher import WebResearcherAgent

questions = ["问题 1", "问题 2", "问题 3"]
agent = WebResearcherAgent(llm_config)

for question in questions:
    result = await agent.run(question)
    print(f"Q: {question}\nA: {result['prediction']}\n")
```

查看 [examples/batch_research.py](./examples/batch_research.py) 获取高级批量处理示例。

### Python 解释器配置

`PythonInterpreter` 工具支持两种执行模式：

**1. 沙箱模式（生产环境推荐）：**
```bash
# 配置沙箱端点
export SANDBOX_FUSION_ENDPOINTS="http://your-sandbox-endpoint.com"
```

**2. 本地模式（自动降级）：**
- 当未配置 `SANDBOX_FUSION_ENDPOINTS` 时，代码在本地执行
- 适用于开发和测试
- ⚠️ **警告**：本地执行会在当前 Python 环境中运行代码

```python
from webresearcher import PythonInterpreter

# 如果配置了沙箱则使用沙箱，否则降级到本地执行
interpreter = PythonInterpreter()
result = interpreter.call({'code': 'print("Hello, World!")'})
```

详细示例请参考 [examples/python_interpreter_example.py](./examples/python_interpreter_example.py)。

### 日志管理

WebResearcher 提供了统一的日志管理系统，可以通过环境变量或编程方式控制日志级别：

**通过环境变量：**

```bash
# 运行前设置日志级别
export WEBRESEARCHER_LOG_LEVEL=DEBUG  # 选项：DEBUG, INFO, WARNING, ERROR, CRITICAL
webresearcher "你的问题"
```

**编程方式：**

```python
from webresearcher import set_log_level, add_file_logger

# 设置控制台日志级别
set_log_level("WARNING")  # 只显示警告和错误

# 添加文件日志，支持自动轮转
add_file_logger("research.log", level="DEBUG")

# 现在执行研究
agent = WebResearcherAgent(llm_config)
result = await agent.run("你的问题")
```

**文件日志功能：**
- 文件大小超过 10MB 时自动轮转
- 保留最近 7 天的日志
- 自动压缩旧日志为 .zip 格式

详细使用方法请参考 [logger.py](https://github.com/shibing624/WebResearcher/blob/main/webresearcher/logger.py)。

## 🎯 功能特性

### 核心特性

- ✅ **迭代综合**: 通过周期性报告更新防止上下文溢出
- ✅ **无界深度**: 几乎无限的研究轮次
- ✅ **智能 Token 管理**: 自动上下文修剪和压缩
- ✅ **异步支持**: 非阻塞 I/O 提升性能

### 工具特性

- ✅ **网页搜索**: 通过 Serper 集成 Google 搜索
- ✅ **学术搜索**: Google Scholar 查询研究论文
- ✅ **网页抓取**: 智能内容提取
- ✅ **代码执行**: 沙盒 Python 解释器
- ✅ **文件处理**: 支持 PDF、DOCX、CSV、Excel 等
- ✅ **可扩展**: 轻松创建自定义工具

### 生产特性

- ✅ **零框架锁定**: 无 qwen-agent 等类似依赖
- ✅ **CLI + API**: 支持命令行和 Python 调用

## 📊 性能表现

基于论文的评估结果：

- **HotpotQA**: 在多跳推理任务上表现优异
- **Bamboogle**: 在复杂事实问题上表现出色
- **上下文管理**: 即使 50+ 轮后仍保持精简的工作空间
- **准确性**: 与基线 Agent 相当或超越

<p align="center">
  <img src="https://github.com/shibing624/WebResearcher/blob/main/docs/performance.png" alt="性能表现" width="100%"/>
</p>

## 🔧 配置

### 环境变量

```bash
# 必需
OPENAI_API_KEY=...              # OpenAI API 密钥 或 DeepSeek API 密钥
SERPER_API_KEY=...                 # Serper API（Google 搜索）

# 可选
OPENAI_BASE_URL=https://...        # 自定义 OpenAI 端点, 或 DeepSeek base url
JINA_API_KEY=...                   # Jina AI（网页抓取）
SANDBOX_FUSION_ENDPOINTS=...       # 代码执行沙盒
MAX_LLM_CALL_PER_RUN=50           # 每次研究的最大迭代次数
FILE_DIR=./files                   # 文件存储目录
```

### LLM 配置

```python
llm_config = {
    "model": "deepseek-v3.1",              # 或: o3-mini, gpt-4-turbo 等
    "generate_cfg": {
        "temperature": 0.6,          # 采样温度 (0.0-2.0)
        "top_p": 0.95,              # 核采样
        "presence_penalty": 1.1,     # 重复惩罚
        "model_thinking_type": "enabled"  # enabled|disabled|auto, 如果不支持thinking，则不设置
    },
    "max_input_tokens": 32000,      # 上下文窗口限制
    "llm_timeout": 300.0,           # LLM API 超时（秒）
    "agent_timeout": 600.0,         # Agent 总超时（秒）
}
```

## 🎭 WebWeaver Agent

**WebWeaver** 是一个双智能体研究框架，实现了动态大纲范式，提供比单智能体 WebResearcher 更结构化的研究方法。

### 架构组件

#### 1. Memory Bank（记忆库）
共享的证据存储，连接 Planner 和 Writer 智能体：
- **添加证据**: Planner 存储发现的内容并分配引用 ID
- **检索证据**: Writer 通过 ID 获取特定证据
- **解耦存储**: 让智能体专注于各自的任务

#### 2. Planner Agent（规划智能体）
探索研究问题并构建带引用的大纲：
- **操作**:
  - `search`: 从网络收集信息
  - `write_outline`: 创建/更新带引用的研究大纲
  - `terminate`: 完成规划阶段
- **输出**: 带有引用 ID 的结构化大纲

#### 3. Writer Agent（写作智能体）
逐节撰写综合报告：
- **操作**:
  - `retrieve`: 从 Memory Bank 获取证据
  - `write`: 撰写带内联引用的报告章节
  - `terminate`: 完成写作阶段
- **输出**: 带有适当引用的完整研究报告

<p align="center">
  <img src="https://github.com/shibing624/WebResearcher/blob/main/docs/webweaver.png" alt="WebWeaver架构" width="100%"/>
</p>

### 核心特性

#### 动态大纲
与传统静态大纲不同，WebWeaver 的大纲随着新证据的发现而演化：
1. Planner 搜索并发现证据
2. 每个发现获得唯一的引用 ID
3. 大纲更新以纳入新证据
4. 过程重复直到大纲完整

#### 引用支撑的报告
最终报告中的所有声明都有具体证据支持：
- 证据在 Memory Bank 中存储完整上下文
- Writer 仅检索每个章节的相关证据
- 引用内联嵌入（例如 `[cite:id_1]`）

### WebWeaver 使用方法

#### 基础使用

```python
import asyncio
from webresearcher import WebWeaverAgent

async def main():
    # 配置 LLM
    llm_config = {
        "model": "gpt-4o",
        "generate_cfg": {
            "temperature": 0.1,  # 低温度用于事实性研究
            "top_p": 0.95,
            "max_tokens": 10000,
        },
        "llm_timeout": 300.0,
    }
    
    # 初始化智能体
    agent = WebWeaverAgent(llm_config=llm_config)
    
    # 执行研究
    question = "气候变化的主要原因是什么？"
    result = await agent.run(question)
    
    # 访问结果
    print("最终大纲:", result['final_outline'])
    print("最终报告:", result['final_report'])
    print("记忆库大小:", result['memory_bank_size'])

if __name__ == "__main__":
    asyncio.run(main())
```

#### 命令行使用

```bash
# 使用 WebWeaver 模式
webresearcher "气候变化的原因是什么？" --use-webweaver

# 保存结果到文件
webresearcher "研究问题" --use-webweaver --output report.json

# 详细日志
webresearcher "问题" --use-webweaver --verbose
```

### WebResearcher vs WebWeaver 对比

| 特性 | WebResearcher | WebWeaver |
|------|---------------|-----------|
| 架构 | 单智能体 | 双智能体 |
| 范式 | IterResearch | 动态大纲 |
| 记忆 | 无状态工作空间 | Memory Bank |
| 输出 | 直接答案 | 大纲 + 报告 |
| 引用 | 隐式 | 显式带 ID |
| 结构 | 迭代综合 | 层次化 |
| 适用场景 | 快速问答 | 综合报告 |

### 何时使用 WebWeaver

选择 **WebWeaver** 当您需要：
- ✅ 长篇、综合性研究报告
- ✅ 显式引用追踪
- ✅ 带证据映射的结构化大纲
- ✅ 可复现的研究过程
- ✅ 多章节文档

选择 **WebResearcher** 当您需要：
- ✅ 快速、聚焦的答案
- ✅ 更简单的架构
- ✅ 直接的问答格式
- ✅ 更低的 Token 使用量
- ✅ 更快的结果

## 📝 示例

查看 [examples/](./examples/) 目录获取完整示例：

- **[webresearcher_usage.py](examples/webresearcher_usage.py)** - WebResearcher Agent 使用示例
- **[batch_research.py](./examples/batch_research.py)** - 批量处理多个问题
- **[custom_agent.py](./examples/custom_agent.py)** - 创建自定义工具
- **[webweaver_usage.py](examples/webweaver_usage.py)** - WebWeaver Agent 使用示例

## 🧪 测试

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest

# 运行覆盖率测试
pytest --cov=webresearcher
```

## 🤝 参与贡献

我们欢迎各种形式的贡献！

贡献方式：
- 🐛 报告 Bug
- 💡 提出新功能建议
- 📝 改进文档
- 🔧 提交 Pull Request

详细指南请查看 [CONTRIBUTING.md](./CONTRIBUTING.md)。

## 📧 联系方式

- **GitHub Issues**: [报告问题或功能请求](https://github.com/shibing624/WebResearcher/issues)
- **邮箱**: xuming624@qq.com
- **微信**: xuming624（备注：姓名-公司-NLP）

<p align="center">
  <img src="https://github.com/shibing624/WebResearcher/blob/main/docs/wechat.jpeg" width="200" />
</p>

## 🌟 Star 历史

[![Star History Chart](https://api.star-history.com/svg?repos=shibing624/WebResearcher&type=Date)](https://star-history.com/#shibing624/WebResearcher&Date)

## 📑 引用

如果您在研究中使用了 WebResearcher，请引用：

```bibtex
@misc{qiao2025webresearcher,
    title={WebResearcher: Unleashing unbounded reasoning capability in Long-Horizon Agents}, 
    author={Zile Qiao and Guoxin Chen and Xuanzhong Chen and Donglei Yu and Wenbiao Yin and Xinyu Wang and Zhen Zhang and Baixuan Li and Huifeng Yin and Kuan Li and Rui Min and Minpeng Liao and Yong Jiang and Pengjun Xie and Fei Huang and Jingren Zhou},
    year={2025},
    eprint={2509.13309},
    archivePrefix={arXiv},
    primaryClass={cs.CL},
    url={https://arxiv.org/abs/2509.13309}, 
}
```

```bibtex
@misc{li2025webweaverstructuringwebscaleevidence,
      title={WebWeaver: Structuring Web-Scale Evidence with Dynamic Outlines for Open-Ended Deep Research}, 
      author={Zijian Li and Xin Guan and Bo Zhang and Shen Huang and Houquan Zhou and Shaopeng Lai and Ming Yan and Yong Jiang and Pengjun Xie and Fei Huang and Jun Zhang and Jingren Zhou},
      year={2025},
      eprint={2509.13312},
      archivePrefix={arXiv},
      primaryClass={cs.CL},
      url={https://arxiv.org/abs/2509.13312}, 
}
```

## 📄 许可证

本项目采用 [Apache License 2.0](./LICENSE) 许可证 - 可免费用于商业用途。

## 🙏 致谢

本项目受以下研究启发并在此基础上构建：

- **[WebResearcher 论文](https://arxiv.org/abs/2509.13309)** by Qiao et al.
- **[WebWeaver 论文](https://arxiv.org/abs/2509.13312)** by Li et al.
- **[Alibaba-NLP/DeepResearch](https://github.com/Alibaba-NLP/DeepResearch)** - 原始研究实现

特别感谢论文作者在迭代研究范式上的开创性工作！

