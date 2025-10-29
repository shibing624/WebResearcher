import json5
import os
import re
import datetime
import asyncio
import random
import time

from typing import Dict, List, Optional
from openai import OpenAI, APIError, APIConnectionError, APITimeoutError

from webresearcher.base import Message, build_text_completion_prompt, count_tokens as count_tokens_base
from webresearcher.log import logger
from webresearcher.prompt import get_iterresearch_system_prompt
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
    AGENT_TIMEOUT, 
    FILE_DIR
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


class ResearchRound:
    """
    实现了 IterResearch 范式的核心状态管理器。
    
    状态只包含用于构建下一个提示的核心信息：
    - question (Q): 原始问题
    - current_report (R_{i-1}): 上一轮生成的报告
    - last_observation (O_{i-1}): 上一轮工具调用的结果
    """

    def __init__(self, question: str):
        self.question = question

        # R_{i-1}: 上一轮生成的报告，初始为空
        self.current_report = "This is the first round. The report is empty."

        # O_{i-1}: 上一轮工具调用的结果，初始为空
        self.last_observation = "This is the first round. No tool has been called yet."

    def get_context(self, system_prompt: str) -> List[Dict]:
        """
        构建当前轮次的精简上下文。
        这代表了论文中的 Workspace，即状态 s_t = (Q, R_{i-1}, O_{i-1})
        """
        user_content = (
            f"**Question:** {self.question}\n\n"
            f"**Current Report (R_{{i-1}}):**\n{self.current_report}\n\n"
            f"**Last Observation (O_{{i-1}}):**\n{self.last_observation}"
        )

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]


class WebResearcherAgent:
    """
    Web Research Agent implementing the IterResearch paradigm.
    
    The IterResearch paradigm uses a cyclical process of:
    1. Workspace (question + previous report + last tool result)
    2. Think-Action (LLM generates reasoning and action)
    3. Tool Execution (execute the tool and get result)
    4. Synthesis (update report by integrating new information)
    
    This agent is fully independent and does not inherit from external frameworks.
    """

    def __init__(
            self,
            llm_config: Optional[Dict] = None,
            function_list: Optional[List[str]] = None,
    ):
        self.llm_generate_cfg = llm_config.get("generate_cfg", {})
        self.model = llm_config.get("model", "gpt-4o")  # 主模型
        self.max_input_tokens = llm_config.get("max_input_tokens", 32000)
        self.llm_timeout = llm_config.get("llm_timeout", 300.0)
        self.agent_timeout = llm_config.get("agent_timeout", 600.0)
        self.function_list = function_list or list(TOOL_MAP.keys())

    def parse_output(self, text: str) -> Dict[str, str]:
        """
        解析 LLM 的单次输出，严格提取 <think>, <report>, 和 (<tool_call> 或 <answer>)。
        这是 IterResearch 范式的核心：LLM 在单次调用中生成三段式输出。
        """
        output = {
            "think": "",
            "report": "",
            "tool_call": "",
            "answer": ""
        }

        # 1. 提取 <think>
        think_match = re.search(r'<think>(.*?)</think>', text, re.DOTALL)
        if think_match:
            output["think"] = think_match.group(1).strip()

        # 2. 提取 <report>
        report_match = re.search(r'<report>(.*?)</report>', text, re.DOTALL)
        if report_match:
            output["report"] = report_match.group(1).strip()

        # 3. 提取 <tool_call> 或 <answer>
        tool_call_match = re.search(r'<tool_call>(.*?)</tool_call>', text, re.DOTALL)
        answer_matches = re.findall(r'<answer>(.*?)</answer>', text, re.DOTALL)
        if answer_matches:
            answer_str = "\n".join([match.strip() for match in answer_matches if match.strip()])
            answer_str = answer_str.strip()
        else:
            answer_str = None

        if tool_call_match:
            tool_call_content = tool_call_match.group(1).strip()
            # 处理 Python 代码块的特殊格式
            if "python\n<code>" in tool_call_content or "<code>" in tool_call_content:
                output["tool_call"] = tool_call_content
            else:
                output["tool_call"] = tool_call_content
        elif answer_str:
            output["answer"] = answer_str
        else:
            logger.warning("LLM output did not contain <tool_call> or <answer> tag.")

        return output

    async def call_server(self, msgs: List[Dict], stop_sequences: List[str] = None,
                          max_tries: int = 1) -> str:
        """异步方法，并使用 run_in_executor 处理同步的 OpenAI 库"""
        client = OpenAI(
            api_key=OPENAI_API_KEY,
            base_url=OPENAI_BASE_URL,
            timeout=self.llm_timeout,
        )

        base_sleep_time = 1
        loop = asyncio.get_event_loop()

        stop_sequences = stop_sequences or ["<tool_response>"]

        for attempt in range(max_tries):
            try:
                request_params = {
                    "model": self.model,
                    "messages": msgs,
                    "stop": stop_sequences,
                    "temperature": self.llm_generate_cfg.get('temperature', 0.6),
                    "top_p": self.llm_generate_cfg.get('top_p', 0.95),
                    "max_tokens": 10000,
                    "presence_penalty": self.llm_generate_cfg.get('presence_penalty', 1.1)
                }
                model_thinking_type = self.llm_generate_cfg.get("model_thinking_type", "")
                if model_thinking_type:
                    request_params["extra_body"] = {
                        "thinking": {
                            "type": model_thinking_type,
                        }
                    }
                # [关键] 使用 run_in_executor 在线程池中运行同步的 blocking I/O
                chat_response = await loop.run_in_executor(
                    None,  # 使用默认的 ThreadPoolExecutor
                    lambda: client.chat.completions.create(**request_params)
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
                    f"Attempt {attempt + 1} API error: {e}, base_url: {OPENAI_BASE_URL}, api_key: {OPENAI_API_KEY}, model: {self.model}")
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} unexpected error: {e}")

            if attempt < max_tries - 1:
                sleep_time = base_sleep_time * (2 ** attempt) + random.uniform(0, 1)
                sleep_time = min(sleep_time, 30)
                logger.warning(f"Retrying in {sleep_time:.2f}s...")
                await asyncio.sleep(sleep_time)  # [关键] 使用 await asyncio.sleep
            else:
                logger.error("All retry attempts exhausted. The LLM call failed.")
        return "LLM server error."

    def count_tokens(self, messages, model="gpt-4o"):
        """Count tokens in messages"""
        try:
            # Convert dict messages to Message objects if needed
            full_message = []
            for x in messages:
                if isinstance(x, dict):
                    full_message.append(Message(**x))
                elif isinstance(x, Message):
                    full_message.append(x)
                else:
                    full_message.append(x)

            full_prompt = build_text_completion_prompt(full_message, allow_special=True)
            return count_tokens_base(full_prompt, model)
        except Exception as e:
            logger.warning(f"Failed to count tokens: {e}. Using simple split.")
            return sum(len(str(x).split()) for x in messages)

    async def custom_call_tool(self, tool_call_str: str) -> str:
        """async方法，并正确处理同步/异步工具"""
        loop = asyncio.get_event_loop()

        try:
            # 1. 优先检查是否包含 <code> 标签（处理 Python 代码）
            # 支持多种格式：
            # - python\n<code>...</code>
            # - <code>...</code>
            # - {"name": "python", ...}\n<code>...</code>
            if "<code>" in tool_call_str and "</code>" in tool_call_str:
                code_raw = tool_call_str.split("<code>", 1)[1].rsplit("</code>", 1)[0].strip()
                result = await loop.run_in_executor(None, TOOL_MAP['python'].call, code_raw)
                return result

            # 2. 处理 JSON 工具调用
            tool_call = json5.loads(tool_call_str)
            tool_name = tool_call.get('name', '')
            tool_args = tool_call.get('arguments', {})

            if tool_name not in TOOL_MAP:
                return f"Error: Tool {tool_name} not found"

            tool = TOOL_MAP[tool_name]

            # 3. [关键] 区分同步和异步工具
            if asyncio.iscoroutinefunction(tool.call):
                # 如果工具本身是 async (例如 FileParser)
                if tool_name == "parse_file":
                    params = {"files": tool_args.get("files")}
                    result = await tool.call(params, file_root_path=FILE_DIR)
                else:
                    result = await tool.call(tool_args)  # 假设其他 async 工具
            else:
                # 如果工具是 sync (例如 Search, Visit, Scholar)
                # 在 executor 中运行
                result = await loop.run_in_executor(None, tool.call, tool_args)

            return str(result) if not isinstance(result, str) else result

        except Exception as e:
            logger.error(f"Tool call parsing or execution failed: {e}")
            return f"Error: Tool call failed. Input: {tool_call_str}. Error: {e}"

    async def run(self, question):
        """
        严格按照 IterResearch 范式执行研究（单 LLM 调用）。
        
        循环如下:
        s_t = (Q, R_{i-1}, O_{i-1})
        LLM(s_t) -> (Think_i, Report_i, Action_i)
        
        if Action_i == <answer>:
            STOP
        else:
            O_i = Tool(Action_i)
            s_{t+1} = (Q, R_i, O_i)
            LOOP
        """
        start_time = time.time()

        # 1. 初始化研究轮次
        research_round = ResearchRound(question=question)
        system_prompt = get_iterresearch_system_prompt(today_date(), self.function_list)

        # 完整轨迹日志（用于调试）
        full_trajectory_log = []
        prediction = ''
        termination = ''

        num_llm_calls_available = MAX_LLM_CALL_PER_RUN
        round_num = 0

        while num_llm_calls_available > 0:
            if time.time() - start_time > self.agent_timeout:
                logger.warning("Agent timeout reached.")
                termination = "timeout"
                prediction = "No answer found (timeout)."
                break

            round_num += 1
            num_llm_calls_available -= 1

            # 2. 构建提示 (s_t = Q, R_{i-1}, O_{i-1})
            current_context = research_round.get_context(system_prompt)

            if round_num == 1:
                full_trajectory_log.extend(current_context)  # 仅记录初始上下文

            # 3. 单次 LLM 调用 (生成 T_i, R_i, A_i)
            content = ''
            try:
                logger.debug(f"Round {round_num}: Calling LLM. Remaining calls: {num_llm_calls_available}")
                content = await self.call_server(current_context)

                full_trajectory_log.append({"role": "assistant", "content": content})
                logger.debug(f'Round {round_num} LLM response received.')

            except (APIError, APIConnectionError, APITimeoutError) as e:
                logger.error(f"API Error: {e}")
                prediction = f"Error: API Error {e}"
                termination = 'api error'
                break
            except Exception as e:
                logger.error(f"Unknown Error: {e}")
                prediction = f"Error: Unknown {e}"
                termination = 'unknown error'
                break

            # 4. 解析 LLM 的结构化输出 (T_i, R_i, A_i / Answer_i)
            parsed = self.parse_output(content)
            think_content = parsed["think"]
            report_content = parsed["report"]
            action_content = parsed["tool_call"]
            answer_content = parsed["answer"]

            logger.debug(f"Round {round_num} - Think: {think_content}")
            logger.debug(f"Round {round_num} - Report: {report_content}")
            logger.debug(f"Round {round_num} - Action: {action_content}")
            logger.debug(f"Round {round_num} - Answer: {answer_content}")

            # 5. 状态更新 (s_t -> s_{t+1})

            # 5.1 更新报告 (R_i)
            # 无论 LLM 接下来是调用工具还是回答，它都必须生成一份新报告。
            # 这份新报告 R_i 将用于 s_{t+1}
            if report_content:
                research_round.current_report = report_content
            else:
                # 如果LLM没有生成新报告，我们沿用上一轮的报告
                logger.warning("No <report> found. Report will not be updated for the next round.")

            # 5.2 检查是否终止
            if answer_content:
                prediction = answer_content
                termination = 'answer found'
                logger.debug(f"Round {round_num}: LLM provided <answer>. Terminating loop.")
                break

            # 5.3 执行 Action (A_i)
            if action_content:
                try:
                    logger.debug(f"Round {round_num}: Executing tool...")
                    tool_response_str = await self.custom_call_tool(action_content)

                    # 将工具响应 O_i 存储，用于下一轮 s_{t+1}
                    research_round.last_observation = tool_response_str

                    # 记录工具响应到完整日志
                    tool_obs_msg = f"{OBS_START}\n{tool_response_str}\n{OBS_END}"
                    full_trajectory_log.append({"role": "user", "content": tool_obs_msg})

                    logger.debug(f"Round {round_num}: Tool execution completed.")

                except Exception as e:
                    logger.error(f"Error calling tool: {e}")
                    error_str = f"Error executing tool: {e}"
                    research_round.last_observation = error_str
                    full_trajectory_log.append({"role": "user", "content": f"{OBS_START}\n{error_str}\n{OBS_END}"})
            else:
                # LLM 既没有回答也没有调用工具
                logger.warning("LLM did not produce <answer> or <tool_call>. Forcing answer generation...")

                # 强制生成答案
                force_answer_msgs = current_context + [
                    {"role": "user", "content": (
                        "You did not provide a valid response format. "
                        "Based on your current report and the information gathered so far, "
                        "please provide the final answer to the original question. "
                        "Use the three-part format: <think>...</think> <report>...</report> <answer>...</answer>"
                    )}
                ]

                try:
                    forced_content = await self.call_server(force_answer_msgs)
                    forced_parsed = self.parse_output(forced_content)

                    if forced_parsed["answer"]:
                        prediction = forced_parsed["answer"]
                        termination = "answer (forced)"
                        full_trajectory_log.append({"role": "assistant", "content": forced_content})
                        break
                    else:
                        logger.error("Failed to force answer generation")
                        prediction = "No answer found (format error after retry)."
                        termination = "format error"
                        break
                except Exception as e:
                    logger.error(f"Error during forced answer generation: {e}")
                    prediction = "No answer found (format error)."
                    termination = "format error"
                    break

            # 5.4 Token 限制检查
            token_count = self.count_tokens(current_context)
            logger.debug(f"Round {round_num} context token count: {token_count}")
            if token_count > self.max_input_tokens:
                logger.warning(f"Token quantity exceeds the limit: {token_count}")
                # 强制生成答案
                force_answer_msgs = current_context + [
                    {"role": "user", "content": "You have now reached the maximum context length. "
                                                "Stop making tool calls. Based on your research report, "
                                                "provide the final answer in the three-part format: "
                                                "<think>...</think> <report>...</report> <answer>...</answer>"}
                ]
                content = await self.call_server(force_answer_msgs)
                parsed = self.parse_output(content)
                prediction = parsed["answer"] if parsed["answer"] else "No answer found (token limit)."
                termination = 'token limit reached'
                full_trajectory_log.append({"role": "assistant", "content": content})
                break

        # 循环结束后的收尾
        if not prediction:
            prediction = 'No answer found.'
            termination = 'answer not found'
            if num_llm_calls_available == 0:
                termination = 'exceed available llm calls'

        # 返回最终结果
        result = {
            "question": question,
            "prediction": prediction,
            "report": research_round.current_report,
            "termination": termination,
            "trajectory": full_trajectory_log,
        }
        return result


async def main():
    # 1. 定义你的 LLM 配置
    llm_config = {
        "model": "gpt-4o",
        "generate_cfg": {
            'max_input_tokens': 32000,
            "temperature": 0.6,
            "top_p": 0.95,
            "presence_penalty": 1.1
        }
    }

    # 2. 实例化 agent
    agent = WebResearcherAgent(
        llm_config=llm_config,
        function_list=['search', 'python']
    )

    question = '刘翔破纪录时候是多少岁?'
    gt = "23岁差2天"

    # 4. 运行完整的并行研究与总结
    final_result = await agent.run(question)

    # 5. 打印结果
    print(f"final_result: {final_result}")


if __name__ == "__main__":
    asyncio.run(main())
