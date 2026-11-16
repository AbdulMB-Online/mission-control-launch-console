import json

from openai import (
    APIConnectionError, APIError, APITimeoutError, AsyncOpenAI,
    AuthenticationError, DefaultAsyncHttpx2Client, RateLimitError,
)

from app.application.llm import LLMRequest, LLMResult, token_usage


class OpenAIGateway:
    """The only adapter allowed to construct an OpenAI client."""

    provider = "openai"

    def __init__(self, api_key: str, model: str):
        self.model = model
        self._client = AsyncOpenAI(
            api_key=api_key, max_retries=0, timeout=30.0,
            base_url="https://api.openai.com/v1",
            http_client=DefaultAsyncHttpx2Client(trust_env=False, follow_redirects=False, timeout=30.0),
        )

    async def generate(self, request: LLMRequest) -> LLMResult:
        try:
            response = await self._client.responses.create(
                model=self.model, instructions=request.system_prompt,
                input=[{"role": "user", "content": [{"type": "input_text", "text": json.dumps(request.data)}]}],
                text={"format": {"type": "json_schema", "name": f"{request.stage}_v1",
                                 "strict": True, "schema": request.schema}},
                max_output_tokens=request.max_output_tokens, reasoning={"effort": "none"},
                store=False,
            )
        except APITimeoutError:
            return self._error("timeout")
        except AuthenticationError:
            return self._error("authentication_error")
        except RateLimitError:
            return self._error("rate_limited")
        except APIConnectionError:
            return self._error("transport_error")
        except APIError:
            return self._error("provider_error")

        usage = getattr(response, "usage", None)
        details = getattr(usage, "input_tokens_details", None)
        metadata = dict(
            provider="openai", model=response.model, response_id=response.id,
            **token_usage(getattr(usage, "input_tokens", None), getattr(details, "cached_tokens", None),
                          getattr(usage, "output_tokens", None)),
        )
        if response.status == "incomplete":
            return LLMResult(**metadata, status="incomplete", error_code="incomplete")
        content = [part for item in response.output if getattr(item, "type", None) == "message"
                   for part in item.content]
        if any(getattr(part, "type", None) == "refusal" for part in content):
            return LLMResult(**metadata, status="refused", error_code="refusal")
        if response.status != "completed":
            return LLMResult(**metadata, status="error", error_code="provider_error")
        try:
            text = "".join(part.text for part in content if getattr(part, "type", None) == "output_text")
            payload = json.loads(text)
        except (ValueError, TypeError):
            return LLMResult(**metadata, status="error", error_code="invalid_output")
        return LLMResult(**metadata, payload=payload)

    def _error(self, code):
        # Provider exception strings can contain request data. Persist only codes.
        return LLMResult(provider="openai", model=self.model, status="error", error_code=code)

    async def aclose(self) -> None:
        await self._client.close()
