import json
import json5
import os
import re
import datetime
import asyncio
import random
import tiktoken
import time

from typing import Dict, List, Optional, Union
from loguru import logger
from openai import OpenAI, APIError, APIConnectionError, APITimeoutError

from webresearcher.base import Message, BaseTool, build_text_completion_prompt, count_tokens as count_tokens_base

from webresearcher.prompt import get_system_prompt
from webresearcher.tool_file import FileParser
from webresearcher.tool_scholar import Scholar
from webresearcher.tool_python import PythonInterpreter
from webresearcher.tool_search import Search
from webresearcher.tool_visit import Visit

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")

OBS_START = '<tool_response>'
OBS_END = '\n</tool_response>'

MAX_LLM_CALL_PER_RUN = int(os.getenv('MAX_LLM_CALL_PER_RUN', 50))
FILE_DIR = os.getenv('FILE_DIR', './files')

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
    这取代了"单上下文"的 `messages` 列表。
    """

    def __init__(self, question: str):
        self.question = question  # 原始问题（固定）
        self.prev_report = "无"  # 上轮总结报告（核心记忆），初始为空
        self.last_tool_res = None  # 上一轮工具结果（用于输入到本轮 get_context）
        self.pending_tool_res = None  # 本轮待综合的工具结果（用于 synthesize_report）
        self.pending_think = ""  # 本轮待综合的思考过程（用于 synthesize_report）

    def get_context(self, system_prompt: str) -> List[Dict]:
        """
        生成本轮精简上下文（仅含必要信息，避免臃肿）。
        这是 IterResearch 的核心：状态只包含 (问题, 上轮报告, 上一轮工具结果)。
        """
        context = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"【研究问题】\n{self.question}"},
            {"role": "user", "content": f"【上轮研究总结】\n{self.prev_report}"},
        ]
        # 添加上一轮工具结果（若有），作为 Workspace 的一部分
        if self.last_tool_res:
            context.append({"role": "user", "content": f"【上轮工具结果】\n{self.last_tool_res}"})

        return context

    def set_pending_data(self, think: str, tool_res: str):
        """暂存本轮的思考和工具结果，以便 synthesize_report 使用"""
        self.pending_think = think
        self.pending_tool_res = tool_res

    async def synthesize_report(self, llm_agent: 'MultiTurnReactAgent'):
        """
        每轮工具调用后更新报告（核心：合并新信息，过滤噪音）。
        这是一个 LLM 调用，用于"综合" (synthesize)。
        """
        if not self.pending_tool_res:
            logger.warning("synthesize_report called with no pending tool result. Skipping.")
            return

        # logger.info("Synthesizing new report...")
        report_prompt = [
            {"role": "system", "content": (
                "你是一个研究报告综合器。\n"
                "你的任务是基于【上轮报告】、【本轮思考】和【本轮工具结果】，生成一份更新、更精炼的【新研究报告】。\n"
                "规则:\n"
                "1. 整合新信息：将【本轮工具结果】中的关键发现融入报告。\n"
                "2. 修正与去重：根据【本轮思考】，修正【上轮报告】中的错误，并删除重复或不再相关的信息。\n"
                "3. 保持连贯：确保新报告是一个逻辑清晰、事实准确的完整总结。\n"
                "4. 只输出报告内容，不要说其他的话。"
            )},
            {"role": "user", "content": f"【上轮报告】\n{self.prev_report}"},
            {"role": "user", "content": f"【本轮思考】\n{self.pending_think}"},
            {"role": "user", "content": f"【本轮工具结果】\n{self.pending_tool_res}"}
        ]

        # 使用 llm_agent 的 call_server 方法进行异步调用
        new_report = await llm_agent.call_server(report_prompt, stop_sequences=["<tool_response>"])

        self.prev_report = new_report.strip() if new_report else self.prev_report

        # [关键] 将本轮的工具结果转移为下一轮的输入
        self.last_tool_res = self.pending_tool_res
        
        # 清理待综合数据
        self.pending_tool_res = None
        self.pending_think = ""
        # logger.info(f"Report updated.")


class MultiTurnReactAgent:
    """
    Multi-turn ReAct agent implementing the IterResearch paradigm.
    No longer inherits from FnCallAgent - fully independent implementation.
    """
    
    def __init__(
            self,
            llm_config: Optional[Dict] = None,
            function_list: Optional[List[str]] = None,
    ):
        self.llm_generate_cfg = llm_config["generate_cfg"]
        self.model = llm_config.get("model", "gpt-4o")  # 主模型
        self.max_input_tokens = llm_config.get("max_input_tokens", 32000)
        self.llm_timeout = llm_config.get("llm_timeout", 300.0)
        self.agent_timeout = llm_config.get("agent_timeout", 600.0)
        self.model_thinking_type = llm_config.get("model_thinking_type", "enabled")
        self.function_list = function_list or list(TOOL_MAP.keys())

    def parse_output(self, text: str) -> Dict[str, str]:
        """
        从 LLM 输出中解析标签。
        优先级：answer > tool_call > think
        使用非贪婪匹配，确保正确提取可能嵌套的标签。
        """
        # 1. 提取 answer（最终答案）- 使用 findall 捕获所有 answer 标签
        answer_matches = re.findall(r'<answer>(.*?)</answer>', text, re.DOTALL)
        if answer_matches:
            # 如果有多个 answer，拼接它们
            answer_str = "\n".join([match.strip() for match in answer_matches if match.strip()])
            answer_str = answer_str.strip()
        else:
            answer_str = None
        
        # 2. 提取 tool_call（工具调用）
        tool_call_match = re.search(r'<tool_call>(.*?)</tool_call>', text, re.DOTALL)
        
        if tool_call_match:
            tool_call_content = tool_call_match.group(1).strip()
            # 处理 Python 代码块的特殊格式
            if "python\n<code>" in tool_call_content or "<code>" in tool_call_content:
                tool_call_str = tool_call_content
            else:
                tool_call_str = tool_call_content
        else:
            tool_call_str = None
        
        # 3. 提取 think（思考过程）
        think_match = re.search(r'<think>(.*?)</think>', text, re.DOTALL)
        think_str = think_match.group(1).strip() if think_match else None
        
        # 调试日志：帮助诊断解析问题
        if not answer_str and not tool_call_str:
            logger.debug(f"⚠️ Parse warning: No answer or tool_call found. Text preview:\n{text[:300]}...")
        
        return {
            "think": think_str,
            "tool_call": tool_call_str,
            "answer": answer_str,
        }

    async def call_server(self, msgs: List[Dict], stop_sequences: List[str] = None,
                          max_tries: int = 3) -> str:
        """改为 async 异步方法，并使用 run_in_executor 处理同步的 OpenAI 库"""
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
                # [关键] 使用 run_in_executor 在线程池中运行同步的 blocking I/O
                chat_response = await loop.run_in_executor(
                    None,  # 使用默认的 ThreadPoolExecutor
                    lambda: client.chat.completions.create(
                        model=self.model,
                        messages=msgs,
                        stop=stop_sequences,
                        extra_body={
                            "thinking": {
                                # "type": "disabled",  # 不使用深度思考能力
                                "type": self.model_thinking_type,  # enabled, 使用深度思考能力
                                # "type": "auto", # 模型自行判断是否使用深度思考能力
                            }
                        },
                        temperature=self.llm_generate_cfg.get('temperature', 0.6),
                        top_p=self.llm_generate_cfg.get('top_p', 0.95),
                        max_tokens=10000,
                        presence_penalty=self.llm_generate_cfg.get('presence_penalty', 1.1)
                    )
                )

                content = chat_response.choices[0].message.content
                reasoning_content = None
                if hasattr(chat_response.choices[0].message, 'reasoning_content') and chat_response.choices[
                    0].message.reasoning_content:
                    reasoning_content = chat_response.choices[0].message.reasoning_content
                    content = f"<think>{reasoning_content}</think>\n{content}"
                
                logger.debug(f"input messages: {msgs}, \nLLM Response: {content}, \nreasoning_content: {reasoning_content}")

                if content and content.strip():
                    return content.strip()
                else:
                    logger.warning(f"Attempt {attempt + 1}: Empty response received.")

            except (APIError, APIConnectionError, APITimeoutError) as e:
                logger.warning(f"Attempt {attempt + 1} API error: {e}")
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} unexpected error: {e}")

            if attempt < max_tries - 1:
                sleep_time = base_sleep_time * (2 ** attempt) + random.uniform(0, 1)
                sleep_time = min(sleep_time, 30)
                logger.info(f"Retrying in {sleep_time:.2f}s...")
                await asyncio.sleep(sleep_time)  # [关键] 使用 await asyncio.sleep
            else:
                logger.error("All retry attempts exhausted. The call has failed.")
        return "LLM server error (all retries exhausted)."

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
        """[已修复] 改为 async，并正确处理同步/异步工具"""
        loop = asyncio.get_event_loop()

        try:
            # 1. 处理 Python 代码
            if tool_call_str.startswith("python\n<code>"):
                code_raw = tool_call_str.split("<code>", 1)[1].rsplit("</code>", 1)[0].strip()
                # PythonInterpreter.call 是同步的，用 executor 运行
                result = await loop.run_in_executor(None, TOOL_MAP['PythonInterpreter'].call, code_raw)
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
        start_time = time.time()

        # 1. 初始化研究轮次（仅携带问题，无历史冗余）
        research_round = ResearchRound(question=question)
        system_prompt = get_system_prompt(self.function_list) + str(today_date())

        # 'full_trajectory_log' 仅用于调试和日志记录，*不*用于生成提示
        full_trajectory_log = []
        prediction = ''
        termination = ''

        num_llm_calls_available = MAX_LLM_CALL_PER_RUN
        round_num = 0

        while num_llm_calls_available > 0:
            if time.time() - start_time > self.agent_timeout:  # 3 minutes in seconds
                logger.warning("Agent timeout reached.")
                termination = "timeout"
                prediction = "No answer found (timeout)."
                break

            round_num += 1
            num_llm_calls_available -= 1

            # 2. 生成本轮精简上下文（仅含问题+上轮报告+最新工具结果）
            current_context = research_round.get_context(system_prompt)
            if round_num == 1:
                full_trajectory_log.extend(current_context)  # 仅记录初始上下文

            # 3. 调用LLM获取“思考+工具调用/答案”（论文中的Think-Action组件）
            content = await self.call_server(current_context)
            full_trajectory_log.append({"role": "assistant", "content": content})

            logger.debug(f'Round {round_num}: {content}')

            # 4. 解析输出 (Think, Action/Answer)
            parsed = self.parse_output(content)
            logger.debug(f"Parsed output: {parsed}")

            # 5. 检查是否为最终答案
            if parsed["answer"]:
                logger.debug("Final answer found.")
                prediction = parsed["answer"]
                termination = "answer"
                break  # 成功退出循环

            # 6. 检查是否为工具调用
            elif parsed["tool_call"]:
                logger.debug(f"Executing tool: {parsed['tool_call'][:100]}...")
                result = await self.custom_call_tool(parsed["tool_call"])

                tool_response_log = f"<tool_response>\n{result}\n</tool_response>"
                full_trajectory_log.append({"role": "user", "content": tool_response_log})

                # 7. [关键] 更新 IterResearch 状态
                # 7a. 暂存思考和工具结果
                research_round.set_pending_data(think=parsed["think"] or "", tool_res=result)

                # 7b. [核心] 调用 LLM 进行"综合"，更新中央记忆 (prev_report)
                # synthesize_report 内部会：
                # - 将 pending_tool_res 融合到 prev_report
                # - 将 pending_tool_res 转移为 last_tool_res（供下一轮输入使用）
                # - 清空 pending_tool_res 和 pending_think
                await research_round.synthesize_report(self)

            else:
                # 格式错误：LLM 没有生成 answer 或 tool_call
                logger.warning("⚠️ LLM did not produce <answer> or <tool_call>. Forcing answer generation...")
                
                # 强制生成答案：基于当前研究报告要求 LLM 给出最终答案
                force_answer_msgs = current_context + [
                    {"role": "user", "content": (
                        "You did not provide a valid response format. "
                        "Based on the research summary and information gathered so far, "
                        "please provide the final answer to the original question. "
                        "Use <answer>...</answer> format."
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

            # 8. Token 限制检查 (现在检查精简上下文，更不容易触发)
            token_count = self.count_tokens(current_context)
            logger.debug(f"Round {round_num} context token count: {token_count}")
            if token_count > self.max_input_tokens:
                logger.warning(f"Token quantity exceeds the limit: {token_count}")
                # 强制生成答案
                force_answer_msgs = current_context + [
                    {"role": "user", "content": "You have now reached the maximum context length. "
                                                "Stop making tool calls. Based on your research summary, "
                                                "provide the final answer in <answer>...</answer> format."}
                ]
                content = await self.call_server(force_answer_msgs)
                parsed = self.parse_output(content)
                logger.debug(f"Parsed output: {parsed}")
                prediction = parsed["answer"] if parsed["answer"] else "No answer found (token limit)."
                termination = 'token limit reached'
                break  # 退出循环

        # 循环结束后的收尾
        if 'prediction' not in locals():
            prediction = 'No answer found.'
            termination = 'answer not found'
            if num_llm_calls_available == 0:
                termination = 'exceed available llm calls'

        # [关键] 返回最终报告和答案，以供“整合”
        result = {
            "question": question,
            "prediction": prediction,
            "report": research_round.prev_report,
            "termination": termination,
            "trajectory": full_trajectory_log,  # 完整日志
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
    agent = MultiTurnReactAgent(
        llm_config=llm_config,
        function_list=['search', 'PythonInterpreter']
    )

    question = '刘翔破纪录时候是多少岁?'
    gt = "23岁差2天"

    # 4. 运行完整的并行研究与总结
    final_result = await agent.run(question)

    # 5. 打印结果
    logger.info(f"final_result: {final_result}")


if __name__ == "__main__":
    asyncio.run(main())
