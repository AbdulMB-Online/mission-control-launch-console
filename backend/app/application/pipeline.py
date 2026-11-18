"""Advisory stages return data; only the caller persists their results."""

import asyncio
from dataclasses import replace
from uuid import uuid4

from pydantic import ValidationError

from app.application.ai_schemas import InjectionCheck, MissingInformationCheck, ToneCheck
from app.application.llm import LLMRequest, guarded_generate, model_error, token_usage, running_trace
from app.application.prompts import CHECK_BOUNDARY, CHECK_SYSTEM, report_data
from app.domain.checks import CheckOutcome


CHECK_SCHEMAS = {"injection": InjectionCheck, "missing_information": MissingInformationCheck, "tone": ToneCheck}


async def analyze_checks(report, gateway, clock, store):
    group = str(uuid4())
    pending = {kind: running_trace(report.id, kind, 50 + index, clock(), gateway, f"{kind}-v1", parallel_group=group)
               for index, kind in enumerate(CHECK_SCHEMAS)}
    await store.start_traces(list(pending.values()))

    async def check(kind):
        request = LLMRequest(
            stage=kind, round_number=None, system_prompt=CHECK_SYSTEM[kind] + CHECK_BOUNDARY,
            data={"report": report_data(report)}, schema=CHECK_SCHEMAS[kind].model_json_schema(),
            max_output_tokens=500, prompt_version=f"{kind}-v1",
        )
        response = await guarded_generate(gateway, request)
        finished = clock()
        code = model_error(response)
        payload = None
        if code is None:
            try:
                payload = CHECK_SCHEMAS[kind].model_validate(response.payload)
            except ValidationError:
                code = "invalid_output"
        if payload is not None:
            values = payload.model_dump()
            flagged = values.pop("flagged") if kind != "tone" else payload.tone in ("urgent", "panic")
            outcome = CheckOutcome(kind, "completed", flagged, values)
        else:
            outcome = CheckOutcome(kind, "error", None, {}, code)
        trace = replace(pending[kind],
            status=outcome.status, finished_at=finished,
            provider=response.provider, model=response.model, prompt_version=request.prompt_version,
            provider_response_id=response.response_id, error_code=code, parallel_group=group,
            **token_usage(response.input_tokens, response.cached_input_tokens, response.output_tokens),
        )
        # Independent short sessions retain completed siblings even if another
        # check is later cancelled. No session spans a model call.
        await store.finish_trace(trace)
        return outcome, trace

    # Each storage operation opens its own session. No shared session enters
    # concurrent calls; stage failures are captured independently.
    tasks = [asyncio.create_task(check(kind)) for kind in CHECK_SCHEMAS]
    try:
        results = await asyncio.gather(*tasks)
    except BaseException:
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        raise
    outcomes, traces = zip(*results, strict=True)
    reasons = list(report.review_reasons)
    for item in outcomes:
        if item.status == "error":
            reasons.append(f"{item.kind}_{item.error_code}")
        elif item.flagged:
            reasons.append(f"{item.kind}_flagged")
    resolved = replace(report, checks=tuple(outcomes), requires_review=report.requires_review or bool(reasons),
                       review_reasons=tuple(dict.fromkeys(reasons)))
    return resolved, list(traces)
