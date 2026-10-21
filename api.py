from fastapi import FastAPI
from pydantic import BaseModel
import agent.handle_turn as ht

app = FastAPI(title="数码3C客服 Agent")


class ChatIn(BaseModel):
    query: str


class ChatOut(BaseModel):
    answer: str


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/chat", response_model=ChatOut)
def chat(body: ChatIn):
    return {"answer": ht.handle_turn(body.query)}


@app.post("/reset")
def reset():
    ht.history.clear()
    ht.current.clear()
    return {"ok": True}
