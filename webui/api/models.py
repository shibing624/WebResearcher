from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class CreateSessionRequest(BaseModel):
    """创建新会话"""
    agent: Optional[str] = Field(default="web_researcher", description="Agent 类型: web_researcher | webweaver | react | tts")
    tts_num_agents: Optional[int] = Field(default=3, ge=2, le=8, description="TTS Agent 并行智能体个数，2-8")
    max_turns: Optional[int] = Field(default=5, ge=1, le=20, description="多轮对话历史轮数，1-20")
    instruction: Optional[str] = Field(default="", max_length=2000, description="可选的附加指令")
    tools: Optional[List[str]] = Field(default=None, description="限定可用工具名称列表")


class ResearchRequest(BaseModel):
    """在会话中提交新问题"""
    session_id: str = Field(..., description="会话 ID")
    question: str = Field(..., min_length=1, max_length=4000, description="研究问题")


class TaskEvent(BaseModel):
    """返回给前端的事件结构，用于绘制时间轴或日志"""

    type: str
    timestamp: datetime
    round: Optional[int] = None
    plan: Optional[str] = None
    report: Optional[str] = None
    action: Optional[str] = None
    tool_call: Optional[str] = None
    observation: Optional[str] = None
    answer: Optional[str] = None
    status: Optional[str] = None
    termination: Optional[str] = None


class TaskPayload(BaseModel):
    """任务详情响应模型"""

    task_id: str
    question: str
    status: str
    created_at: datetime
    updated_at: datetime
    events: List[Dict[str, Any]]
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
