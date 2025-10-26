#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试 IterResearch 范式的实现
"""
import asyncio
import os
from webresearcher.agent import WebResearcherAgent
from webresearcher.logger import logger

async def test_iterresearch():
    """测试 IterResearch 范式"""
    
    # 检查环境变量
    if not os.getenv("OPENAI_API_KEY"):
        logger.error("请设置 OPENAI_API_KEY 环境变量")
        return
    
    # 1. 定义 LLM 配置
    llm_config = {
        "model": "gpt-4o",
        "generate_cfg": {
            'max_input_tokens': 32000,
            "temperature": 0.6,
            "top_p": 0.95,
            "presence_penalty": 1.1
        },
        "llm_timeout": 300.0,
        "agent_timeout": 600.0,
        "model_thinking_type": "disabled"
    }

    # 2. 实例化 agent
    agent = WebResearcherAgent(
        llm_config=llm_config,
        function_list=['search', 'visit', 'PythonInterpreter']
    )

    # 3. 测试问题
    question = '刘翔破纪录时候是多少岁?'
    
    logger.info(f"=" * 80)
    logger.info(f"测试 IterResearch 范式")
    logger.info(f"问题: {question}")
    logger.info(f"=" * 80)

    # 4. 运行研究
    result = await agent.run(question)

    # 5. 打印结果
    logger.info(f"\n" + "=" * 80)
    logger.info(f"研究完成")
    logger.info(f"=" * 80)
    logger.info(f"问题: {result['question']}")
    logger.info(f"终止原因: {result['termination']}")
    logger.info(f"\n最终答案:")
    logger.info(f"{result['prediction']}")
    logger.info(f"\n最终研究报告:")
    logger.info(f"{result['report']}")
    logger.info(f"=" * 80)
    
    # 6. 打印轨迹统计
    trajectory_count = len([msg for msg in result['trajectory'] if msg.get('role') == 'assistant'])
    logger.info(f"总 LLM 调用次数: {trajectory_count}")


if __name__ == "__main__":
    asyncio.run(test_iterresearch())

