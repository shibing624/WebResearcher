# 日志系统迁移说明

## 概述

WebResearcher 项目已完成日志系统统一管理的重构，所有模块现在使用统一配置的 logger，可以通过环境变量或编程方式控制整体日志级别。

## 变更内容

### 1. 新增文件

- **`webresearcher/logger.py`**: 统一的日志配置模块
  - 提供 `logger` 实例
  - 提供 `set_log_level()` 函数动态设置日志级别
  - 提供 `add_file_logger()` 函数添加文件日志
  - 支持通过环境变量 `WEBRESEARCHER_LOG_LEVEL` 控制日志级别

### 2. 修改的文件

以下文件的 logger 导入已从 `from loguru import logger` 改为 `from webresearcher.logger import logger`：

1. `webresearcher/agent.py`
2. `webresearcher/cli.py`
3. `webresearcher/tool_python.py`
4. `webresearcher/tool_scholar.py`
5. `webresearcher/tool_search.py`
6. `webresearcher/tool_visit.py`
7. `webresearcher/tts_agent.py`
8. `webresearcher/file_tools/file_parser.py`
9. `webresearcher/file_tools/utils.py`
10. `webresearcher/file_tools/video_analysis.py`

### 3. 更新的导出

`webresearcher/__init__.py` 已更新，新增导出：
- `logger`
- `set_log_level`
- `add_file_logger`

用户可以直接从主包导入：
```python
from webresearcher import logger, set_log_level, add_file_logger
```

### 4. 文档更新

- **新增**: `docs/logging_guide.md` - 详细的日志使用指南
- **新增**: `examples/logging_example.py` - 日志系统使用示例
- **更新**: `README.md` - 添加了日志管理章节
- **更新**: `README_zh.md` - 添加了日志管理章节（中文）

### 5. Bug 修复

- `webresearcher/tool_file.py` 添加了缺失的 `import os`

## 使用方法

### 方式一：环境变量（推荐用于生产环境）

```bash
export WEBRESEARCHER_LOG_LEVEL=WARNING
python your_script.py
```

### 方式二：编程设置（推荐用于开发调试）

```python
from webresearcher import set_log_level

# 开发时查看详细日志
set_log_level("DEBUG")

# 生产环境只看错误
set_log_level("ERROR")
```

### 方式三：添加文件日志

```python
from webresearcher import add_file_logger

# 同时输出到控制台和文件
add_file_logger("app.log", level="INFO")
```

## 优势

1. **统一管理**: 所有模块使用同一个 logger 实例，便于统一控制
2. **灵活配置**: 支持环境变量和编程两种方式设置日志级别
3. **开箱即用**: 默认配置适合大多数场景
4. **向后兼容**: 不影响现有代码的使用方式
5. **生产就绪**: 支持文件轮转、自动压缩、定期清理

## 日志级别说明

| 级别 | 用途 | 适用场景 |
|------|------|----------|
| DEBUG | 详细的调试信息 | 开发和问题排查 |
| INFO | 一般性信息（默认） | 正常运行时的重要信息 |
| WARNING | 警告信息 | 生产环境推荐级别 |
| ERROR | 错误信息 | 只关注错误 |
| CRITICAL | 严重错误 | 生产环境最小输出 |

## 测试验证

所有修改已通过测试验证：

```bash
# 测试导入
python -c "from webresearcher import logger, set_log_level, add_file_logger; print('OK')"

# 测试功能
python examples/logging_example.py
```

## 迁移建议

对于使用 WebResearcher 的项目：

1. **无需修改代码**: 现有代码可以继续正常工作
2. **建议添加日志控制**: 在应用启动时设置合适的日志级别
3. **生产环境配置**: 使用环境变量 `WEBRESEARCHER_LOG_LEVEL=WARNING`

## 参考文档

- [日志使用指南](./docs/logging_guide.md)
- [使用示例](./examples/logging_example.py)
- [Loguru 官方文档](https://loguru.readthedocs.io/)

