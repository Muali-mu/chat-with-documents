from fastapi import FastAPI
from pydantic import BaseModel

import db
import generate
import retrieval

app = FastAPI(title="Chat With Your Docs")


class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[str]


@app.on_event("startup")
def startup():
    db.init_pool()


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    chunks = retrieval.retrieve(req.question)
    answer = generate.answer_question(req.question, chunks)
    sources = sorted({f"{c['filename']} ({c.get('section_label') or 'N/A'})" for c in chunks})
    return ChatResponse(answer=answer, sources=sources)


@app.get("/health")
def health():
    return {"status": "ok"}
