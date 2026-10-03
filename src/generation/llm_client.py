import os
from dataclasses import dataclass
from time import perf_counter
from typing import TypeVar

from dotenv import load_dotenv
from openai import OpenAI, OpenAIError
from pydantic import BaseModel, ValidationError


DEFAULT_OPENAI_MODEL = "gpt-5-mini"

SchemaT = TypeVar("SchemaT", bound=BaseModel)


class LLMClientError(Exception):
    """Base error for LLM client failures."""


class MissingAPIKeyError(LLMClientError):
    """Raised when OPENAI_API_KEY is unavailable."""


class LLMAPIError(LLMClientError):
    """Raised when the OpenAI API call fails."""


class InvalidStructuredResponseError(LLMClientError):
    """Raised when the LLM response cannot be validated."""


@dataclass(frozen=True)
class LLMResult:
    """Validated structured output plus model usage metadata."""

    output: BaseModel
    model: str
    provider: str
    latency_ms: int
    input_tokens: int | None
    output_tokens: int | None
    estimated_cost_usd: float | None = None


class OpenAILLMClient:
    """Small OpenAI wrapper for structured LLM output."""

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        load_dotenv()
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise MissingAPIKeyError("OPENAI_API_KEY is required.")

        self.model = model or os.getenv("OPENAI_MODEL") or DEFAULT_OPENAI_MODEL
        self._client = OpenAI(api_key=self.api_key)

    def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_schema: type[SchemaT],
    ) -> LLMResult:
        """Request and validate structured output from OpenAI."""

        started = perf_counter()
        try:
            completion = self._client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format=response_schema,
            )
        except OpenAIError as exc:
            raise LLMAPIError(str(exc)) from exc

        latency_ms = int((perf_counter() - started) * 1000)
        message = completion.choices[0].message
        try:
            output = message.parsed
            if output is None:
                raise InvalidStructuredResponseError("OpenAI returned no parsed output.")
            response_schema.model_validate(output)
        except (ValidationError, InvalidStructuredResponseError) as exc:
            raise InvalidStructuredResponseError(str(exc)) from exc

        usage = getattr(completion, "usage", None)
        input_tokens = getattr(usage, "prompt_tokens", None)
        output_tokens = getattr(usage, "completion_tokens", None)

        return LLMResult(
            output=output,
            model=self.model,
            provider="openai",
            latency_ms=latency_ms,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )
