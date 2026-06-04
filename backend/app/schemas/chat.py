from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str
    agent: str
    task_type: str
    memory_used: bool
    policy_verdict: str = "auto_approved"
    approval_id: str | None = None
    inference_provider: str = "local"
