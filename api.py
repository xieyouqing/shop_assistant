from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel

from agent.handle_turn import HandleTurn

app = FastAPI(title="数码3C客服 Agent")

# 单用户占位：SessionStore 写好后替换成「每个 sid 一个 HandleTurn」
_session = HandleTurn()

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
def chat(body: ChatIn):
    return {"answer": _session.handle_turn(body.query)}


@app.post("/reset")
def reset():
    _session.history.clear()
    _session.current = []
    return {"ok": True}
