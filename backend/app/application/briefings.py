"""Bounded drafting/evaluation with durable drafts and human-only approval."""

from dataclasses import asdict, replace
from uuid import uuid4

from pydantic import ValidationError

from app.application.ai_schemas import Draft, Evaluation
from app.application.llm import LLMRequest, ModelTrace, guarded_generate, model_error, token_usage
from app.application.prompts import DRAFT_SYSTEM, EVALUATION_SYSTEM, report_data
from app.domain.briefings import Briefing


def context(report):
    return {
        "report": report_data(report),
        "launch_decision": {
            "verdict": report.verdict,
            "violations": [dict(field=item.field, observed=format(item.observed, "f"), operator=item.operator,
                                limit=format(item.limit, "f"), message=item.message) for item in report.violations],
            "effective_severity": report.effective_severity,
            "brief_by_at": report.brief_by_at.isoformat(),
        },
        "classification": {"subsystem": report.subsystem, "severity": report.classified_severity,
                           "status": report.classification_status, "rationale": report.classification_rationale},
        "checks": [asdict(item) for item in report.checks],
    }


def draft_data(draft):
    return {"summary": draft.summary, "recommended_actions": list(draft.recommended_actions),
            "round_number": draft.round_number}


def require_review(report, reason):
    return replace(report, requires_review=True, review_reasons=tuple(dict.fromkeys((*report.review_reasons, reason))))


async def briefing_loop(report, gateway, store, clock):
    if report.pipeline_status in ("completed", "failed"):
        return report
    if report.briefings:
        # A partial run may already have incurred provider charges. Recovery
        # must mark it interrupted rather than silently repeat model requests.
        raise ValueError("Briefing execution already started; do not repeat it.")
    report = replace(report, pipeline_status="processing", error_code=None)

    async def call(stage, number, schema, data):
        request = LLMRequest(
            stage=stage, round_number=number,
            system_prompt=DRAFT_SYSTEM if stage == "draft" else EVALUATION_SYSTEM,
            data=data, schema=schema.model_json_schema(),
            max_output_tokens=700 if stage == "draft" else 400, prompt_version=f"{stage}-v1",
        )
        started = clock()
        response = await guarded_generate(gateway, request)
        code = model_error(response)
        payload = None
        if code is None:
            try:
                payload = schema.model_validate(response.payload)
            except ValidationError:
                code = "invalid_output"
        trace = ModelTrace(
            id=str(uuid4()), report_id=report.id, step_key=f"{stage}_{number}",
            display_order=100 + (number - 1) * 20 + (10 if stage == "evaluation" else 0),
            status="error" if code else "completed", started_at=started, finished_at=clock(),
            provider=response.provider, model=response.model, prompt_version=request.prompt_version,
            provider_response_id=response.response_id, error_code=code, round_number=number,
            **token_usage(response.input_tokens, response.cached_input_tokens, response.output_tokens),
        )
        return payload, trace, code

    for number in range(1, 4):
        previous = report.briefings[-1] if report.briefings else None
        data = {**context(report), "previous_draft": draft_data(previous) if previous else None,
                "evaluation_feedback": list(previous.feedback) if previous else []}
        payload, trace, code = await call("draft", number, Draft, data)
        if code:
            report = require_review(replace(report, pipeline_status="failed", error_code=f"draft_{code}"), f"draft_{code}")
            await store.update_briefings(report, trace)
            return report
        draft = Briefing(str(uuid4()), number, payload.summary, tuple(payload.recommended_actions), clock())
        report = replace(report, briefings=(*report.briefings, draft))
        await store.update_briefings(report, trace)

        evaluation, trace, code = await call("evaluation", number, Evaluation,
                                             {**context(report), "draft": draft_data(draft)})
        draft = replace(
            draft, evaluation_status="error" if code else "accepted" if evaluation.acceptable else "needs_revision",
            feedback=() if code else tuple(evaluation.feedback), evaluated_at=clock(),
        )
        report = replace(report, briefings=(*report.briefings[:-1], draft))
        if code:
            report = require_review(report, f"evaluation_{code}")
        await store.update_briefings(report, trace)

        if code or evaluation.acceptable or number == 3:
            if not code and not evaluation.acceptable:
                report = require_review(report, "evaluation_exhausted")
            draft = replace(draft, is_selected=True)
            report = replace(report, pipeline_status="completed", briefings=(*report.briefings[:-1], draft))
            await store.update_briefings(report)
            return report

    raise AssertionError("The bounded loop must terminate by round three.")
