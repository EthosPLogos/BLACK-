from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10_000)


class ChatResponse(BaseModel):
    reply: str
    agent: str
    task_type: str
    memory_used: bool
    policy_verdict: str = "auto_approved"
    approval_id: str | None = None
    inference_provider: str = "local"
