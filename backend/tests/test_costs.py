"""Exact arithmetic contract; imports are deferred so missing behavior is red, not collection errors."""
from decimal import Decimal
from importlib import import_module, util

import pytest


def costs():
    assert util.find_spec("app.domain.costs") is not None, "Python cost calculation has not been implemented"
    return import_module("app.domain.costs")


def snapshot(module):
    return module.RateSnapshot(
        version="openai-standard-2026-11-17", model="gpt-5.4-mini-2026-03-17",
        input_per_million=Decimal("0.75"), cached_input_per_million=Decimal("0.075"),
        output_per_million=Decimal("4.50"),
    )


@pytest.mark.parametrize("usage,expected", [
    ((1000, 200, 100), "0.001065"),
    ((1000, 1000, 100), "0.000525"),
    ((0, 0, 0), "0"),
    ((1, 0, 0), "0.00000075"),
    ((1, 1, 0), "0.000000075"),
    ((1_000_000, 200_000, 100_000), "1.065"),
])
def test_python_cost_uses_cached_subset_and_exact_decimal_arithmetic(usage, expected):
    module = costs()
    value = module.calculate_cost("openai", "gpt-5.4-mini-2026-03-17", *usage, snapshot(module))
    assert type(value) is Decimal and value == Decimal(expected)


@pytest.mark.parametrize("usage", [
    (None, None, None), (1000, None, 100), (1000, 200, None),
    (-1, 0, 1), (1, -1, 1), (1, 0, -1), (1, 2, 1),
    (True, 0, 1), (1, False, 1), (1, 0, True),
    (1.0, 0, 1), ("1000", 200, 100),
])
def test_unknown_or_invalid_token_counts_never_become_a_zero_bill(usage):
    module = costs()
    assert module.calculate_cost("openai", "gpt-5.4-mini-2026-03-17", *usage, snapshot(module)) is None


def test_missing_or_mismatched_model_rate_is_unknown():
    module = costs()
    assert module.calculate_cost("openai", "unpriced-model", 1000, 200, 100, None) is None
    assert module.calculate_cost("openai", "unpriced-model", 1000, 200, 100, snapshot(module)) is None


@pytest.mark.parametrize("provider", ["fake", "python", "human"])
def test_simulation_and_deterministic_operations_have_no_provider_charge(provider):
    module = costs()
    assert module.calculate_cost(provider, None, 1000, 200, 100, None) == Decimal("0")


def test_small_call_costs_are_summed_without_per_call_rounding():
    module = costs()
    values = [module.calculate_cost("openai", "gpt-5.4-mini-2026-03-17", 1, 1, 0, snapshot(module)) for _ in range(100)]
    assert sum(values, Decimal("0")) == Decimal("0.000007500")
