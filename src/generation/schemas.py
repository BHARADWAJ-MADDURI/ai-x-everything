from pydantic import BaseModel, ConfigDict, Field


class ArticleOutput(BaseModel):
    """Validated LLM output used to build an Article dataclass."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1)
    subtitle: str | None = None
    tldr: str = Field(min_length=1)
    what_happened: str = Field(min_length=1)
    how_it_works: str | None = None
    why_it_matters: str = Field(min_length=1)
    industry_impact: str | None = None
    career_impact: str | None = None
    opportunities: list[str] = Field(default_factory=list)
    risks_and_limitations: list[str] = Field(default_factory=list)
    key_concepts: list[str] = Field(default_factory=list)


class ShortVideoScene(BaseModel):
    """One scene in a platform-independent short-video plan."""

    model_config = ConfigDict(extra="forbid")

    scene_number: int = Field(ge=1)
    narration: str = Field(min_length=1)
    on_screen_text: str = Field(min_length=1)
    visual_direction: str = Field(min_length=1)


class ShortVideoPlan(BaseModel):
    """Validated short-video presentation plan derived from an Article."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1)
    hook: str = Field(min_length=1)
    target_duration_seconds: int = Field(ge=15, le=90)
    scenes: list[ShortVideoScene] = Field(min_length=1)
    closing_line: str = Field(min_length=1)
    caption: str = Field(min_length=1)
    hashtags: list[str] = Field(default_factory=list)
