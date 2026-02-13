import asyncio
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv
import sys
sys.path.append("../../")
load_dotenv()
from webresearcher.log import logger
from webresearcher.web_researcher_agent import WebResearcherAgent
from webresearcher.web_weaver_agent import WebWeaverAgent
from webresearcher.react_agent import ReactAgent
from webresearcher.tts_agent import TestTimeScalingAgent



class ConversationTurn:
    """单轮对话"""
    
    def __init__(self, question: str, answer: str = "", status: str = "pending", task_id: str = ""):
        self.task_id = task_id or uuid.uuid4().hex  # 每个 turn 独立的任务 ID
        self.question = question
        self.answer = answer
        self.status = status
        self.created_at = datetime.utcnow()
        self.events: List[Dict[str, Any]] = []
        self.result: Optional[Dict[str, Any]] = None
        self.error: Optional[str] = None
        
        # 新增：结构化的研究过程数据
        self.process_rounds: List[Dict[str, Any]] = []  # 每一轮的计划和报告
        self.process_tools: List[Dict[str, Any]] = []   # 所有工具调用
        self._webweaver_phase: str = "planner"  # Web Weaver 当前阶段
    
    def add_process_round(self, round_num: int, plan: str = "", report: str = "", timestamp: str = ""):
        """添加研究轮次"""
        # 检查是否已存在，存在则更新
        for r in self.process_rounds:
            if r.get("round") == round_num:
                if plan:
                    r["plan"] = plan
                if report:
                    r["report"] = report
                if timestamp:
                    r["timestamp"] = timestamp
                return
        
        # 不存在则新增
        self.process_rounds.append({
            "round": round_num,
            "plan": plan,
            "report": report,
            "timestamp": timestamp or datetime.utcnow().isoformat(),
        })
    
    def add_process_tool(self, round_num: int, tool_name: str, observation: str, is_error: bool = False, timestamp: str = ""):
        """添加工具调用"""
        self.process_tools.append({
            "round": round_num,
            "tool": tool_name,
            "observation": observation,
            "is_error": is_error,
            "timestamp": timestamp or datetime.utcnow().isoformat(),
        })
    
    def get_process_data(self) -> Dict[str, Any]:
        """获取结构化的研究过程数据"""
        return {
            "rounds": self.process_rounds,
            "tools": self.process_tools,
        }
    
    def to_dict(self, include_process: bool = True) -> Dict[str, Any]:
        data = {
            "task_id": self.task_id,  # 添加 task_id
            "question": self.question,
            "answer": self.answer,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "events": self.events,
            "result": self.result,
            "error": self.error,
        }
        if include_process:
            data["process"] = self.get_process_data()  # 新增研究过程
        return data


class SessionState:
    """会话状态，包含多轮对话"""
    
    def __init__(self, session_id: str, instruction: str = "", tools: Optional[List[str]] = None, agent: str = "web_researcher", tts_num_agents: int = 3, max_turns: int = 5):
        self.id = session_id
        self.instruction = instruction or ""
        self.tools = tools
        self.agent = agent or "web_researcher"
        self.tts_num_agents = max(2, min(8, tts_num_agents)) if tts_num_agents else 3
        self.max_turns = max(1, min(20, max_turns)) if max_turns else 5
        self.status = "active"
        self.created_at = datetime.utcnow()
        self.updated_at = self.created_at
        self.turns: List[ConversationTurn] = []
        self._condition = asyncio.Condition()
        self._current_turn: Optional[ConversationTurn] = None
        self._research_task: Optional[asyncio.Task] = None
    
    @property
    def is_active(self) -> bool:
        return self.status == "active"
    
    @property
    def current_turn(self) -> Optional[ConversationTurn]:
        return self._current_turn
    
    async def add_turn(self, question: str) -> ConversationTurn:
        """添加新的一轮对话"""
        turn = ConversationTurn(question=question, status="running")
        self.turns.append(turn)
        self._current_turn = turn
        self.updated_at = datetime.utcnow()
        async with self._condition:
            self._condition.notify_all()
        return turn
    
    async def add_event(self, event: Dict[str, Any]):
        """为当前轮次添加事件"""
        if not self._current_turn:
            return
        
        normalized = dict(event)
        timestamp = normalized.get("timestamp")
        if isinstance(timestamp, datetime):
            normalized["timestamp"] = timestamp.isoformat()
        elif not timestamp:
            normalized["timestamp"] = datetime.utcnow().isoformat()
        
        async with self._condition:
            self._current_turn.events.append(normalized)
            self.updated_at = datetime.utcnow()
            
            # 同时提取并存储结构化的研究过程数据
            event_type = normalized.get("type")
            
            # 记录 Web Weaver 阶段
            if event_type == "status" and normalized.get("phase"):
                self._current_turn._webweaver_phase = normalized["phase"]
            
            if event_type == "round":
                # 提取轮次、计划和报告
                round_num = normalized.get("round", 1)
                plan = normalized.get("plan", "")
                report = normalized.get("report", "")
                self._current_turn.add_process_round(
                    round_num=round_num,
                    plan=plan,
                    report=report,
                    timestamp=normalized["timestamp"]
                )
            
            elif event_type in ("tool", "tool_error"):
                # 提取工具调用（Web Weaver 用 step，Web Researcher 用 round）
                round_num = normalized.get("round")
                if round_num is None and "step" in normalized:
                    phase = getattr(self._current_turn, "_webweaver_phase", "planner")
                    round_num = (100 if phase == "writer" else 0) + normalized.get("step", 1)
                round_num = round_num if round_num is not None else 1
                tool_name = normalized.get("tool_call") or normalized.get("action") or normalized.get("tool_name", "unknown")
                observation = normalized.get("observation", "")
                is_error = (event_type == "tool_error")
                self._current_turn.add_process_tool(
                    round_num=round_num,
                    tool_name=tool_name,
                    observation=observation,
                    is_error=is_error,
                    timestamp=normalized["timestamp"]
                )
            
            elif event_type == "thinking":
                # React Agent: 思考/推理内容，存入 round 的 plan
                round_num = normalized.get("round", 1)
                content = normalized.get("content", "")
                for r in self._current_turn.process_rounds:
                    if r.get("round") == round_num:
                        r["plan"] = (r.get("plan", "") + ("\n\n" if r.get("plan") else "") + content).strip()
                        if normalized.get("timestamp"):
                            r["timestamp"] = normalized["timestamp"]
                        break
                else:
                    self._current_turn.add_process_round(
                        round_num=round_num,
                        plan=content,
                        report="",
                        timestamp=normalized["timestamp"]
                    )
            
            elif event_type == "step":
                phase = getattr(self._current_turn, "_webweaver_phase", "planner")
                round_num = (100 if phase == "writer" else 0) + normalized.get("step", 1)
                plan = normalized.get("plan", "")
                self._current_turn.add_process_round(
                    round_num=round_num,
                    plan=plan,
                    report="",
                    timestamp=normalized["timestamp"]
                )
            
            elif event_type == "outline_updated":
                phase = getattr(self._current_turn, "_webweaver_phase", "planner")
                round_num = (100 if phase == "writer" else 0) + normalized.get("step", 1)
                outline = normalized.get("outline", "")
                self._current_turn.add_process_round(
                    round_num=round_num,
                    plan="",
                    report=outline,
                    timestamp=normalized["timestamp"]
                )
            
            elif event_type == "tts_result":
                # TTS Agent: 将 parallel_runs 转为 process_rounds 供前端展示
                for i, run in enumerate(normalized.get("parallel_runs", [])):
                    pred = run.get("prediction", "")
                    report = run.get("report", "")
                    content = (pred + ("\n\n" + report if report else "")).strip()
                    self._current_turn.add_process_round(
                        round_num=i + 1,
                        plan="",
                        report=content or f"(Agent {i + 1} 未返回)",
                        timestamp=normalized.get("timestamp", "")
                    )
            
            elif event_type == "section_written":
                phase = getattr(self._current_turn, "_webweaver_phase", "planner")
                round_num = (100 if phase == "writer" else 0) + normalized.get("step", 1)
                content = normalized.get("content", "")
                # 追加到已有 report
                for r in self._current_turn.process_rounds:
                    if r.get("round") == round_num:
                        r["report"] = (r.get("report", "") + ("\n\n" if r.get("report") else "") + content).strip()
                        if normalized.get("timestamp"):
                            r["timestamp"] = normalized["timestamp"]
                        break
                else:
                    self._current_turn.add_process_round(
                        round_num=round_num,
                        plan="",
                        report=content,
                        timestamp=normalized["timestamp"]
                    )
            
            self._condition.notify_all()
    
    async def finish_turn(self, answer: str, result: Optional[Dict[str, Any]] = None, error: Optional[str] = None):
        """完成当前轮次"""
        if not self._current_turn:
            return
        
        self._current_turn.answer = answer
        self._current_turn.result = result
        self._current_turn.error = error
        self._current_turn.status = "completed" if not error else "failed"
        self.updated_at = datetime.utcnow()
        
        async with self._condition:
            self._condition.notify_all()
    
    def get_history_context(self, max_turns: int = 5) -> str:
        """构建历史对话上下文（用于多轮对话）
        
        Args:
            max_turns: 最多包含最近的 N 轮对话，默认 5 轮
        """
        if len(self.turns) <= 1:
            return ""
        
        # 只包含已完成的轮次（排除当前正在进行的轮次）
        completed_turns = [t for t in self.turns[:-1] if t.status == "completed" and t.answer]
        
        if not completed_turns:
            return ""
        
        # 只取最近的 max_turns 轮对话
        recent_turns = completed_turns[-max_turns:] if len(completed_turns) > max_turns else completed_turns
        
        context_parts = [
            "## Previous Conversation History",
            f"The following are the previous {len(recent_turns)} round(s) of conversation in this session.",
            "You should use this information to understand the context and provide better answers for the current question.",
            "DO NOT repeat information from previous answers unless specifically asked.",
            ""
        ]
        
        for idx, turn in enumerate(recent_turns, 1):
            context_parts.append(f"### Previous Round {idx}")
            context_parts.append(f"User Question: {turn.question}")
            context_parts.append(f"Your Answer: {turn.answer}")
            context_parts.append("")
        
        return "\n".join(context_parts)
    
    def to_dict(self, include_events: bool = True, include_process: bool = True) -> Dict[str, Any]:
        payload = {
            "session_id": self.id,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "turns": [turn.to_dict(include_process=include_process) if include_events else {
                "task_id": turn.task_id,
                "question": turn.question,
                "answer": turn.answer,
                "status": turn.status,
            } for turn in self.turns],
        }
        return payload
    
    def summary(self) -> Dict[str, Any]:
        """简要信息（用于列表）"""
        first_question = self.turns[0].question if self.turns else "未命名会话"
        last_answer = self.turns[-1].answer if self.turns else ""
        
        return {
            "session_id": self.id,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "turn_count": len(self.turns),
            "first_question": first_question,
            "last_answer": last_answer,
        }
    
    def history_record(self) -> Dict[str, Any]:
        """历史记录格式（包含研究过程）"""
        # 重要：保存完整的 turn 数据，包括 task_id 和 process
        record = {
            "session_id": self.id,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "turns": [turn.to_dict(include_process=True) for turn in self.turns],  # 包含研究过程
            "first_question": self.turns[0].question if self.turns else "",
            "turn_count": len(self.turns),
        }
        return record
    
    def condition(self) -> asyncio.Condition:
        return self._condition


class SessionManager:
    """管理多轮对话会话"""
    
    def __init__(self, history_path: Path):
        self.history_path = history_path
        self._history_lock = asyncio.Lock()
        self._sessions: Dict[str, SessionState] = {}
    
    def create_session(self, instruction: str = "", tools: Optional[List[str]] = None, agent: str = "web_researcher", tts_num_agents: int = 3, max_turns: int = 5) -> SessionState:
        """创建新会话"""
        session_id = uuid.uuid4().hex
        session = SessionState(session_id=session_id, instruction=instruction, tools=tools, agent=agent, tts_num_agents=tts_num_agents, max_turns=max_turns)
        self._sessions[session_id] = session
        return session
    
    async def cancel_research(self, session: SessionState) -> bool:
        """取消该会话正在运行的研究任务。返回 True 表示成功取消了任务。"""
        task = getattr(session, "_research_task", None)
        if task and not task.done():
            task.cancel()
            try:
                await task  # 等待任务结束，并消费 CancelledError
            except asyncio.CancelledError:
                pass
            return True
        return False
    
    def get_session(self, session_id: str) -> Optional[SessionState]:
        """获取会话，如果不在内存中，则从历史文件加载"""
        # 先从内存中查找
        if session_id in self._sessions:
            return self._sessions[session_id]
        
        # 从历史文件中加载
        return self._load_session_from_history(session_id)
    
    def _load_session_from_history(self, session_id: str) -> Optional[SessionState]:
        """从历史文件中加载会话（只读模式）"""
        if not self.history_path.exists():
            return None
        
        try:
            with self.history_path.open("r", encoding="utf-8") as fin:
                for line in fin:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                        if record.get("session_id") == session_id:
                            # 从历史记录重建 SessionState（只读）
                            session = SessionState(
                                session_id=record["session_id"],
                                instruction="",  # 历史记录不保存 instruction
                                tools=None
                            )
                            session.status = record.get("status", "completed")
                            session.created_at = datetime.fromisoformat(record["created_at"])
                            session.updated_at = datetime.fromisoformat(record["updated_at"])
                            
                            # 重建轮次
                            for turn_data in record.get("turns", []):
                                turn = ConversationTurn(
                                    question=turn_data["question"],
                                    answer=turn_data.get("answer", ""),
                                    status=turn_data.get("status", "completed"),
                                    task_id=turn_data.get("task_id", "")  # 加载 task_id
                                )
                                if "created_at" in turn_data:
                                    turn.created_at = datetime.fromisoformat(turn_data["created_at"])
                                turn.events = turn_data.get("events", [])
                                turn.result = turn_data.get("result")
                                turn.error = turn_data.get("error")
                                
                                # 重建研究过程数据
                                process_data = turn_data.get("process", {})
                                turn.process_rounds = process_data.get("rounds", [])
                                turn.process_tools = process_data.get("tools", [])
                                
                                session.turns.append(turn)
                            
                            # 加载的历史会话不需要 _current_turn（已完成）
                            session._current_turn = None
                            
                            return session
                    except (json.JSONDecodeError, KeyError, ValueError) as e:
                        logger.warning("Failed to parse history record: %s", e)
                        continue
        except Exception as e:
            logger.error("Failed to load session from history: %s", e)
        
        return None
    
    def start_research(self, session: SessionState, question: str):
        """在会话中开始新的一轮研究"""
        loop = asyncio.get_running_loop()
        task = loop.create_task(self._run_research(session, question))
        session._research_task = task
    
    async def _run_research(self, session: SessionState, question: str):
        """执行研究任务"""
        # 添加新的轮次
        turn = await session.add_turn(question)
        
        # 构建历史对话上下文
        max_turns_val = getattr(session, "max_turns", 5)
        history_context = session.get_history_context(max_turns=max_turns_val)
        
        # 关键修复：将历史上下文添加到 instruction 中
        # 这样可以让 agent 在 system prompt 中看到历史对话
        enhanced_instruction = session.instruction
        if history_context:
            enhanced_instruction = f"{session.instruction}\n\n{history_context}".strip()
        
        # 当前问题（不附加历史）
        current_question = question
        
        logger.info(f"Starting research for session {session.id}, turn {len(session.turns)}")
        logger.debug(f"Current question: {question}")
        logger.debug(f"Has history: {bool(history_context)}")
        if history_context:
            logger.debug(f"History context preview: {history_context[:200]}...")
        
        # 创建独立的 agent 实例
        agent_type = session.agent or "web_researcher"
        if agent_type == "webweaver":
            agent = WebWeaverAgent(instruction=enhanced_instruction)
            answer_key = "final_report"
            supports_progress = True
        elif agent_type == "react":
            agent = ReactAgent(
                instruction=enhanced_instruction,
                function_list=session.tools if session.tools else None,
                use_xml_protocol=False,
            )
            answer_key = "prediction"
            supports_progress = True
        elif agent_type == "tts":
            agent = TestTimeScalingAgent(function_list=session.tools if session.tools else None)
            answer_key = "final_synthesized_answer"
            supports_progress = False
        else:
            agent = WebResearcherAgent(
                instruction=enhanced_instruction,
                function_list=session.tools if session.tools else None,
            )
            answer_key = "prediction"
            supports_progress = True
        
        async def progress(event: Dict[str, Any]):
            await session.add_event(event)
        
        try:
            # 执行研究，使用当前问题
            if agent_type == "tts":
                num_agents = getattr(session, "tts_num_agents", 3)
                result = await agent.run(question=current_question, num_parallel_agents=num_agents)
            else:
                result = await agent.run(current_question, progress_callback=progress if supports_progress else None)
            
            answer = result.get(answer_key, "")
            err = result.get("error")
            
            # 添加最终事件（Web Weaver/React 已发送 complete/final，Web Researcher 需要 summary，TTS 无流式事件需合成展示）
            if result and agent_type == "web_researcher":
                await session.add_event({
                    "type": "summary",
                    "answer": answer,
                    "report": result.get("report"),
                    "termination": result.get("termination"),
                })
            elif result and agent_type == "tts":
                # TTS 无 progress_callback，合成 tts_result 事件供前端展示并行研究过程
                await session.add_event({
                    "type": "tts_result",
                    "parallel_runs": result.get("parallel_runs", []),
                    "synthesis_inputs": result.get("synthesis_inputs", []),
                })
            
            await session.finish_turn(answer=answer, result=result, error=err)
            logger.info(f"Research completed for session {session.id}, turn {len(session.turns)}")
            
        except asyncio.CancelledError:
            logger.info("Research cancelled for session %s", session.id)
            await session.add_event({"type": "error", "message": "用户已中止研究"})
            await session.finish_turn(answer="", error="用户已中止研究")
            raise
        except Exception as exc:
            error_msg = str(exc)
            logger.exception("Research failed in session %s: %s", session.id, exc)
            await session.add_event({"type": "error", "message": error_msg})
            await session.finish_turn(answer="", error=error_msg)
        
        finally:
            session._research_task = None
            # 持久化整个会话
            await self._persist_session(session)
    
    async def _persist_session(self, session: SessionState):
        """持久化会话到历史文件"""
        self.history_path.parent.mkdir(parents=True, exist_ok=True)
        record = session.history_record()
        async with self._history_lock:
            await asyncio.to_thread(self._append_jsonl, record)
    
    def _append_jsonl(self, record: Dict[str, Any]):
        """追加 JSONL 记录"""
        with self.history_path.open("a", encoding="utf-8") as fout:
            fout.write(json.dumps(record, ensure_ascii=False) + "\n")
    
    async def read_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """读取历史会话列表"""
        if not self.history_path.exists():
            history: List[Dict[str, Any]] = []
        else:
            history = await asyncio.to_thread(self._load_jsonl)
        
        # 合并活跃会话
        active = [session.history_record() for session in self._sessions.values()]
        combined = sorted(history + active, key=lambda item: item.get("updated_at", ""), reverse=True)
        
        # 去重（以 session_id 为准，保留最新的）
        seen = set()
        unique = []
        for item in combined:
            sid = item.get("session_id")
            if sid and sid not in seen:
                seen.add(sid)
                unique.append(item)
        
        if limit:
            unique = unique[:limit]
        
        return unique
    
    def _load_jsonl(self) -> List[Dict[str, Any]]:
        """加载 JSONL 文件"""
        items: List[Dict[str, Any]] = []
        with self.history_path.open("r", encoding="utf-8") as fin:
            for line in fin:
                line = line.strip()
                if not line:
                    continue
                try:
                    items.append(json.loads(line))
                except json.JSONDecodeError:
                    logger.warning("Skip malformed history line: %s", line[:120])
        return items
