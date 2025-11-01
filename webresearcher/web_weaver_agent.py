# -*- coding: utf-8 -*-
"""
@author:XuMing(xuming624@qq.com)
@description: WebWeaver Agent - Dual-Agent Research Framework with Dynamic Outline
"""
import json5
import os
import re
import datetime
import asyncio
import random
import time
import json

from typing import Dict, List, Optional, Set
from openai import OpenAI, APIError, APIConnectionError, APITimeoutError

from webresearcher.base import Message, BaseTool
from webresearcher.log import logger
from webresearcher.prompt import get_webweaver_planner_prompt, get_webweaver_writer_prompt
from webresearcher.tool_memory import MemoryBank, RetrieveTool
from webresearcher.tool_planner_search import PlannerSearchTool
from webresearcher.tool_planner_scholar import PlannerScholarTool
from webresearcher.tool_planner_visit import PlannerVisitTool
from webresearcher.tool_planner_python import PlannerPythonTool
from webresearcher.tool_planner_file import PlannerFileTool
from webresearcher.config import (
    OPENAI_API_KEY, 
    OPENAI_BASE_URL, 
    OBS_START, 
    OBS_END, 
    MAX_LLM_CALL_PER_RUN, 
    AGENT_TIMEOUT, 
    FILE_DIR
)


def today_date():
    """Get today's date in YYYY-MM-DD format."""
    return datetime.date.today().strftime("%Y-%m-%d")


class BaseWebWeaverAgent:
    """
    Base class for WebWeaver agents (Planner and Writer).
    Handles common LLM calling and tool execution logic.
    """

    def __init__(self, llm_config: Dict, tool_map: Dict[str, BaseTool]):
        """
        Initialize base agent with LLM config and tools.
        
        Args:
            llm_config: LLM configuration dict
            tool_map: Dictionary mapping tool names to BaseTool instances
        """
        self.llm_config = llm_config
        self.llm_generate_cfg = self.llm_config.get("generate_cfg", {})
        self.model = self.llm_config.get("model", "gpt-4o")
        self.llm_timeout = self.llm_config.get("llm_timeout", 300.0)
        self.tool_map = tool_map
        self.function_list = list(tool_map.keys())
        self.openai_api_key = self.llm_config.get("openai_api_key", OPENAI_API_KEY)
        self.openai_base_url = self.llm_config.get("openai_base_url", OPENAI_BASE_URL)
        self.client = OpenAI(
            api_key=self.openai_api_key,
            base_url=self.openai_base_url,
            timeout=self.llm_timeout,
        )
        # Cache for idempotent tool calls to avoid redundant executions (e.g., repeated retrieve on same IDs)
        # Tools listed here will be cached by (tool_name, normalized_args)
        self.cacheable_tools = set(llm_config.get("cacheable_tools", ["retrieve"]))
        self.tool_call_cache: Dict[str, str] = {}

    async def call_server(self, msgs: List[Dict], stop_sequences: List[str] = None,
                          max_tries: int = 1) -> str:
        """
        Async LLM API call with retry logic.
        
        Args:
            msgs: List of message dicts
            stop_sequences: Optional stop sequences
            max_tries: Maximum retry attempts
            
        Returns:
            LLM response content
        """
        base_sleep_time = 1
        loop = asyncio.get_event_loop()
        stop_sequences = stop_sequences or [OBS_START]

        for attempt in range(max_tries):
            try:
                request_params = {
                    "model": self.model,
                    "messages": msgs,
                    "stop": stop_sequences,
                    "temperature": self.llm_generate_cfg.get('temperature', 0.1),
                    "top_p": self.llm_generate_cfg.get('top_p', 0.95),
                }
                model_thinking_type = self.llm_generate_cfg.get("model_thinking_type", "")
                if model_thinking_type:
                    request_params["extra_body"] = {
                        "thinking": {
                            "type": model_thinking_type,
                        }
                    }
                
                # Run in executor to handle sync OpenAI client
                chat_response = await loop.run_in_executor(
                    None,
                    lambda: self.client.chat.completions.create(**request_params)
                )
                
                content = chat_response.choices[0].message.content
                reasoning_content = None
                if hasattr(chat_response.choices[0].message, 'reasoning_content') and chat_response.choices[
                    0].message.reasoning_content:
                    reasoning_content = chat_response.choices[0].message.reasoning_content
                    content = f"<reasoning>{reasoning_content}</reasoning>\n{content}"
                # logger.debug(f"input messages: {msgs}, \nLLM Response: {content}")
                if content and content.strip():
                    return content.strip()
                else:
                    logger.warning(f"Attempt {attempt + 1}: Empty response received.")

            except (APIError, APIConnectionError, APITimeoutError) as e:
                logger.warning(
                    f"Attempt {attempt + 1} API error: {e}, base_url: {self.openai_base_url}, api_key: {self.openai_api_key}, model: {self.model}")
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} unexpected error: {e}")

            if attempt < max_tries - 1:
                sleep_time = base_sleep_time * (2 ** attempt) + random.uniform(0, 1)
                sleep_time = min(sleep_time, 30)
                logger.warning(f"Retrying in {sleep_time:.2f}s...")
                await asyncio.sleep(sleep_time)
            else:
                logger.error("All retry attempts exhausted.")

        return "Error: LLM server failed after all retries."

    async def call_tool(self, tool_call_str: str) -> str:
        """
        Async tool execution with sync/async handling.
        
        Args:
            tool_call_str: JSON string with tool call info
            
        Returns:
            Tool execution result
        """
        loop = asyncio.get_event_loop()
        
        try:
            tool_call = json5.loads(tool_call_str)
            tool_name = tool_call.get('name')
            tool_args = tool_call.get('arguments', {})

            if tool_name not in self.tool_map:
                return f"Error: Tool '{tool_name}' not found in agent's tool map."

            # Auto-fix common LLM mistakes: convert string to array for query/url/files parameters
            if tool_name in ['search', 'google_scholar'] and 'query' in tool_args:
                if isinstance(tool_args['query'], str):
                    tool_args['query'] = [tool_args['query']]
            elif tool_name == 'visit' and 'url' in tool_args:
                if isinstance(tool_args['url'], str):
                    tool_args['url'] = [tool_args['url']]
            elif tool_name == 'parse_file' and 'files' in tool_args:
                if isinstance(tool_args['files'], str):
                    tool_args['files'] = [tool_args['files']]

            # Cache check for idempotent tools (e.g., 'retrieve')
            cache_key = None
            if tool_name in self.cacheable_tools:
                try:
                    # Normalize args to a deterministic JSON string as cache key
                    cache_key = f"{tool_name}::" + json.dumps(tool_args, sort_keys=True, ensure_ascii=False)
                    if cache_key in self.tool_call_cache:
                        logger.debug(f"Cache hit for tool '{tool_name}' with identical arguments. Skipping execution.")
                        return self.tool_call_cache[cache_key]
                except Exception as _:
                    # Fallback: if normalization fails, proceed without cache
                    cache_key = None

            tool = self.tool_map[tool_name]

            # Handle async vs sync tools
            if asyncio.iscoroutinefunction(tool.call):
                result = await tool.call(tool_args)
            else:
                result = await loop.run_in_executor(None, tool.call, tool_args)

            result_str = str(result) if not isinstance(result, str) else result

            # Store in cache if applicable
            if cache_key is not None:
                self.tool_call_cache[cache_key] = result_str

            return result_str

        except Exception as e:
            logger.error(f"Tool call failed: {e}")
            return f"Error: Tool call failed. Input: {tool_call_str}. Error: {e}"


class WebWeaverPlanner(BaseWebWeaverAgent):
    """
    Planner Agent for WebWeaver.
    
    Goal: Iteratively search and optimize a research outline.
    Actions: search, write_outline, terminate.
    
    Based on WebWeaver paper Section 3.2 and Appendix B.2.
    """

    def __init__(self, llm_config: Dict, memory_bank: MemoryBank, function_list: Optional[List[str]] = None, instruction: str = ""):
        """
        Initialize Planner agent.
        
        Args:
            llm_config: LLM configuration
            memory_bank: Shared MemoryBank instance
        """
        # Planner's tool set - all 5 common tools like WebResearcher
        full_tool_map = {
            "search": PlannerSearchTool(memory_bank),
            "google_scholar": PlannerScholarTool(memory_bank),
            "visit": PlannerVisitTool(memory_bank),
            "python": PlannerPythonTool(memory_bank),
            "parse_file": PlannerFileTool(memory_bank),
        }
        tool_map = {k: v for k, v in full_tool_map.items() if not function_list or k in function_list} or full_tool_map

        super().__init__(llm_config, tool_map)
        self.memory_bank = memory_bank
        self.system_prompt = get_webweaver_planner_prompt(today_date(), self.function_list, instruction)

    def parse_output(self, text: str) -> Dict[str, str]:
        """
        Parse Planner's output: <think> and (<tool_call> | <write_outline> | <terminate>).
        
        Args:
            text: Raw LLM output
            
        Returns:
            Dict with 'think', 'action_type', and 'action_content'
        """
        think_match = re.search(r'<think>(.*?)</think>', text, re.DOTALL)
        think = think_match.group(1).strip() if think_match else ""

        tool_call_match = re.search(r'<tool_call>(.*?)</tool_call>', text, re.DOTALL)
        write_outline_match = re.search(r'<write_outline>(.*?)</write_outline>', text, re.DOTALL)
        terminate_match = re.search(r'<terminate>', text, re.DOTALL)

        action_type = None
        action_content = ""

        if terminate_match:
            action_type = "terminate"
        elif write_outline_match:
            action_type = "write_outline"
            action_content = write_outline_match.group(1).strip()
        elif tool_call_match:
            action_type = "tool_call"
            action_content = tool_call_match.group(1).strip()
        else:
            action_type = "error"
            action_content = "No valid action tag found. Must use <tool_call>, <write_outline>, or <terminate>."
            logger.warning(f"Planner output parsing error: {action_content}")

        return {
            "think": think,
            "action_type": action_type,
            "action_content": action_content
        }

    async def run(self, question: str) -> str:
        """
        Execute Planner's research loop.
        
        Args:
            question: Research question
            
        Returns:
            Final outline string
        """
        logger.debug("--- [WebWeaver] Planner Agent activated ---")

        current_outline = "Outline is empty. Start by searching for information."
        last_observation = "No observation yet."

        for i in range(MAX_LLM_CALL_PER_RUN):
            # Build Planner context
            context_str = (
                f"[Question]\n{question}\n\n"
                f"[Current Outline]\n{current_outline}\n\n"
                f"[Last Observation]\n{last_observation}\n\n"
                f"**IMPORTANT: When you write the outline using <write_outline>, "
                f"you MUST use the SAME LANGUAGE as the [Question] above. Do NOT translate.**"
            )
            # Final iteration: force LLM to output <write_outline> and avoid tool calls or terminate
            is_last_iteration = (i == MAX_LLM_CALL_PER_RUN - 1)
            if is_last_iteration:
                context_str += (
                    "\n[Final Instruction]\n"
                    "This is your last allowed step. You MUST output <write_outline> with the complete final outline. "
                    "Do NOT output <tool_call> or <terminate>."
                )
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": context_str}
            ]

            # Call LLM
            response_content = await self.call_server(messages)
            
            # Parse action
            parsed = self.parse_output(response_content)
            logger.debug(f"Planner Step {i + 1} | Action: {parsed}")

            # Execute action
            if parsed['action_type'] == "terminate":
                logger.debug("Planner finished. Terminating.")
                return current_outline

            elif parsed['action_type'] == "write_outline":
                current_outline = parsed['action_content']
                last_observation = "Outline successfully updated."
                logger.debug(f"Planner Step {i + 1}: Outline updated.")

            elif parsed['action_type'] == "tool_call":
                tool_call_str = parsed['action_content']
                last_observation = await self.call_tool(tool_call_str)
                logger.debug(f"Planner Step {i + 1}: Tool executed.")

            elif parsed['action_type'] == "error":
                last_observation = parsed['action_content']
                logger.warning(f"Planner Step {i + 1}: Action parse error.")

        logger.warning("Planner reached max iterations.")
        return current_outline


class WebWeaverWriter(BaseWebWeaverAgent):
    """
    Writer Agent for WebWeaver.
    
    Goal: Write report section-by-section based on Planner's outline and memory bank.
    Actions: retrieve, write, terminate.
    
    Based on WebWeaver paper Section 3.3 and Appendix B.3.
    """

    def __init__(self, llm_config: Dict, memory_bank: MemoryBank, instruction: str = ""):
        """
        Initialize Writer agent.
        
        Args:
            llm_config: LLM configuration
            memory_bank: Shared MemoryBank instance
        """
        # Writer only needs retrieve tool
        tool_map = {
            "retrieve": RetrieveTool(memory_bank),
        }

        super().__init__(llm_config, tool_map)
        self.memory_bank = memory_bank
        self.system_prompt = get_webweaver_writer_prompt(today_date(), instruction)

    def parse_output(self, text: str) -> Dict[str, str]:
        """
        Parse Writer's output: <think> and (<tool_call> | <write> | <terminate>).
        
        Args:
            text: Raw LLM output
            
        Returns:
            Dict with 'think', 'action_type', and 'action_content'
        """
        think_match = re.search(r'<think>(.*?)</think>', text, re.DOTALL)
        think = think_match.group(1).strip() if think_match else ""

        tool_call_match = re.search(r'<tool_call>(.*?)</tool_call>', text, re.DOTALL)
        write_match = re.search(r'<write>(.*?)</write>', text, re.DOTALL)
        terminate_match = re.search(r'<terminate>', text, re.DOTALL)

        action_type = None
        action_content = ""

        if terminate_match:
            action_type = "terminate"
        elif write_match:
            action_type = "write"
            action_content = write_match.group(1).strip()
        elif tool_call_match:
            action_type = "tool_call"
            action_content = tool_call_match.group(1).strip()
        else:
            action_type = "error"
            action_content = "No valid action tag found. Must use <tool_call> (retrieve), <write>, or <terminate>."
            logger.warning(f"Writer output parsing error: {action_content}")

        return {
            "think": think,
            "action_type": action_type,
            "action_content": action_content
        }

    async def run(self, question: str, final_outline: str) -> str:
        """
        Execute Writer's writing loop.
        
        Args:
            question: Research question
            final_outline: Final outline from Planner
            
        Returns:
            Final report string
        """
        logger.debug("--- [WebWeaver] Writer Agent activated ---")

        report_written_so_far = ""
        last_observation = "No observation yet. Start by retrieving evidence for the first section."
        # Track retrieve calls to avoid redundant tool executions for identical arguments
        seen_retrieve_keys: Set[str] = set()
        retrieve_repeat_counts: Dict[str, int] = {}
        retrieve_results_cache: Dict[str, str] = {}  # Cache actual evidence content
        steps_since_last_write = 0
        # Heuristics
        MAX_IDLE_BEFORE_FORCE_WRITE_HINT = 6   # iterations with no <write> before adding a strong hint
        for i in range(MAX_LLM_CALL_PER_RUN):
            # Build Writer context
            context_str = (
                f"[Question]\n{question}\n\n"
                f"[Final Outline]\n{final_outline}\n\n"
                f"[Report Written So Far]\n{report_written_so_far}\n\n"
                f"[Last Observation]\n{last_observation}\n\n"
                f"**CRITICAL LANGUAGE REQUIREMENT: The report you write using <write> MUST be "
                f"in the SAME LANGUAGE as the [Question] and [Final Outline] above. "
                f"Check the language carefully and DO NOT translate or switch languages.**"
            )
            # Final iteration: force LLM to output <write> and avoid tool calls or terminate
            is_last_iteration = (i == MAX_LLM_CALL_PER_RUN - 1)
            if is_last_iteration:
                context_str += (
                    "\n[Final Instruction]\n"
                    "This is your last allowed step. You MUST output <write> with a well-structured final section using the evidence you have. "
                    "Do NOT output <tool_call> or <terminate>."
                )
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": context_str}
            ]

            # Call LLM
            response_content = await self.call_server(messages)

            # Parse action
            parsed = self.parse_output(response_content)
            logger.debug(f"Writer Step {i + 1} | Action: {parsed}")

            # Execute action
            if parsed['action_type'] == "terminate":
                logger.debug("Writer finished. Terminating.")
                return report_written_so_far

            elif parsed['action_type'] == "write":
                section_prose = parsed['action_content']
                report_written_so_far += "\n\n" + section_prose
                last_observation = f"Section written successfully:\n{section_prose}\n"
                logger.debug(f"Writer Step {i + 1}: Section written.")
                steps_since_last_write = 0

            elif parsed['action_type'] == "tool_call":
                tool_call_str = parsed['action_content']
                # Try to parse tool call to detect identical retrieve arguments
                try:
                    tool_call = json5.loads(tool_call_str)
                    tool_name = tool_call.get('name')
                    tool_args = tool_call.get('arguments', {})
                except Exception:
                    tool_name, tool_args = None, None

                # If it's a retrieve with identical arguments, return cached evidence instead of skipping
                if tool_name == "retrieve":
                    try:
                        key = json.dumps(tool_args, sort_keys=True, ensure_ascii=False)
                    except Exception:
                        key = None

                    if key is not None:
                        if key in seen_retrieve_keys:
                            retrieve_repeat_counts[key] = retrieve_repeat_counts.get(key, 1) + 1
                            logger.debug(
                                f"Writer Step {i + 1}: Returning cached evidence for duplicate retrieve args={key}. "
                                f"repeat={retrieve_repeat_counts[key]}"
                            )
                            # Return the cached evidence content with a strong hint to write
                            cached_evidence = retrieve_results_cache.get(key, "")
                            guidance = (
                                "Evidence for these citation IDs has already been retrieved. "
                                "Here is the evidence again:\n\n"
                                f"{cached_evidence}\n\n"
                                "You MUST now proceed to <write> the section using this evidence. "
                                "Do NOT call <tool_call> retrieve again for the same IDs."
                            )
                            last_observation = guidance
                            steps_since_last_write += 1
                            continue
                        else:
                            seen_retrieve_keys.add(key)

                # Execute tool (will still benefit from Base cache if identical within process)
                last_observation = await self.call_tool(tool_call_str)
                
                # Cache the evidence result for retrieve tool
                if tool_name == "retrieve" and key is not None:
                    retrieve_results_cache[key] = last_observation
                
                logger.debug(f"Writer Step {i + 1}: Evidence retrieved.")
                steps_since_last_write += 1

            elif parsed['action_type'] == "error":
                last_observation = parsed['action_content']
                logger.warning(f"Writer Step {i + 1}: Action parse error.")
                steps_since_last_write += 1

            # If the model is idling without writing for too long, add a strong hint to force progress
            if steps_since_last_write >= MAX_IDLE_BEFORE_FORCE_WRITE_HINT:
                last_observation += (
                    "\nInstruction: You have gathered sufficient evidence. In the next step, "
                    "you MUST output <write> with a well-structured section. Do NOT call <tool_call> unless "
                    "retrieving different, additional evidence explicitly required by the outline."
                )

        logger.warning("Writer reached max iterations.")
        return report_written_so_far


class WebWeaverAgent:
    """
    WebWeaver main orchestrator.
    
    Coordinates Planner and Writer agents in sequence.
    Based on WebWeaver paper dual-agent framework.
    """

    def __init__(
            self,
            llm_config: Optional[Dict] = None,
            function_list: Optional[List[str]] = None,
            instruction: str = "",
            api_key: Optional[str] = None,
            base_url: Optional[str] = None,
    ):
        """
        Initialize WebWeaver agent.
        
        Args:
            llm_config: LLM configuration dict
        """
        base_config = llm_config or {
            "model": "gpt-4o",
            "generate_cfg": {
                "temperature": 0.1,
                "top_p": 0.95,
                "max_tokens": 10000,
            },
            "llm_timeout": 300.0,
        }
        self.llm_config = dict(base_config)
        if api_key:
            self.llm_config["openai_api_key"] = api_key
        if base_url:
            self.llm_config["openai_base_url"] = base_url
        
        # Initialize shared memory bank
        self.memory_bank = MemoryBank()

        # Initialize sub-agents
        self.planner = WebWeaverPlanner(self.llm_config, self.memory_bank, function_list=function_list, instruction=instruction)
        self.writer = WebWeaverWriter(self.llm_config, self.memory_bank, instruction=instruction)

        logger.debug("WebWeaver Dual-Agent Framework initialized.")
        logger.debug(f"Planner Tools: {self.planner.function_list}")
        logger.debug(f"Writer Tools: {self.writer.function_list}")

    async def run(self, question: str) -> Dict[str, str]:
        """
        Execute WebWeaver's complete dual-agent workflow.
        
        Args:
            question: Research question
            
        Returns:
            Dict with final_report, final_outline, and metadata
        """
        start_time = time.time()

        # Phase 1: Run Planner
        # Planner fills memory_bank and returns final outline
        try:
            final_outline = await asyncio.wait_for(
                self.planner.run(question),
                timeout=AGENT_TIMEOUT
            )
            logger.debug("--- Planner Phase Complete ---")
            logger.debug(f"Final Outline:\n{final_outline}")
            logger.debug(f"Memory Bank contains {self.memory_bank.size()} items.")
        except Exception as e:
            logger.error(f"Planner Agent failed: {e}")
            return {
                "question": question,
                "final_report": "",
                "error": f"Planner phase error: {e}"
            }

        # Phase 2: Run Writer
        # Writer uses Planner's output (final_outline, memory_bank)
        try:
            final_report = await asyncio.wait_for(
                self.writer.run(question, final_outline),
                timeout=AGENT_TIMEOUT
            )
            logger.debug("--- Writer Phase Complete ---")
        except Exception as e:
            logger.error(f"Writer Agent failed: {e}")
            return {
                "question": question,
                "final_report": "",
                "error": f"Writer phase error: {e}"
            }

        end_time = time.time()

        return {
            "question": question,
            "final_outline": final_outline,
            "final_report": final_report,
            "memory_bank_size": self.memory_bank.size(),
            "total_time_seconds": end_time - start_time
        }


async def main():
    """Main function for testing WebWeaver agent."""
    from webresearcher.log import set_log_level
    set_log_level("DEBUG")
    
    llm_config = {
        "model": "gpt-4o",
        "generate_cfg": {
            "temperature": 0.1,
            "top_p": 0.95,
            "max_tokens": 10000,
        },
        "llm_timeout": 300.0,
    }
    agent = WebWeaverAgent(llm_config=llm_config)
    print(OPENAI_API_KEY)
    question =  "刘翔破纪录时候是多少岁?"
    result = await agent.run(question)
    print(result)


if __name__ == '__main__':
    asyncio.run(main())
