#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Python Interpreter 使用示例

演示如何使用 PythonInterpreter 工具执行代码，包括：
1. 沙箱环境执行（需要配置 SANDBOX_FUSION_ENDPOINTS）
2. 本地环境降级执行（无需配置）
"""

import os
from webresearcher.tool_python import PythonInterpreter

print("=" * 70)
print("Python Interpreter 使用示例")
print("=" * 70)

# 检查是否配置了沙箱环境
sandbox_endpoints = os.environ.get('SANDBOX_FUSION_ENDPOINTS', '')
if sandbox_endpoints and sandbox_endpoints != '':
    print(f"\n✓ 沙箱环境已配置: {sandbox_endpoints}")
    print("  代码将在安全的沙箱环境中执行")
else:
    print("\n⚠ 沙箱环境未配置")
    print("  代码将在本地环境中执行（降级模式）")
    print("  提示：设置 SANDBOX_FUSION_ENDPOINTS 环境变量可启用沙箱执行")

print("\n" + "=" * 70)

# 创建解释器实例
interpreter = PythonInterpreter()

# 示例 1: 基本计算
print("\n【示例 1】基本计算")
print("-" * 70)

code1 = """
# 计算圆的面积
import math

radius = 5
area = math.pi * radius ** 2
print(f"半径为 {radius} 的圆的面积是: {area:.2f}")

# 斐波那契数列
def fibonacci(n):
    a, b = 0, 1
    for _ in range(n):
        print(a, end=' ')
        a, b = b, a + b
    print()

print("\\n前10个斐波那契数:")
fibonacci(10)
"""

result1 = interpreter.call({'code': code1})
print("执行结果:")
print(result1)

# 示例 2: 数据处理
print("\n" + "=" * 70)
print("\n【示例 2】数据处理")
print("-" * 70)

code2 = """
# 处理列表数据
data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

# 计算统计信息
mean = sum(data) / len(data)
max_val = max(data)
min_val = min(data)

print(f"数据: {data}")
print(f"平均值: {mean}")
print(f"最大值: {max_val}")
print(f"最小值: {min_val}")

# 筛选偶数
even_numbers = [x for x in data if x % 2 == 0]
print(f"偶数: {even_numbers}")
"""

result2 = interpreter.call({'code': code2})
print("执行结果:")
print(result2)

# 示例 3: 字符串处理
print("\n" + "=" * 70)
print("\n【示例 3】字符串处理")
print("-" * 70)

code3 = """
text = "Hello, World! This is a Python Interpreter example."

print(f"原始文本: {text}")
print(f"长度: {len(text)}")
print(f"大写: {text.upper()}")
print(f"小写: {text.lower()}")
print(f"单词数: {len(text.split())}")

# 统计字符
char_count = {}
for char in text.lower():
    if char.isalpha():
        char_count[char] = char_count.get(char, 0) + 1

# 显示前5个最常见的字符
sorted_chars = sorted(char_count.items(), key=lambda x: x[1], reverse=True)[:5]
print("\\n最常见的5个字母:")
for char, count in sorted_chars:
    print(f"  {char}: {count}次")
"""

result3 = interpreter.call({'code': code3})
print("执行结果:")
print(result3)

# 示例 4: 错误处理
print("\n" + "=" * 70)
print("\n【示例 4】错误处理")
print("-" * 70)

code4 = """
# 这段代码会产生错误
print("尝试除以零...")
result = 10 / 0
print(f"结果: {result}")
"""

result4 = interpreter.call({'code': code4})
print("执行结果:")
print(result4)

# 示例 5: 使用三引号代码块
print("\n" + "=" * 70)
print("\n【示例 5】使用三引号代码块格式")
print("-" * 70)

code_with_backticks = """```python
# 这是用 markdown 格式包裹的代码
for i in range(5):
    print(f"星星 {'*' * (i + 1)}")
```"""

result5 = interpreter.call({'code': code_with_backticks})
print("执行结果:")
print(result5)

print("\n" + "=" * 70)
print("\n所有示例执行完成！")
print("\n使用建议：")
print("1. 生产环境建议配置 SANDBOX_FUSION_ENDPOINTS 使用沙箱执行")
print("2. 本地开发可以直接使用本地执行模式")
print("3. 始终使用 print() 输出你想看到的结果")
print("4. 代码可以使用三引号或 <code></code> 标签包裹")
print("=" * 70)

