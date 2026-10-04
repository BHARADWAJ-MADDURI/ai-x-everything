from pydantic import BaseModel, ConfigDict, Field


class CanonicalContentDraftOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    hook: str = Field(min_length=1)
    thesis: str = Field(min_length=1)
    key_points: list[str] = Field(min_length=1)
    technical_explanation: str = Field(min_length=1)
    human_implication: str | None = None
    career_upskill_implication: str | None = None
    takeaway: str = Field(min_length=1)
    cta: str = Field(min_length=1)
    claim_references: list[str] = Field(min_length=1)
