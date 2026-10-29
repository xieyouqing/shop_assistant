import uuid
from pathlib import Path

import config

from fastapi import Cookie, FastAPI, Response
from fastapi.responses import FileResponse
from pydantic import BaseModel

from agent.session_store import SessionStore

app = FastAPI(title="数码3C客服 Agent")

# 每个浏览器一个会话：session id 存在 cookie 里
store = SessionStore()

# 前端页面：单文件静态页，与 API 同源托管，避免 CORS
WEB_INDEX = Path(__file__).resolve().parent / "web" / "index.html"


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(WEB_INDEX)


class ChatIn(BaseModel):
    query: str


class ChatOut(BaseModel):
    answer: str


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/chat", response_model=ChatOut)
def chat(body: ChatIn, response: Response, sid: str | None = Cookie(default=None)):
    if sid is None:  # 第一次访问：发一个会话 id
        sid = uuid.uuid4().hex
        response.set_cookie("sid", sid, httponly=True, max_age=config.SESSION_TTL, path="/")
    return {"answer": store.get(sid).handle_turn(body.query)}


@app.post("/reset")
def reset(sid: str | None = Cookie(default=None)):
    if sid:
        store.drop(sid)
    return {"ok": True}
