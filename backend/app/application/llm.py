"""Provider-independent model requests, results and persisted call metadata."""

import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Literal


@dataclass(frozen=True)
class LLMRequest:
    stage: str
    round_number: int | None
    system_prompt: str
    data: dict
    schema: dict
    max_output_tokens: int
    prompt_version: str


@dataclass(frozen=True)
class LLMResult:
    provider: str
    model: str | None = None
    response_id: str | None = None
    payload: object = None
    status: Literal["completed", "refused", "incomplete", "error"] = "completed"
    error_code: str | None = None
    input_tokens: int | None = None
    cached_input_tokens: int | None = None
    output_tokens: int | None = None
    usage_status: str = "unavailable"


def token_usage(input_tokens, cached_input_tokens, output_tokens) -> dict:
    counts = (input_tokens, cached_input_tokens, output_tokens)
    valid = all(type(count) is int and count >= 0 for count in counts)
    if valid and cached_input_tokens <= input_tokens:
        return dict(input_tokens=input_tokens, cached_input_tokens=cached_input_tokens,
                    output_tokens=output_tokens, usage_status="reported")
    return dict(input_tokens=None, cached_input_tokens=None, output_tokens=None, usage_status="unavailable")


@dataclass(frozen=True)
class ModelTrace:
    id: str
    report_id: str
    step_key: str
    display_order: int
    status: str
    started_at: datetime
    finished_at: datetime
    provider: str
    model: str | None
    prompt_version: str
    provider_response_id: str | None
    input_tokens: int | None
    cached_input_tokens: int | None
    output_tokens: int | None
    usage_status: str
    error_code: str | None
    parallel_group: str | None = None
    round_number: int | None = None


async def guarded_generate(gateway, request: LLMRequest) -> LLMResult:
    try:
        async with asyncio.timeout(30):
            return await gateway.generate(request)
    except TimeoutError:
        code = "timeout"
    except Exception:
        code = "provider_error"
    # CancelledError inherits BaseException and must propagate to the caller.
    return LLMResult(provider=getattr(gateway, "provider", "unknown"), status="error", error_code=code)


def model_error(response) -> str | None:
    if response.status == "completed":
        return None
    allowed = ("refusal", "incomplete", "invalid_output", "timeout", "provider_error",
               "authentication_error", "rate_limited", "transport_error")
    return response.error_code if response.error_code in allowed else "provider_error"
