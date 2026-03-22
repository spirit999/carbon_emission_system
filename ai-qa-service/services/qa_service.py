"""智能问答领域服务：上下文拉取、向量检索、智谱 GLM 同步/流式调用。"""
import json
import logging
import time
from typing import List, Optional, Tuple

import httpx
import numpy as np

from core.config import settings

logger = logging.getLogger(__name__)

HTTP_CLIENT_TIMEOUT = httpx.Timeout(
    connect=10.0,
    read=60.0,
    write=20.0,
    pool=10.0,
)

_chunk_cache: Optional[Tuple[List[str], np.ndarray]] = None
_chunk_cache_ts: float = 0.0


def fetch_and_chunk() -> List[str]:
    chunks: List[str] = []
    try:
        with httpx.Client(timeout=HTTP_CLIENT_TIMEOUT) as client:
            resp = client.get(f"{settings.BACKEND_BASE_URL}/school/info")
            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == 200 and data.get("data"):
                    school = data["data"]
                    lines = ["【学校概况】"]
                    for k, v in school.items():
                        if v is not None:
                            lines.append(f"{k}：{v}")
                    if len(lines) > 1:
                        chunks.append("\n".join(lines))

            resp2 = client.get(f"{settings.BACKEND_BASE_URL}/carbonEmission/collegeCarbonEmission")
            if resp2.status_code == 200:
                data2 = resp2.json()
                if data2.get("code") == 200 and data2.get("data"):
                    carbon = data2["data"]
                    year = carbon.get("actualYear") or 2025
                    lines = [f"【{year} 年碳排放概览】"]
                    for k, v in carbon.items():
                        if k != "actualYear" and v is not None:
                            lines.append(f"{k}：{v} kg CO2")
                    if len(lines) > 1:
                        chunks.append("\n".join(lines))

            resp3 = client.get(f"{settings.BACKEND_BASE_URL}/carbonEmission/listSpeciesCarbon")
            if resp3.status_code == 200:
                data3 = resp3.json()
                if data3.get("code") == 200 and data3.get("data"):
                    raw = data3["data"]
                    items = raw.get("list", []) if isinstance(raw, dict) else (raw if isinstance(raw, list) else [])
                    if items:
                        lines = ["【各排放源 CO2 排放量】"]
                        for it in items:
                            name = it.get("objectCategory", it.get("category", ""))
                            val = it.get("emissionAmount", it.get("amount", ""))
                            lines.append(f"{name}：{val} kg")
                        chunks.append("\n".join(lines))
    except Exception as e:
        logger.warning("拉取并分块失败: %s", e)
    return chunks


def embed_texts(texts: List[str]) -> Optional[np.ndarray]:
    if not texts or not settings.LLM_API_KEY:
        return None
    batch_size = 8
    all_embeddings: List[List[float]] = []
    with httpx.Client(timeout=httpx.Timeout(connect=10.0, read=30.0, write=10.0, pool=10.0)) as client:
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            payload = {"model": settings.EMBEDDING_MODEL, "input": batch}
            headers = {
                "Authorization": f"Bearer {settings.LLM_API_KEY}",
                "Content-Type": "application/json",
            }
            try:
                resp = client.post(settings.EMBEDDING_BASE_URL, json=payload, headers=headers)
                if resp.status_code != 200:
                    logger.warning("embedding 请求失败: %s %s", resp.status_code, resp.text)
                    return None
                body = resp.json()
                for item in body.get("data", []):
                    emb = item.get("embedding")
                    if emb:
                        all_embeddings.append(emb)
            except Exception as e:
                logger.warning("embedding 调用异常: %s", e)
                return None
    if len(all_embeddings) != len(texts):
        return None
    return np.array(all_embeddings, dtype=np.float32)


def _get_or_refresh_chunk_embeddings() -> Optional[Tuple[List[str], np.ndarray]]:
    global _chunk_cache, _chunk_cache_ts
    now = time.time()
    if _chunk_cache is not None and (now - _chunk_cache_ts) < settings.VECTOR_CACHE_TTL:
        return _chunk_cache
    chunks = fetch_and_chunk()
    if not chunks:
        return None
    embeddings = embed_texts(chunks)
    if embeddings is None or len(embeddings) != len(chunks):
        return None
    _chunk_cache = (chunks, embeddings)
    _chunk_cache_ts = now
    return _chunk_cache


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    a_norm = a / (np.linalg.norm(a, axis=1, keepdims=True) + 1e-8)
    b_norm = b / (np.linalg.norm(b) + 1e-8)
    return (a_norm @ b_norm.T).ravel()


def build_system_context() -> str:
    chunks = fetch_and_chunk()
    if not chunks:
        return "当前系统暂无可用的业务数据。"
    return "\n\n".join(chunks)


def get_relevant_context(question: str, top_k: Optional[int] = None) -> str:
    k = top_k if top_k is not None else settings.VECTOR_TOP_K
    if not settings.EMBEDDING_ENABLED or not settings.LLM_API_KEY:
        return build_system_context()
    cached = _get_or_refresh_chunk_embeddings()
    if cached is None:
        return build_system_context()
    chunks, embeddings = cached
    q_emb = embed_texts([question])
    if q_emb is None or q_emb.shape[0] != 1:
        return build_system_context()
    sims = _cosine_similarity(embeddings, q_emb)
    take = min(k, len(chunks))
    top_indices = np.argsort(sims)[::-1][:take]
    selected = [chunks[i] for i in top_indices]
    return "\n\n".join(selected)


def build_prompt(question: str, context: str) -> str:
    return (
        "你是北京林业大学碳排放核算与管理系统的智能助手，只能基于我提供的系统数据进行回答，不要编造没有的数据。"
        "如果系统数据中没有相关信息，请明确回答「系统当前数据无法回答该问题」。\n\n"
        "=== 系统数据开始 ===\n"
        f"{context}\n"
        "=== 系统数据结束 ===\n\n"
        f"用户问题：{question}\n"
        "请用简体中文、面向学校管理人员，使用 Markdown 格式输出（适当使用 ## 标题、- 列表、**加粗**、`代码` 等），"
        "结构清晰、便于阅读。"
    )


def extract_content_from_zhipu_response(resp_body: str) -> Optional[str]:
    if not resp_body:
        return None
    try:
        data = json.loads(resp_body)
        choices = data.get("choices") or []
        if choices:
            msg = choices[0].get("message") or {}
            content = msg.get("content")
            if content:
                return content.strip()
    except (json.JSONDecodeError, KeyError) as e:
        logger.warning("解析智谱响应失败: %s", e)
    return None


def call_llm(prompt: str) -> str:
    if not settings.LLM_API_KEY:
        raise ValueError("未配置 LLM_API_KEY")
    payload = {
        "model": settings.LLM_MODEL,
        "max_tokens": settings.LLM_MAX_TOKENS,
        "messages": [{"role": "user", "content": prompt}],
    }
    headers = {
        "Authorization": f"Bearer {settings.LLM_API_KEY}",
        "Content-Type": "application/json",
    }
    with httpx.Client(timeout=HTTP_CLIENT_TIMEOUT) as client:
        resp = client.post(settings.LLM_BASE_URL, json=payload, headers=headers)
    if resp.status_code != 200:
        raise RuntimeError(f"LLM API 调用失败，HTTP {resp.status_code}: {resp.text}")
    content = extract_content_from_zhipu_response(resp.text)
    return content if content else resp.text


def call_llm_stream(prompt: str):
    if not settings.LLM_API_KEY:
        raise ValueError("未配置 LLM_API_KEY")
    payload = {
        "model": settings.LLM_MODEL,
        "max_tokens": settings.LLM_MAX_TOKENS,
        "messages": [{"role": "user", "content": prompt}],
        "stream": True,
    }
    headers = {
        "Authorization": f"Bearer {settings.LLM_API_KEY}",
        "Content-Type": "application/json",
    }
    with httpx.Client(timeout=HTTP_CLIENT_TIMEOUT) as client:
        with client.stream("POST", settings.LLM_BASE_URL, json=payload, headers=headers) as resp:
            if resp.status_code != 200:
                raise RuntimeError(f"LLM API 调用失败，HTTP {resp.status_code}")
            for line in resp.iter_lines():
                if not line or not line.startswith("data: "):
                    continue
                data = line[6:].strip()
                if data == "[DONE]":
                    break
                try:
                    obj = json.loads(data)
                    for choice in obj.get("choices", []):
                        delta = choice.get("delta", {})
                        content = delta.get("content")
                        if content:
                            yield content
                except (json.JSONDecodeError, KeyError):
                    continue


def answer_question_sync(question: str) -> Tuple[int, str, Optional[str]]:
    """返回 (http风格业务code, 回答正文, 可选 message)。"""
    context = get_relevant_context(question, top_k=settings.VECTOR_TOP_K)
    prompt = build_prompt(question, context)

    if not settings.LLM_ENABLED:
        return (
            200,
            "当前服务未启用大模型（LLM_ENABLED=false），请联系管理员配置。\n\n系统上下文（供调试）：\n" + context,
            None,
        )

    try:
        answer = call_llm(prompt)
        return 200, answer, None
    except httpx.TimeoutException as e:
        logger.error("调用大模型接口超时: %s", e)
        return (
            200,
            "调用大模型接口失败：大模型响应超时，请稍后重试，或简化问题内容后再次尝试。",
            None,
        )
    except Exception as e:
        logger.error("调用大模型接口失败: %s", e)
        return 200, f"调用大模型接口失败：{str(e)}", None


def stream_answer_chunks(question: str):
    context = get_relevant_context(question, top_k=settings.VECTOR_TOP_K)
    prompt = build_prompt(question, context)
    if not settings.LLM_ENABLED:
        yield "当前服务未启用大模型（LLM_ENABLED=false），请联系管理员配置。"
        return
    try:
        for chunk in call_llm_stream(prompt):
            yield chunk
    except httpx.TimeoutException:
        yield "\n\n[调用大模型超时，请稍后重试或简化问题。]"
    except Exception as e:
        logger.error("流式调用失败: %s", e)
        yield f"\n\n[调用失败：{str(e)}]"
