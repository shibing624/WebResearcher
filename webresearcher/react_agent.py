# -*- coding: utf-8 -*-
"""
@author:XuMing(xuming624@qq.com)
@description: React Agent implementing the MultiTurn ReAct paradigm.
"""
from typing import Dict, List, Optional
import asyncio
import datetime
import json5
import random
import time
import re

from openai import OpenAI, APIError, APIConnectionError, APITimeoutError

from webresearcher.base import Message, build_text_completion_prompt, count_tokens as count_tokens_base
from webresearcher.log import logger
from webresearcher.prompt import get_system_prompt
from webresearcher.tool_file import FileParser
from webresearcher.tool_scholar import Scholar
from webresearcher.tool_python import PythonInterpreter
from webresearcher.tool_search import Search
from webresearcher.tool_visit import Visit
from webresearcher.config import (
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    OBS_START,
    OBS_END,
    MAX_LLM_CALL_PER_RUN,
    FILE_DIR,
)


TOOL_CLASS = [
    FileParser(),
    Scholar(),
    Visit(),
    Search(),
    PythonInterpreter(),
]
TOOL_MAP = {tool.name: tool for tool in TOOL_CLASS}


def today_date():
    return datetime.date.today().strftime("%Y-%m-%d")


class ReactAgent:
    """A lightweight MultiTurn ReAct-style agent compatible with local vLLM or OpenAI endpoints."""

    def __init__(
        self,
        llm_config: Optional[Dict] = None,
        function_list: Optional[List[str]] = None,
        instruction: str = "",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ) -> None:
        llm_config = dict(llm_config or {})
        if api_key:
            llm_config["openai_api_key"] = api_key
        if base_url:
            llm_config["openai_base_url"] = base_url

        self.llm_config = llm_config
        self.model = self.llm_config.get("model", "gpt-4o")
        self.generate_cfg = self.llm_config.get("generate_cfg", {"temperature": 0.6, "top_p": 0.95})
        self.openai_api_key = self.llm_config.get("openai_api_key", OPENAI_API_KEY)
        self.openai_base_url = self.llm_config.get("openai_base_url", OPENAI_BASE_URL)
        self.llm_timeout = self.llm_config.get("llm_timeout", 600.0)

        self.function_list = function_list or list(TOOL_MAP.keys())
        self.instruction = instruction

    def count_tokens(self, messages: List[Dict]) -> int:
        try:
            full_message: List[Message] = []
            for x in messages:
                if isinstance(x, dict):
                    full_message.append(Message(**x))
                else:
                    full_message.append(x)
            full_prompt = build_text_completion_prompt(full_message, allow_special=True)
            return count_tokens_base(full_prompt, self.model)
        except Exception as e:
            logger.warning(f"Failed to count tokens: {e}. Using simple split.")
            return sum(len(str(x).split()) for x in messages)

    async def call_server(self, msgs: List[Dict], stop_sequences: Optional[List[str]] = None, max_tries: int = 5) -> str:
        client = OpenAI(
            api_key=self.openai_api_key or "EMPTY",
            base_url=self.openai_base_url,
            timeout=self.llm_timeout,
        )
        base_sleep_time = 1
        loop = asyncio.get_event_loop()
        stop_sequences = stop_sequences or [OBS_START]

        for attempt in range(max_tries):
            try:
                request_params = {
                    "model": self.model,
                    "messages": msgs,
                    "stop": stop_sequences,
                    "temperature": self.generate_cfg.get("temperature", 0.6),
                    "top_p": self.generate_cfg.get("top_p", 0.95),
                }
                chat_response = await loop.run_in_executor(
                    None,
                    lambda: client.chat.completions.create(**request_params),
                )
                content = chat_response.choices[0].message.content
                reasoning_content = None
                if hasattr(chat_response.choices[0].message, 'reasoning_content') and chat_response.choices[0].message.reasoning_content:
                    reasoning_content = chat_response.choices[0].message.reasoning_content
                logger.debug(f"Input messages: {msgs}, \nReasoning_content: {reasoning_content}, \nLLM Response: {content}")
                if content and content.strip():
                    return content.strip()
                logger.warning(f"Attempt {attempt + 1}: Empty response received.")
            except (APIError, APIConnectionError, APITimeoutError) as e:
                logger.warning(f"Attempt {attempt + 1} API error: {e}")
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} unexpected error: {e}")

            if attempt < max_tries - 1:
                sleep_time = base_sleep_time * (2 ** attempt) + random.uniform(0, 1)
                sleep_time = min(sleep_time, 30)
                logger.warning(f"Retrying in {sleep_time:.2f}s...")
                await asyncio.sleep(sleep_time)
        return "LLM server error."

    @staticmethod
    def _strip_after_tool_response(content: str) -> str:
        if OBS_START in content:
            return content.split(OBS_START, 1)[0].strip()
        return content

    async def _call_tool(self, tool_call_block: str) -> str:
        # Python inline code path
        if "<code>" in tool_call_block and "</code>" in tool_call_block and "python" in tool_call_block.lower():
            code_raw = tool_call_block.split("<code>", 1)[1].split("</code>", 1)[0].strip()
            result = TOOL_MAP["python"].call(code_raw)
            return result if isinstance(result, str) else str(result)

        # JSON tool path
        try:
            tool_call = json5.loads(tool_call_block)
            tool_name = tool_call.get("name", "")
            tool_args = tool_call.get("arguments", {})
        except Exception:
            return 'Error: Tool call is not a valid JSON. Tool call must contain a valid "name" and "arguments" field.'

        if tool_name not in TOOL_MAP:
            return f"Error: Tool {tool_name} not found"

        tool = TOOL_MAP[tool_name]
        # handle async tool (parse_file) with file root
        try:
            if asyncio.iscoroutinefunction(tool.call):
                if tool_name == "parse_file":
                    params = {"files": tool_args.get("files")}
                    result = await tool.call(params, file_root_path=FILE_DIR)
                else:
                    result = await tool.call(tool_args)
            else:
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, tool.call, tool_args)
            return result if isinstance(result, str) else str(result)
        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            return f"Error: Tool execution failed. {e}"

    def _parse_answer(self, content: str) -> Dict[str, Optional[str]]:
        ans = {
            "answer": None,
            "terminate": False,
        }
        # Prefer <answer> as a termination signal; if both exist, <answer> wins
        answer_match = re.search(r"<answer>(.*?)</answer>", content, re.DOTALL)
        if answer_match:
            ans["answer"] = answer_match.group(1).strip()
            ans["terminate"] = True  # Treat <answer> as a terminate signal
            return ans
        term_match = re.search(r"<terminate>(.*?)</terminate>", content, re.DOTALL)
        if term_match:
            ans["terminate"] = True
            body = term_match.group(1)
            if body:
                ans["answer"] = body.strip()
        return ans

    async def run(self, question: str) -> Dict[str, str]:
        # Build system prompt with tool schemas and task-specific instruction handled inside prompt.py
        system_prompt = get_system_prompt(today_date(), self.function_list, self.instruction)
        messages: List[Dict] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ]

        start_time = time.time()
        remaining = MAX_LLM_CALL_PER_RUN

        while remaining > 0:
            if time.time() - start_time > self.llm_timeout:
                best_effort = "Final answer generated by agent (timeout)."
                return {
                    "question": question,
                    "prediction": best_effort,
                    "termination": "timeout",
                    "trajectory": messages,
                }

            remaining -= 1
            content = await self.call_server(messages)
            content = self._strip_after_tool_response(content)

            # tool call path: normalize assistant message to only include the <tool_call> block to avoid verbose assistant chatter
            if "<tool_call>" in content and "</tool_call>" in content:
                tool_block = content.split("<tool_call>", 1)[1].split("</tool_call>", 1)[0]
                # Execute tool
                tool_result = await self._call_tool(tool_block)
                logger.debug(f"Tool result: {tool_result}")
                # Combine <tool_call> and tool response into a single 'user' message to avoid consecutive assistant entries
                messages.append({
                    "role": "user",
                    "content": (
                        f"<tool_call>\n{tool_block}\n</tool_call>\n"
                        f"{OBS_START}\n{tool_result}\n{OBS_END}"
                    )
                })
                continue

            # normal assistant response path (no tool call)
            messages.append({"role": "assistant", "content": content})

            # termination path
            final = self._parse_answer(content)
            logger.debug(f"Final answer: {final}")
            if final["answer"]:
                return {
                    "question": question,
                    "prediction": final["answer"],
                    "termination": "terminated with answer",
                    "trajectory": messages,
                }
            if final["terminate"]:
                # Ensure a non-empty best-effort prediction even if terminate has no body
                best_effort = content.strip() or "Final answer generated by agent."
                return {
                    "question": question,
                    "prediction": best_effort,
                    "termination": "terminated without answer",
                    "trajectory": messages,
                }
            
            # If no termination, prompt the agent to continue or provide final answer
            messages.append({
                "role": "user",
                "content": "Please continue your analysis or provide the final answer using <answer> tags."
            })

            # last round fallback: ask explicitly for final answer
            if remaining == 0:
                forced_prompt = (
                    "You have reached the limit. Stop tool calls. Provide the final response using "
                    "<answer> only. Do NOT include <tool_call> or <think>."
                )
                # Echo task-specific instruction to maximize adherence in the final call
                if self.instruction:
                    forced_prompt = (
                        f"{forced_prompt}\n\nRemember the task-specific instruction and follow it strictly:\n{self.instruction}"
                    )
                messages.append({"role": "user", "content": forced_prompt})
                content = await self.call_server(messages)
                messages.append({"role": "assistant", "content": content})
                final = self._parse_answer(content)
                if final["answer"]:
                    return {
                        "question": question,
                        "prediction": final["answer"],
                        "termination": "terminated with answer (forced)",
                        "trajectory": messages,
                    }
                # No <answer> tag: use LLM text as final prediction to avoid empty/No answer
                fallback_text = content.strip()
                return {
                    "question": question,
                    "prediction": fallback_text or "Final answer generated by agent.",
                    "termination": "finalized without answer tag",
                    "trajectory": messages,
                }

        # Exhausted available LLM calls: perform a final forced answer call before returning
        forced_prompt = (
            "You have reached the limit. Stop tool calls. Provide the final response using "
            "<answer> only. Do NOT include <tool_call> or <think>."
        )
        if self.instruction:
            forced_prompt = (
                f"{forced_prompt}\n\nRemember the task-specific instruction and follow it strictly:\n{self.instruction}"
            )
        messages.append({"role": "user", "content": forced_prompt})
        content = await self.call_server(messages)
        messages.append({"role": "assistant", "content": content})
        final = self._parse_answer(content)
        if final["answer"]:
            return {
                "question": question,
                "prediction": final["answer"],
                "termination": "terminated with answer (forced)",
                "trajectory": messages,
            }
        fallback_text = content.strip()
        return {
            "question": question,
            "prediction": fallback_text or "Final answer generated by agent.",
            "termination": "exceed available llm calls (finalized without answer tag)",
            "trajectory": messages,
        }

async def main():
    agent = ReactAgent()
    result = await agent.run("What is the capital of France?")
    print(result)

if __name__ == "__main__":
    asyncio.run(main())