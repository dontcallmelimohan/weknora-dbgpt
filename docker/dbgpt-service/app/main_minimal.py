"""
DB-GPT Data Intelligence Microservice — 精简版入口（仅代理，不依赖 DB-GPT 源码）

用于服务器 Docker 部署，只包含 connectors/databases/chat 代理路由。
"""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting DB-GPT Data Intelligence Service (minimal)...")
    yield
    logger.info("Shutting down...")


app = FastAPI(
    title="DB-GPT Data Intelligence Service",
    description="Connectors / Databases / Chat 代理微服务",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
from app.routes.chat import router as chat_router
from app.routes.databases import router as databases_router
from app.routes.connectors import router as connectors_router

app.include_router(chat_router)
app.include_router(databases_router)
app.include_router(connectors_router)


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "0.1.0", "dbgpt_base": os.getenv("DBGPT_BASE", "")}
