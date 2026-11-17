"""Standard text-token prices, frozen with each call; no provider or database dependency."""
from dataclasses import asdict, dataclass
from decimal import Decimal


@dataclass(frozen=True)
class RateSnapshot:
    version: str
    model: str
    input_per_million: Decimal
    cached_input_per_million: Decimal
    output_per_million: Decimal

    def __post_init__(self):
        for rate in (self.input_per_million, self.cached_input_per_million, self.output_per_million):
            if not isinstance(rate, Decimal) or not rate.is_finite() or rate < 0:
                raise ValueError("Rates must be finite, nonnegative Decimals.")

    def to_dict(self):
        return {key: format(value, "f") if isinstance(value, Decimal) else value for key, value in asdict(self).items()}


# Verified 2026-11-17: https://developers.openai.com/api/docs/models/gpt-5.4-mini
# Standard Responses text pricing; no Batch/Flex/regional/tool adjustments.
def get_rate(provider: str, model: str | None) -> RateSnapshot | None:
    if provider == "openai" and model in ("gpt-5.4-mini", "gpt-5.4-mini-2026-03-17"):
        return RateSnapshot("openai-standard-2026-11-17", model, Decimal("0.75"), Decimal("0.075"), Decimal("4.50"))
    return None


def calculate_cost(provider, model, input_tokens, cached_input_tokens, output_tokens, rate):
    if provider in ("fake", "python", "human"):
        return Decimal("0")
    counts = (input_tokens, cached_input_tokens, output_tokens)
    if (not all(type(count) is int and count >= 0 for count in counts)
        or cached_input_tokens > input_tokens or rate is None or rate.model != model):
        return None
    return ((input_tokens - cached_input_tokens) * rate.input_per_million
            + cached_input_tokens * rate.cached_input_per_million
            + output_tokens * rate.output_per_million) / Decimal("1000000")


def summarize_traces(steps):
    known = [step for step in steps if step["usage_status"] == "reported"]
    return {
        "input_tokens": sum(step["input_tokens"] for step in known),
        "cached_input_tokens": sum(step["cached_input_tokens"] for step in known),
        "output_tokens": sum(step["output_tokens"] for step in known),
        "usage_complete": len(known) == len(steps),
        "known_cost_usd": format(sum((Decimal(step["cost_usd"]) for step in steps if step["cost_usd"] is not None), Decimal("0")), "f"),
        "cost_complete": all(step["cost_usd"] is not None for step in steps),
        "simulated": any(step["provider"] == "fake" for step in steps),
    }
