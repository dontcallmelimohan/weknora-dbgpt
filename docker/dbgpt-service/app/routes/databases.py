"""
数据库连接管理 API — 精简版：内存 CRUD + 代理到 DB-GPT
"""

import logging
import os
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import httpx

logger = logging.getLogger(__name__)
DBGPT_BASE = os.getenv("DBGPT_BASE", "http://dbgpt:5670")
router = APIRouter(prefix="/api/databases", tags=["Databases"])

_db_connections: dict[str, dict] = {}


class DatabaseCreate(BaseModel):
    name: str = Field(..., description="连接名称")
    db_type: str = Field(..., description="数据库类型: mysql / postgresql / sqlite")
    db_url: str = Field(..., description="数据库连接 URL")
    description: Optional[str] = Field(None, description="描述")


class DatabaseUpdate(BaseModel):
    name: Optional[str] = None
    db_url: Optional[str] = None
    description: Optional[str] = None


@router.get("")
async def list_databases():
    return {
        "databases": [
            {"id": k, "name": v["name"], "db_type": v["db_type"], "description": v.get("description", "")}
            for k, v in _db_connections.items()
        ]
    }


@router.post("/connect")
async def create_database(db: DatabaseCreate):
    import uuid
    db_id = str(uuid.uuid4())[:8]
    _db_connections[db_id] = {
        "id": db_id, "name": db.name, "db_type": db.db_type,
        "db_url": db.db_url, "description": db.description or "",
    }
    return {"id": db_id, "name": db.name, "db_type": db.db_type, "status": "connected"}


@router.delete("/{db_id}")
async def delete_database(db_id: str):
    if db_id not in _db_connections:
        raise HTTPException(404, "数据库连接不存在")
    del _db_connections[db_id]
    return {"status": "deleted", "id": db_id}


@router.put("/{db_id}")
async def update_database(db_id: str, db: DatabaseUpdate):
    if db_id not in _db_connections:
        raise HTTPException(404, "数据库连接不存在")
    existing = _db_connections[db_id]
    if db.name is not None:
        existing["name"] = db.name
    if db.db_url is not None:
        existing["db_url"] = db.db_url
    if db.description is not None:
        existing["description"] = db.description
    return {"id": db_id, "status": "updated"}


@router.get("/{db_id}/tables")
async def list_db_tables(db_id: str):
    """代理到 DB-GPT 获取表列表"""
    if db_id not in _db_connections:
        raise HTTPException(404, "数据库连接不存在")
    conn = _db_connections[db_id]
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{DBGPT_BASE}/api/v2/chat/db/tables",
                json={"db_name": conn["name"], "db_type": conn["db_type"]},
            )
            return resp.json()
    except Exception as e:
        raise HTTPException(500, f"DB-GPT 代理失败: {str(e)}")


@router.get("/{db_id}/schema")
async def get_db_schema(db_id: str, table: Optional[str] = None):
    if db_id not in _db_connections:
        raise HTTPException(404, "数据库连接不存在")
    conn = _db_connections[db_id]
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{DBGPT_BASE}/api/v2/chat/db/schema",
                json={"db_name": conn["name"], "table": table} if table else {"db_name": conn["name"]},
            )
            return resp.json()
    except Exception as e:
        raise HTTPException(500, f"DB-GPT 代理失败: {str(e)}")


@router.post("/{db_id}/query")
async def execute_query(db_id: str, body: dict):
    sql = body.get("sql", "")
    if not sql:
        raise HTTPException(400, "SQL 不能为空")
    if db_id not in _db_connections:
        raise HTTPException(404, "数据库连接不存在")
    conn = _db_connections[db_id]
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{DBGPT_BASE}/api/v2/chat/db/query",
                json={"db_name": conn["name"], "sql": sql},
            )
            return resp.json()
    except Exception as e:
        raise HTTPException(500, f"DB-GPT 代理失败: {str(e)}")


@router.post("/{db_id}/test")
async def test_connection(db_id: str):
    if db_id not in _db_connections:
        raise HTTPException(404, "数据库连接不存在")
    return {"status": "ok", "message": "连接信息已保存（精简模式不执行实际连接测试）"}
