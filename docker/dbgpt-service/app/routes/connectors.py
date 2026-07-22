"""
Connector Routes — 代理到 DB-GPT 原生 API (http://localhost:5670)

提供 WeKnora 前端所需的数据库类型与连接管理接口。
所有业务逻辑由 DB-GPT 后端处理，本模块仅做透明代理。
"""

import logging
import os
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
import httpx

logger = logging.getLogger(__name__)

DBGPT_BASE = os.getenv("DBGPT_BASE", "http://dbgpt:5670")
TIMEOUT = 30.0

router = APIRouter(prefix="/api/connectors", tags=["connectors"])

_client: httpx.AsyncClient | None = None

# 前端提交的参数名与 DB-GPT params 参数的映射
PARAM_KEYS = {
    "host", "port", "user", "password", "database", "driver",
    "pool_size", "max_overflow", "pool_timeout", "pool_recycle", "pool_pre_ping",
    "path", "db_path", "check_same_thread", "schema", "hostname",
}


def _transform_body(body: dict) -> dict:
    """将 WeKnora 前端扁平格式转换为 DB-GPT 嵌套格式。
    扁平格式: {db_type, comment, host, port, user, password, database, ...}
    嵌套格式: {type, params: {...}, description, id?}
    如果已经是嵌套格式则直接返回。
    """
    if "type" in body and "params" in body:
        return body
    transformed: dict = {}
    # type
    db_type = body.pop("db_type", None)
    if db_type:
        transformed["type"] = db_type
    # description
    desc = body.pop("comment", None) or body.pop("description", None)
    if desc:
        transformed["description"] = desc
    # id (for update)
    obj_id = body.pop("id", None)
    if obj_id is not None:
        transformed["id"] = obj_id
    # params: 剩余的 key 中属于连接参数的提取出来
    params = {}
    for k in list(body):
        if k in PARAM_KEYS:
            params[k] = body.pop(k)
    if params:
        transformed["params"] = params
    # 剩余未识别的 key 也合并到 params（兼容 DB-GPT 自定义参数）
    if body:
        params.update(body)
        transformed["params"] = params
    return transformed


def get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(timeout=TIMEOUT)
    return _client


@router.get("/types")
async def get_connector_types():
    """获取 DB-GPT 支持的数据源类型列表"""
    client = get_client()
    try:
        resp = await client.get(f"{DBGPT_BASE}/api/v2/serve/datasource-types")
        if resp.status_code >= 400:
            logger.warning(f"DB-GPT returned {resp.status_code} for /datasource-types")
            return JSONResponse(
                content={"success": False, "err_msg": f"DB-GPT 返回错误: {resp.status_code}"},
                status_code=502,
            )
        data = resp.json()
        return JSONResponse(content=data, status_code=resp.status_code)
    except httpx.RequestError as e:
        logger.error(f"Proxy GET /types failed: {e}")
        return JSONResponse(
            content={"success": False, "err_msg": f"后端服务不可达: {e}"},
            status_code=502,
        )
    except Exception as e:
        logger.exception(f"Unexpected error in GET /types")
        return JSONResponse(
            content={"success": False, "err_msg": f"内部错误: {str(e)}"},
            status_code=500,
        )


@router.get("")
async def get_connectors(request: Request):
    """获取已有数据源连接列表"""
    client = get_client()
    try:
        resp = await client.get(f"{DBGPT_BASE}/api/v2/serve/datasources")
        if resp.status_code >= 400:
            logger.warning(f"DB-GPT returned {resp.status_code} for /datasources")
            return JSONResponse(
                content={"success": False, "err_msg": f"DB-GPT 返回错误: {resp.status_code}"},
                status_code=502,
            )
        return JSONResponse(content=resp.json(), status_code=resp.status_code)
    except httpx.RequestError as e:
        logger.error(f"Proxy GET /connectors failed: {e}")
        return JSONResponse(
            content={"success": False, "err_msg": f"后端服务不可达: {e}"},
            status_code=502,
        )
    except Exception as e:
        logger.exception(f"Unexpected error in GET /connectors")
        return JSONResponse(
            content={"success": False, "err_msg": f"内部错误: {str(e)}"},
            status_code=500,
        )


@router.post("")
async def create_connector(request: Request):
    """创建数据源连接"""
    client = get_client()
    try:
        body = _transform_body(await request.json())
        resp = await client.post(f"{DBGPT_BASE}/api/v2/serve/datasources", json=body)
        if resp.status_code >= 400:
            logger.warning(f"DB-GPT returned {resp.status_code} for POST /datasources")
            return JSONResponse(
                content={"success": False, "err_msg": f"DB-GPT 返回错误: {resp.status_code}"},
                status_code=502,
            )
        return JSONResponse(content=resp.json(), status_code=resp.status_code)
    except httpx.RequestError as e:
        logger.error(f"Proxy POST /connectors failed: {e}")
        return JSONResponse(
            content={"success": False, "err_msg": f"后端服务不可达: {e}"},
            status_code=502,
        )
    except Exception as e:
        logger.exception(f"Unexpected error in POST /connectors")
        return JSONResponse(
            content={"success": False, "err_msg": f"内部错误: {str(e)}"},
            status_code=500,
        )


@router.put("/{connector_id}")
async def update_connector(connector_id: str, request: Request):
    """更新数据源连接"""
    client = get_client()
    try:
        body = _transform_body(await request.json())
        resp = await client.put(f"{DBGPT_BASE}/api/v2/serve/datasources", json=body)
        if resp.status_code >= 400:
            logger.warning(f"DB-GPT returned {resp.status_code} for PUT /datasources")
            return JSONResponse(
                content={"success": False, "err_msg": f"DB-GPT 返回错误: {resp.status_code}"},
                status_code=502,
            )
        return JSONResponse(content=resp.json(), status_code=resp.status_code)
    except httpx.RequestError as e:
        logger.error(f"Proxy PUT /connectors/{connector_id} failed: {e}")
        return JSONResponse(
            content={"success": False, "err_msg": f"后端服务不可达: {e}"},
            status_code=502,
        )
    except Exception as e:
        logger.exception(f"Unexpected error in PUT /connectors")
        return JSONResponse(
            content={"success": False, "err_msg": f"内部错误: {str(e)}"},
            status_code=500,
        )


@router.delete("/{connector_id}")
async def delete_connector(connector_id: str):
    """删除数据源连接"""
    client = get_client()
    try:
        resp = await client.delete(f"{DBGPT_BASE}/api/v2/serve/datasources/{connector_id}")
        if resp.status_code >= 400:
            logger.warning(f"DB-GPT returned {resp.status_code} for DELETE /datasources/{connector_id}")
            return JSONResponse(
                content={"success": False, "err_msg": f"DB-GPT 返回错误: {resp.status_code}"},
                status_code=502,
            )
        return JSONResponse(content=resp.json(), status_code=resp.status_code)
    except httpx.RequestError as e:
        logger.error(f"Proxy DELETE /connectors/{connector_id} failed: {e}")
        return JSONResponse(
            content={"success": False, "err_msg": f"后端服务不可达: {e}"},
            status_code=502,
        )
    except Exception as e:
        logger.exception(f"Unexpected error in DELETE /connectors")
        return JSONResponse(
            content={"success": False, "err_msg": f"内部错误: {str(e)}"},
            status_code=500,
        )


@router.post("/test")
async def test_connection(request: Request):
    """测试数据源连接"""
    client = get_client()
    try:
        body = _transform_body(await request.json())
        resp = await client.post(f"{DBGPT_BASE}/api/v2/serve/datasources/test-connection", json=body)
        if resp.status_code >= 400:
            logger.warning(f"DB-GPT returned {resp.status_code} for test-connection")
            return JSONResponse(
                content={"success": False, "err_msg": f"DB-GPT 返回错误: {resp.status_code}"},
                status_code=502,
            )
        return JSONResponse(content=resp.json(), status_code=resp.status_code)
    except httpx.RequestError as e:
        logger.error(f"Proxy POST /connectors/test failed: {e}")
        return JSONResponse(
            content={"success": False, "err_msg": f"后端服务不可达: {e}"},
            status_code=502,
        )
    except Exception as e:
        logger.exception(f"Unexpected error in POST /connectors/test")
        return JSONResponse(
            content={"success": False, "err_msg": f"内部错误: {str(e)}"},
            status_code=500,
        )


@router.post("/{connector_id}/refresh")
async def refresh_connector(connector_id: str):
    """刷新数据源连接信息（表结构等）"""
    client = get_client()
    try:
        resp = await client.post(f"{DBGPT_BASE}/api/v2/serve/datasources/{connector_id}/refresh")
        if resp.status_code >= 400:
            logger.warning(f"DB-GPT returned {resp.status_code} for POST /datasources/{connector_id}/refresh")
            return JSONResponse(
                content={"success": False, "err_msg": f"DB-GPT 返回错误: {resp.status_code}"},
                status_code=502,
            )
        return JSONResponse(content=resp.json(), status_code=resp.status_code)
    except httpx.RequestError as e:
        logger.error(f"Proxy POST /connectors/{connector_id}/refresh failed: {e}")
        return JSONResponse(
            content={"success": False, "err_msg": f"后端服务不可达: {e}"},
            status_code=502,
        )
    except Exception as e:
        logger.exception(f"Unexpected error in POST /connectors/{connector_id}/refresh")
        return JSONResponse(
            content={"success": False, "err_msg": f"内部错误: {str(e)}"},
            status_code=500,
        )
