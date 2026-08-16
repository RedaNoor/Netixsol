from typing import Literal
from pydantic import BaseModel, EmailStr, Field, field_validator

ProjectType = Literal["ai_agent", "web_app", "api_integration", "data_dashboard", "other"]

class ClientRequest(BaseModel):
    client_name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    company: str = Field(min_length=2, max_length=150)
    project_type: ProjectType
    requirements: str = Field(min_length=20, max_length=4000)
    budget_usd: int = Field(ge=500, le=1_000_000)
    timeline_weeks: int = Field(ge=1, le=104)

    @field_validator("requirements")
    @classmethod
    def validate_requirements(cls, value: str) -> str:
        value = value.strip()
        injection_markers = (
            "ignore previous instructions",
            "reveal system prompt",
            "show your hidden prompt",
            "disregard previous instructions",
        )
        if any(marker in value.lower() for marker in injection_markers):
            raise ValueError("Prompt-injection-like instructions are not allowed in requirements.")
        return value

class ProposalDraft(BaseModel):
    executive_summary: str = Field(min_length=20, max_length=1200)
    proposed_scope: list[str] = Field(min_length=3, max_length=10)
    assumptions: list[str] = Field(min_length=1, max_length=8)
    exclusions: list[str] = Field(min_length=1, max_length=8)
    estimated_price_usd: int = Field(ge=500, le=1_000_000)
    estimated_timeline_weeks: int = Field(ge=1, le=104)
    risks: list[str] = Field(min_length=1, max_length=8)
    next_steps: list[str] = Field(min_length=2, max_length=8)

class AgentResult(BaseModel):
    request_id: str
    status: Literal["pending_approval", "approved", "rejected", "failed"]
    lead_score: int = Field(ge=0, le=100)
    lead_tier: Literal["low", "medium", "high"]
    feasibility: Literal["feasible", "needs_discovery"]
    proposal: ProposalDraft | None = None
    reviewer_notes: str | None = None
    warnings: list[str] = []
    approval_url: str | None = None
    metrics: dict = {}

class ApprovalRequest(BaseModel):
    approve: bool
    reviewer_notes: str = Field(default="", max_length=1000)
