"""
Chat Routes — 精简版：透传 SSE 聊天流到 DB-GPT
"""

import logging
import os

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
import httpx

logger = logging.getLogger(__name__)
DBGPT_BASE = os.getenv("DBGPT_BASE", "http://dbgpt:5670")

router = APIRouter(prefix="/api/chat", tags=["Chat"])


@router.get("/stream")
async def chat_stream(request: Request):
    """SSE 流式对话代理"""
    params = dict(request.query_params)
    db_url = params.get("db_url", "")
    question = params.get("question", "Hello")
    model = params.get("model", "")
    
    dbgpt_url = f"{DBGPT_BASE}/api/v2/chat/completions"
    body = {
        "model": model or "siliconflow-chat",
        "messages": [{"role": "user", "content": question}],
        "stream": True,
        "context": {"db_url": db_url} if db_url else {},
    }
    
    async def event_generator():
        async with httpx.AsyncClient(timeout=300.0) as client:
            async with client.stream("POST", dbgpt_url, json=body) as resp:
                async for chunk in resp.aiter_bytes():
                    yield chunk
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
