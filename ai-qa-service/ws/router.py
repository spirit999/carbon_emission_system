"""流式问答（HTTP 分块传输）；与同步问答路由分离，便于独立演进与部署策略。"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from question_answer.schemas import AskRequest
from question_answer import service

router = APIRouter(tags=["stream"])


@router.post("/ask/stream")
def ask_stream(request: AskRequest):
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="问题不能为空")
    return StreamingResponse(
        service.stream_answer_chunks(question),
        media_type="text/markdown; charset=utf-8",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
