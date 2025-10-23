from pydantic import BaseModel
from typing import Optional
from typing import Literal
from typing import Literal

# --- Start Graph Run ---
class StartRequest(BaseModel):
    human_prompt: str

# --- Resume Paused Graph Run ---
class ResumeRequest(BaseModel):
    thread_id: str
    review_action: Literal["approved", "feedback"]
    human_feedback: Optional[str] = None

# --- Minimal API Response ---
class GraphResponse(BaseModel):
    thread_id: str
    run_status: Literal["finished", "awaiting_feedback", "in_progress"]  # ← update this
    assistant_response: str