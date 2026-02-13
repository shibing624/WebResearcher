import json
from pathlib import Path
from typing import Any, AsyncGenerator, Dict

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from .session_manager import SessionManager
from .models import CreateSessionRequest, ResearchRequest

# 历史文件路径
HISTORY_FILE = Path(__file__).resolve().parent.parent / "data" / "history.jsonl"

# 创建路由
api_router = APIRouter(prefix="/api", tags=["research"])

# 创建会话管理器
manager = SessionManager(history_path=HISTORY_FILE)


def _format_sse(payload: Dict[str, Any]) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


@api_router.post("/session")
async def create_session(request: CreateSessionRequest):
    """创建新会话"""
    session = manager.create_session(
        instruction=request.instruction,
        tools=request.tools,
        agent=request.agent or "web_researcher",
        tts_num_agents=request.tts_num_agents or 3,
        max_turns=request.max_turns or 5,
    )
    return session.summary()


@api_router.post("/research")
async def submit_question(request: ResearchRequest):
    """在会话中提交新问题"""
    session = manager.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    manager.start_research(session, request.question)
    return {"session_id": session.id, "status": "running"}


@api_router.post("/session/{session_id}/cancel")
async def cancel_research(session_id: str):
    """取消当前会话正在运行的研究任务"""
    session = manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    cancelled = await manager.cancel_research(session)
    return {"session_id": session_id, "cancelled": cancelled}


@api_router.get("/session/{session_id}")
async def fetch_session(session_id: str):
    """获取会话详情"""
    session = manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session.to_dict(include_events=True)


@api_router.get("/session/{session_id}/turn/{turn_index}/process")
async def fetch_turn_process(session_id: str, turn_index: int):
    """获取指定轮次的研究过程（通过轮次索引）"""
    session = manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if turn_index < 0 or turn_index >= len(session.turns):
        raise HTTPException(status_code=404, detail="Turn not found")
    
    turn = session.turns[turn_index]
    process_data = turn.get_process_data()
    
    return {
        "session_id": session_id,
        "turn_index": turn_index,
        "task_id": turn.task_id,
        "question": turn.question,
        "answer": turn.answer,
        "status": turn.status,
        "process": process_data,
    }


@api_router.get("/session/{session_id}/task/{task_id}/process")
async def fetch_task_process(session_id: str, task_id: str):
    """获取指定任务的研究过程（通过 task_id）"""
    session = manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # 查找对应的 turn
    turn = None
    turn_index = -1
    for idx, t in enumerate(session.turns):
        if t.task_id == task_id:
            turn = t
            turn_index = idx
            break
    
    if not turn:
        raise HTTPException(status_code=404, detail="Task not found")
    
    process_data = turn.get_process_data()
    
    return {
        "session_id": session_id,
        "turn_index": turn_index,
        "task_id": turn.task_id,
        "question": turn.question,
        "answer": turn.answer,
        "status": turn.status,
        "process": process_data,
    }


@api_router.get("/session/{session_id}/stream")
async def stream_session(session_id: str):
    """流式获取会话事件"""
    session = manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # 如果是历史会话（没有 current_turn），直接返回空流
    if not session.current_turn:
        async def empty_generator() -> AsyncGenerator[str, None]:
            # 历史会话已完成，不需要流式传输
            yield _format_sse({"type": "info", "message": "Historical session, no live events"})
            return
        return StreamingResponse(empty_generator(), media_type="text/event-stream")
    
    condition = session.condition()
    
    async def event_generator() -> AsyncGenerator[str, None]:
        sent_count = 0
        
        while True:
            # 只发送当前轮次的事件
            current_turn = session.current_turn
            if not current_turn:
                break
            
            # 动态获取当前轮次索引（每次都重新计算，确保准确）
            current_turn_index = len(session.turns) - 1
            
            current_events = current_turn.events
            
            # 发送未发送的事件
            while sent_count < len(current_events):
                event_copy = dict(current_events[sent_count])
                event_copy["turn_index"] = current_turn_index
                yield _format_sse(event_copy)
                sent_count += 1
            
            # 检查当前轮次是否完成
            if current_turn.status in ("completed", "failed"):
                # 提取最后一轮的 report（从 events 中查找）
                last_report = ""
                for event in reversed(current_turn.events):
                    if event.get("type") == "round" and event.get("report"):
                        last_report = event["report"]
                        break
                
                # 发送最终状态
                yield _format_sse({
                    "type": "turn_finished",
                    "turn_index": current_turn_index,
                    "status": current_turn.status,
                    "answer": current_turn.answer,
                    "report": last_report,
                    "error": current_turn.error,
                })
                break
            
            # 等待新事件
            async with condition:
                await condition.wait()
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")


@api_router.get("/history")
async def list_history(limit: int = 20):
    """获取历史会话列表"""
    records = await manager.read_history(limit=limit)
    return {"items": records}
