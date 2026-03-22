"""
智能问答微服务入口：统一注册路由模块。
"""
import logging

from fastapi import FastAPI

from question_answer.router import router as question_answer_router
from ws.router import router as ws_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

app = FastAPI(title="AI智能问答服务", version="1.0.0")
app.include_router(question_answer_router)
app.include_router(ws_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
