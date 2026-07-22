"""
数据库连接管理 API — 对接 DB-GPT 的数据源管理
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.db_connector import DatabaseConnector

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/databases", tags=["Databases"])

# 内存存储（生产环境应使用 DB-GPT 的持久化存储）
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
    """列出所有已配置的数据库连接"""
    return {
        "databases": [
            {
                "id": k,
                "name": v["name"],
                "db_type": v["db_type"],
                "description": v.get("description", ""),
            }
            for k, v in _db_connections.items()
        ]
    }


@router.post("/connect")
async def create_database(db: DatabaseCreate):
    """添加数据库连接"""
    import uuid
    db_id = str(uuid.uuid4())[:8]

    # 测试连接
    try:
        connector = DatabaseConnector(db.db_url)
        if not connector.test_connection():
            raise HTTPException(400, "数据库连接测试失败")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, f"数据库连接测试失败: {str(e)}")

    _db_connections[db_id] = {
        "id": db_id,
        "name": db.name,
        "db_type": db.db_type,
        "db_url": db.db_url,
        "description": db.description or "",
    }

    return {"id": db_id, "name": db.name, "db_type": db.db_type, "status": "connected"}


@router.delete("/{db_id}")
async def delete_database(db_id: str):
    """删除数据库连接"""
    if db_id not in _db_connections:
        raise HTTPException(404, "数据库连接不存在")
    del _db_connections[db_id]
    return {"status": "deleted", "id": db_id}


@router.put("/{db_id}")
async def update_database(db_id: str, db: DatabaseUpdate):
    """更新数据库连接"""
    if db_id not in _db_connections:
        raise HTTPException(404, "数据库连接不存在")

    existing = _db_connections[db_id]
    if db.name is not None:
        existing["name"] = db.name
    if db.db_url is not None:
        # 测试新连接
        try:
            connector = DatabaseConnector(db.db_url)
            if not connector.test_connection():
                raise HTTPException(400, "新数据库连接测试失败")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(400, f"新数据库连接测试失败: {str(e)}")
        existing["db_url"] = db.db_url
    if db.description is not None:
        existing["description"] = db.description

    return {"id": db_id, "status": "updated"}


@router.get("/{db_id}/tables")
async def list_db_tables(db_id: str):
    """列出数据库中所有表"""
    if db_id not in _db_connections:
        raise HTTPException(404, "数据库连接不存在")

    conn_info = _db_connections[db_id]
    try:
        db = DatabaseConnector(conn_info["db_url"])
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = []
        for table_name in inspector.get_table_names():
            try:
                columns = inspector.get_columns(table_name)
                row_count = 0
                try:
                    result = db.execute_query(f"SELECT COUNT(*) as cnt FROM {table_name}")
                    if result[0]:
                        row_count = result[0][0].get("cnt", 0)
                except Exception:
                    pass
                tables.append({
                    "name": table_name,
                    "columns": len(columns),
                    "rows": row_count,
                })
            except Exception:
                tables.append({"name": table_name, "columns": 0, "rows": 0})
        return {"tables": tables}
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/{db_id}/schema")
async def get_db_schema(db_id: str, table: Optional[str] = None):
    """获取数据库表结构"""
    if db_id not in _db_connections:
        raise HTTPException(404, "数据库连接不存在")

    conn_info = _db_connections[db_id]
    try:
        db = DatabaseConnector(conn_info["db_url"])
        tables = [table] if table else None
        schema = db.get_table_schemas(tables)
        return {"schema": schema}
    except Exception as e:
        raise HTTPException(500, str(e))


@router.post("/{db_id}/query")
async def execute_query(db_id: str, body: dict):
    """执行 SQL 查询"""
    if db_id not in _db_connections:
        raise HTTPException(404, "数据库连接不存在")

    sql = body.get("sql", "")
    if not sql:
        raise HTTPException(400, "SQL 不能为空")

    conn_info = _db_connections[db_id]
    try:
        db = DatabaseConnector(conn_info["db_url"])
        rows, count = db.execute_query(sql)
        columns = list(rows[0].keys()) if rows else []
        return {
            "columns": columns,
            "rows": rows[:200],
            "row_count": count,
        }
    except Exception as e:
        raise HTTPException(500, str(e))


@router.post("/{db_id}/test")
async def test_connection(db_id: str):
    """测试数据库连接"""
    if db_id not in _db_connections:
        raise HTTPException(404, "数据库连接不存在")

    conn_info = _db_connections[db_id]
    try:
        db = DatabaseConnector(conn_info["db_url"])
        if db.test_connection():
            return {"status": "ok", "message": "连接成功"}
        else:
            return {"status": "error", "message": "连接失败"}
    except Exception as e:
        raise HTTPException(500, str(e))
