"""
流式数据对话 API — 支持 SSE 实时输出分析过程
- SQL 生成：通过 Agent Runner (LLM)
- SQL 执行：通过 DB-GPT API (支持容器内数据源) 或本地 DatabaseConnector
"""

import asyncio
import json
import logging
from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.core.agent_runner import get_runner

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["Chat"])

DBGPT_INTERNAL_URL = "http://localhost:5670"
DBGPT_SQL_RUN_URL = f"{DBGPT_INTERNAL_URL}/api/v1/editor/sql/run"


async def _exec_sql_via_dbgpt(db_name: str, sql: str) -> dict:
    """通过 DB-GPT 内部 API 执行 SQL"""
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(DBGPT_SQL_RUN_URL, json={
            "db_name": db_name,
            "sql": sql,
        })
        data = resp.json()
        if not data.get("success"):
            return {"error": data.get("err_msg", "Unknown error")}
        result = data.get("data", {})
        return {
            "columns": result.get("colunms", []),
            "rows": [list(row) for row in result.get("values", [])],
            "row_count": len(result.get("values", [])),
        }


async def _exec_sql_local(db_url: str, sql: str) -> dict:
    """通过本地 DatabaseConnector 执行 SQL"""
    from app.core.db_connector import DatabaseConnector
    db = DatabaseConnector(db_url)
    rows, count = db.execute_query(sql)
    result_data = rows[:100] if rows else []
    return {
        "columns": list(result_data[0].keys()) if result_data else [],
        "rows": result_data,
        "row_count": count,
    }


async def _get_schema_via_dbgpt(db_name: str) -> list[dict]:
    """通过 DB-GPT API 获取数据源的表结构"""
    tables_sql = "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    result = await _exec_sql_via_dbgpt(db_name, tables_sql)
    if "error" in result:
        return []
    table_names = [row[0] for row in result.get("rows", [])]

    schemas = []
    for tname in table_names:
        info_sql = f"PRAGMA table_info({tname})"
        cols = await _exec_sql_via_dbgpt(db_name, info_sql)
        if "error" not in cols:
            col_rows = cols.get("rows", [])
            col_descs = [{"name": r[1], "type": r[2]} for r in col_rows if len(r) > 2]
            schemas.append({"table": tname, "columns": col_descs})

    return schemas


def _schemas_to_ddl(schemas: list[dict]) -> str:
    """将 schema 列表转为 DDL 文本"""
    parts = []
    for s in schemas:
        cols = ", ".join(f'{c["name"]} {c["type"]}' for c in s.get("columns", []))
        parts.append(f"CREATE TABLE {s['table']} ({cols});")
    return "\n".join(parts)


@router.get("/stream")
async def chat_stream(
    question: str = Query(..., description="用户问题"),
    db_url: str = Query("", description="数据库连接 URL（直接连接模式）"),
    db_name: str = Query("", description="DB-GPT 数据源名称（代理模式）"),
    dialect: str = Query("sqlite", description="SQL 方言"),
):
    """流式数据对话（SSE），支持两种模式：
    - db_name 模式：通过 DB-GPT API 代理执行 SQL
    - db_url 模式：直接连接数据库
    """

    use_dbgpt_proxy = bool(db_name)

    async def event_generator():
        runner = get_runner()
        yield f"data: {json.dumps({'type': 'status', 'content': '正在连接数据源...'})}\n\n"

        # Step 1: 获取表结构
        if use_dbgpt_proxy:
            try:
                schemas = await _get_schema_via_dbgpt(db_name)
                if not schemas:
                    yield f"data: {json.dumps({'type': 'error', 'content': f'无法获取数据源 {db_name} 的表结构'})}\n\n"
                    return
                schema_ddl = _schemas_to_ddl(schemas)
                yield f"data: {json.dumps({'type': 'schema', 'content': schema_ddl})}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'content': f'获取表结构失败: {str(e)}'})}\n\n"
                return
        else:
            try:
                from app.core.db_connector import DatabaseConnector
                db = DatabaseConnector(db_url)
                schema_ddl = db.get_table_schemas()
                yield f"data: {json.dumps({'type': 'schema', 'content': schema_ddl})}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'content': f'数据库连接失败: {str(e)}'})}\n\n"
                return

        # Step 2: 生成 SQL
        yield f"data: {json.dumps({'type': 'status', 'content': '正在生成 SQL...'})}\n\n"
        await asyncio.sleep(0.1)

        try:
            # 对于 proxy 模式，db_url 用 SQLite 内存库即可，SQL 生成不需要真实连接
            effective_db_url = db_url if db_url else "sqlite:///:memory:"
            sql_result = await runner.run_sql_task(
                question=question,
                db_url=effective_db_url,
                dialect=dialect,
                execute=False,
            )
            if sql_result.get("error"):
                yield f"data: {json.dumps({'type': 'error', 'content': sql_result['error']})}\n\n"
                return

            sql = sql_result.get("sql", "")
            if not sql:
                yield f"data: {json.dumps({'type': 'done'})}\n\n"
                return

            yield f"data: {json.dumps({'type': 'sql', 'content': sql, 'explanation': sql_result.get('explanation', '')})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': f'SQL 生成失败: {str(e)}'})}\n\n"
            return

        # Step 3: 执行 SQL
        yield f"data: {json.dumps({'type': 'status', 'content': '正在执行查询...'})}\n\n"

        try:
            if use_dbgpt_proxy:
                result = await _exec_sql_via_dbgpt(db_name, sql)
            else:
                result = await _exec_sql_local(db_url, sql)

            if "error" in result:
                yield f"data: {json.dumps({'type': 'error', 'content': result['error'], 'sql': sql})}\n\n"
            else:
                yield f"data: {json.dumps({'type': 'result', 'columns': result['columns'], 'rows': result['rows'], 'row_count': result['row_count']})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': f'查询执行失败: {str(e)}', 'sql': sql})}\n\n"
            return

        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
