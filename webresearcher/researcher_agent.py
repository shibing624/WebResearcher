# -*- coding: utf-8 -*-
"""
@author:XuMing(xuming624@qq.com)
@description: 
"""

import asyncio

from typing import Dict, List
from loguru import logger
from qwen_agent.tools import BaseTool

from webresearcher.react_agent import MultiTurnReactAgent


class WebResearcherAgent:
    """
    [新] 论文中的“Research-Synthesis Framework”编排器。
    它负责并行运行多个 IterResearch Agent 并整合它们的最终报告。
    """

    def __init__(self, llm_config: Dict, function_list: List[BaseTool]):
        self.llm_config = llm_config
        self.function_list = function_list
        self.tool_map = {tool.name: tool for tool in function_list}

    async def run_parallel_research(self, data: Dict, model: str, num_parallel_agents: int = 3) -> List[Dict]:
        """
        [新] 阶段 1: 并行研究 (Parallel Research)
        """
        logger.info(f"--- Starting Parallel Research Phase ({num_parallel_agents} agents) ---")

        # 为每个并行 Agent 创建一个实例
        # 注意：这里我们改变 LLM temperature 来增加多样性 (论文中的 "divergent exploration")
        tasks = []
        for i in range(num_parallel_agents):
            agent_llm_config = self.llm_config.copy()
            # 动态调整温度以鼓励多样性
            agent_llm_config["generate_cfg"]["temperature"] = 0.5 + (i * 0.2)  # e.g., 0.5, 0.7, 0.9

            agent = MultiTurnReactAgent(
                function_list=self.function_list,
                llm=agent_llm_config
            )

            # `data` 包含了 question, answer, planning_port 等
            tasks.append(agent._run(data, model))

        # [关键] 使用 asyncio.gather 并行执行所有 agent
        parallel_results = await asyncio.gather(*tasks, return_exceptions=True)

        logger.info("--- Parallel Research Phase Complete ---")

        valid_results = []
        for i, res in enumerate(parallel_results):
            if isinstance(res, Exception):
                logger.error(f"Agent {i} failed with exception: {res}")
            elif res.get("termination") == "answer":
                logger.info(f"Agent {i} succeeded.")
                valid_results.append(res)
            else:
                logger.warning(f"Agent {i} finished with status: {res.get('termination')}")
                valid_results.append(res)  # 即使失败也保留其报告

        return valid_results

    async def run_synthesis(self, question: str, parallel_results: List[Dict], data: Dict, model: str) -> Dict:
        """
        [新] 阶段 2: 整合总结 (Integrative Synthesis)
        """
        logger.info("--- Starting Integrative Synthesis Phase ---")

        if not parallel_results:
            logger.error("No valid results from parallel research. Cannot synthesize.")
            return {"final_answer": "Synthesis failed: No research data.", "reports": []}

        # 1. 构建“总结提示”
        synthesis_prompt_content = f"【原始研究问题】\n{question}\n\n"
        synthesis_prompt_content += "【来自多个并行研究员的报告和答案】\n"

        reports_for_log = []

        for i, res in enumerate(parallel_results):
            synthesis_prompt_content += f"\n--- 研究员 {i + 1} (状态: {res.get('termination')}) ---\n"
            synthesis_prompt_content += f"【研究员 {i + 1} 的答案】\n{res.get('final_answer')}\n"
            synthesis_prompt_content += f"【研究员 {i + 1} 的最终报告】\n{res.get('final_report')}\n"
            reports_for_log.append({
                "agent": i + 1,
                "answer": res.get('prediction'),
                "report": res.get('report')
            })

        synthesis_messages = [
            {"role": "system", "content": (
                "你是一个顶级的“首席研究员”。\n"
                "你的任务是审查来自多个并行研究员的报告和答案，然后综合所有信息，得出一个唯一的、最准确、最全面的最终答案。\n"
                "1. 交叉验证：比较不同报告中的事实和结论。\n"
                "2. 解决冲突：如果报告冲突，请根据证据做出最佳判断。\n"
                "3. 综合提炼：不要只选择一个答案，要整合所有报告中的有效信息，形成一个更优的答案。\n"
                "4. 你的回答必须是最终答案，不要讨论你的综合过程。只提供最终答案。"
            )},
            {"role": "user", "content": synthesis_prompt_content}
        ]

        # 2. 创建一个“总结 Agent”实例来执行总结
        # (使用一个稳定的、低温的配置)
        synthesis_llm_config = self.llm_config.copy()
        synthesis_llm_config["generate_cfg"]["temperature"] = 0.2

        synthesis_agent = MultiTurnReactAgent(
            function_list=[],  # 总结 Agent 不需要工具
            llm=synthesis_llm_config
        )

        # 3. 调用 LLM 进行最终总结
        final_answer_raw = await synthesis_agent.call_server(
            synthesis_messages,
            stop_sequences=[]  # 不需要工具的 stop token
        )

        return {
            "final_answer": final_answer_raw.strip(),
            "synthesis_reports": reports_for_log
        }

    async def run(self, data: Dict, model: str, num_parallel_agents: int = 3) -> Dict:
        """
        [新] WebResearcher 的主入口点
        """
        question = data['item']['question']
        ground_truth = data['item']['answer']

        # 阶段 1
        parallel_results = await self.run_parallel_research(data, model, num_parallel_agents)

        # 阶段 2
        synthesis_result = await self.run_synthesis(question, parallel_results, data, model)

        return {
            "question": question,
            "ground_truth": ground_truth,
            "final_synthesized_answer": synthesis_result["final_answer"],
            "parallel_runs": parallel_results,  # 包含每个 agent 的完整日志
            "synthesis_inputs": synthesis_result["synthesis_reports"]  # 简洁版报告
        }
