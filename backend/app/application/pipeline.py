"""Advisory stages return data; only the caller persists their results."""

import asyncio
from dataclasses import replace
from uuid import uuid4

from pydantic import ValidationError

from app.application.ai_schemas import InjectionCheck, MissingInformationCheck, ToneCheck
from app.application.llm import LLMRequest, ModelTrace, guarded_generate, model_error, token_usage
from app.application.prompts import CHECK_BOUNDARY, CHECK_SYSTEM, report_data
from app.domain.checks import CheckOutcome


CHECK_SCHEMAS = {"injection": InjectionCheck, "missing_information": MissingInformationCheck, "tone": ToneCheck}


async def analyze_checks(report, gateway, clock):
    group = str(uuid4())

    async def check(kind, order):
        request = LLMRequest(
            stage=kind, round_number=None, system_prompt=CHECK_SYSTEM[kind] + CHECK_BOUNDARY,
            data={"report": report_data(report)}, schema=CHECK_SCHEMAS[kind].model_json_schema(),
            max_output_tokens=500, prompt_version=f"{kind}-v1",
        )
        started = clock()
        response = await guarded_generate(gateway, request)
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
        trace = ModelTrace(
            id=str(uuid4()), report_id=report.id, step_key=kind, display_order=order,
            status=outcome.status, started_at=started, finished_at=clock(),
            provider=response.provider, model=response.model, prompt_version=request.prompt_version,
            provider_response_id=response.response_id, error_code=code, parallel_group=group,
            **token_usage(response.input_tokens, response.cached_input_tokens, response.output_tokens),
        )
        return outcome, trace

    # No storage/session object enters these tasks. Each gets only immutable
    # report data and the async gateway. Capture stage errors inside each call.
    tasks = [asyncio.create_task(check(kind, 50 + index)) for index, kind in enumerate(CHECK_SCHEMAS)]
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
