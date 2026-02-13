# -*- coding: utf-8 -*-
"""
@author:XuMing(xuming624@qq.com)
@description: Test-Time Scaling (TTS) Agent - Optional inference enhancement

This module implements the Test-Time Scaling technique from the WebResearcher paper.
It's an OPTIONAL inference enhancement that trades cost (3-5x tokens) for higher accuracy.

COST WARNING:
- Running N parallel agents costs approximately N × single-agent cost
- Synthesis step adds ~0.5x additional cost
- Total cost: ~(N + 0.5)x of single-agent baseline

WHEN TO USE:
Use for high-value scenarios:
   - Scientific research questions
   - Medical/legal analysis
   - Critical investment decisions
   - Complex technical problem-solving

DON'T use for:
   - Daily queries
   - Simple questions
   - Cost-sensitive applications
   - Real-time interactions

For 95% of use cases, prefer the single WebResearcherAgent (agent.py).
"""

import asyncio
from typing import Dict, List, Optional

from webresearcher.log import logger
from webresearcher.web_researcher_agent import WebResearcherAgent


class TestTimeScalingAgent:
    """
    Test-Time Scaling (TTS) Agent with parallel research and synthesis.
    
    This agent runs multiple IterResearch agents (WebResearcherAgent) in parallel 
    with different temperatures to encourage diverse exploration paths, then 
    synthesizes their findings into a final answer.
    
    Each parallel agent follows the IterResearch paradigm (single LLM call per round
    generating Plan + Report + Action), ensuring efficient and coherent research.
    
    This is analogous to:
    - Self-Consistency sampling in chain-of-thought
    - Best-of-N sampling
    - Monte Carlo Tree Search (MCTS) in game playing
    
    Args:
        llm_config: LLM configuration dict
        function_list: List of tool names to enable
    """

    def __init__(self, llm_config: Optional[Dict] = None, function_list: Optional[List[str]] = None, **kwargs):
        llm_config = dict(llm_config or {})
        self.llm_config = llm_config
        self.function_list = function_list

    def estimate_cost(self, num_parallel_agents: int = 3) -> str:
        """
        Estimate the cost multiplier of using TTS.
        
        Args:
            num_parallel_agents: Number of parallel research agents
            
        Returns:
            Cost estimation message
        """
        total_cost = num_parallel_agents + 0.5
        return (
            f"TTS Cost Estimation:\n"
            f"   • Parallel research: {num_parallel_agents} agents × base cost\n"
            f"   • Synthesis: ~0.5× base cost\n"
            f"   • Total: ~{total_cost:.1f}× of single-agent baseline\n"
            f"   • Use only for high-value scenarios!"
        )

    async def run_parallel_research(
        self, 
        question: str, 
        num_parallel_agents: int = 3
    ) -> List[Dict]:
        """
        Phase 1: Parallel Research with diverse exploration.
        
        Runs multiple IterResearch agents in parallel, each with different
        temperature settings to encourage diverse reasoning paths.
        
        Args:
            question: Research question
            num_parallel_agents: Number of parallel agents (default: 3)
            
        Returns:
            List of research results from each agent
        """
        logger.debug(f"Starting Parallel Research Phase ({num_parallel_agents} agents)")
        logger.warning(self.estimate_cost(num_parallel_agents))

        tasks = []
        for i in range(num_parallel_agents):
            # Create a copy of config for each agent
            agent_llm_config = self.llm_config.copy()
            agent_llm_config["generate_cfg"] = agent_llm_config.get("generate_cfg", {}).copy()
            
            # Adjust temperature for diversity (e.g., 0.5, 0.7, 0.9)
            base_temp = agent_llm_config["generate_cfg"].get("temperature", 0.6)
            agent_llm_config["generate_cfg"]["temperature"] = base_temp + (i * 0.2)
            
            # Create agent instance
            agent = WebResearcherAgent(
                llm_config=agent_llm_config,
                function_list=self.function_list,
            )
            
            # Add to parallel tasks
            tasks.append(agent.run(question))
            logger.debug(
                f"Agent {i+1}: temperature={agent_llm_config['generate_cfg']['temperature']:.2f}"
            )

        # Execute all agents in parallel
        parallel_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        valid_results = []
        for i, res in enumerate(parallel_results):
            if isinstance(res, Exception):
                logger.error(f"Agent {i+1} failed with exception: {res}")
            elif isinstance(res, dict):
                status = res.get("termination", "unknown")
                if status == "answer":
                    logger.debug(f"Agent {i+1} succeeded (status: {status})")
                else:
                    logger.warning(f"Agent {i+1} finished with status: {status}")
                valid_results.append(res)
            else:
                logger.error(f"Agent {i+1} returned unexpected type: {type(res)}")

        logger.debug(f"Parallel Research Complete: {len(valid_results)}/{num_parallel_agents} agents succeeded")
        return valid_results

    async def run_synthesis(
        self, 
        question: str, 
        parallel_results: List[Dict]
    ) -> Dict:
        """
        Phase 2: Integrative Synthesis.
        
        Synthesizes findings from multiple parallel research agents into
        a single, high-quality final answer.
        
        Args:
            question: Original research question
            parallel_results: Results from parallel research phase
            
        Returns:
            Dict with final_answer and synthesis_reports
        """
        logger.debug("Starting Integrative Synthesis Phase")

        if not parallel_results:
            logger.error("No valid results from parallel research. Cannot synthesize.")
            return {
                "final_answer": "Synthesis failed: No research data available.",
                "synthesis_reports": []
            }

        # Build synthesis prompt
        synthesis_prompt_content = f"【原始研究问题】\n{question}\n\n"
        synthesis_prompt_content += "【来自多个并行研究员的报告和答案】\n"

        reports_for_log = []
        for i, res in enumerate(parallel_results):
            synthesis_prompt_content += f"\n--- 研究员 {i + 1} (状态: {res.get('termination', 'unknown')}) ---\n"
            synthesis_prompt_content += f"【研究员 {i + 1} 的答案】\n{res.get('prediction', 'N/A')}\n"
            synthesis_prompt_content += f"【研究员 {i + 1} 的最终报告】\n{res.get('report', 'N/A')}\n"
            
            reports_for_log.append({
                "agent": i + 1,
                "answer": res.get('prediction'),
                "report": res.get('report'),
                "termination": res.get('termination')
            })

        synthesis_messages = [
            {
                "role": "system",
                "content": (
                    "你是一个顶级的【首席研究员】，负责综合多个研究员的发现。\n"
                    "你的任务是审查来自多个并行研究员的报告和答案，然后综合所有信息，"
                    "得出一个唯一的、最准确、最全面的最终答案。\n\n"
                    "工作流程：\n"
                    "1. 交叉验证：比较不同报告中的事实和结论，识别一致性和差异。\n"
                    "2. 解决冲突：如果报告冲突，请根据证据质量和逻辑严密性做出最佳判断。\n"
                    "3. 综合提炼：不要只选择一个答案，要整合所有报告中的有效信息，形成一个更优的答案。\n"
                    "4. 质量优先：优先采纳逻辑清晰、证据充分的结论。\n\n"
                    "输出要求：\n"
                    "- 只输出最终答案，不要讨论你的综合过程\n"
                    "- 答案要准确、简洁、有据可查"
                )
            },
            {"role": "user", "content": synthesis_prompt_content}
        ]

        # Create synthesis agent (low temperature for stability)
        synthesis_llm_config = self.llm_config.copy()
        synthesis_llm_config["generate_cfg"] = synthesis_llm_config.get("generate_cfg", {}).copy()
        synthesis_llm_config["generate_cfg"]["temperature"] = 0.2

        synthesis_agent = WebResearcherAgent(
            llm_config=synthesis_llm_config,
            function_list=[],  # Synthesis agent doesn't need tools
        )

        # Call LLM for synthesis
        logger.debug("Calling synthesis LLM...")
        response = await synthesis_agent.call_server(
            synthesis_messages,
            stop_sequences=[]  # No tool stop tokens needed
        )
        # call_server 返回 Dict，包含 content、reasoning_content 等
        final_answer_text = response.get("content", "") if isinstance(response, dict) else str(response)

        logger.debug("Synthesis Complete")
        return {
            "final_answer": final_answer_text.strip(),
            "synthesis_reports": reports_for_log
        }

    async def run(
        self,
        question: str,
        ground_truth: Optional[str] = None,
        num_parallel_agents: int = 3
    ) -> Dict:
        """
        Main entry point for Test-Time Scaling.
        
        Args:
            question: Research question
            ground_truth: Ground truth answer (optional, for evaluation)
            num_parallel_agents: Number of parallel agents (default: 3)
            
        Returns:
            Dict containing:
                - question: Original question
                - ground_truth: Ground truth (if provided)
                - final_synthesized_answer: Final synthesized answer
                - parallel_runs: All parallel agent results
                - synthesis_inputs: Reports used for synthesis
        """
        logger.debug(f"Starting Test-Time Scaling for: {question[:100]}...")
        
        # Phase 1: Parallel Research
        parallel_results = await self.run_parallel_research(question, num_parallel_agents)

        # Phase 2: Integrative Synthesis
        synthesis_result = await self.run_synthesis(question, parallel_results)

        return {
            "question": question,
            "ground_truth": ground_truth,
            "final_synthesized_answer": synthesis_result["final_answer"],
            "parallel_runs": parallel_results,
            "synthesis_inputs": synthesis_result["synthesis_reports"]
        }

