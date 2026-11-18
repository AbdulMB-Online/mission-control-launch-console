# Technology choices

These four implemented choices follow the requested stack and separate deterministic launch decisions, advisory models and human approval. Each choice includes a specific reason, a rejected alternative and a customer concern.

## Backend: Python and FastAPI

**Specific reason.** FastAPI provides typed HTTP validation and async execution for the three concurrent checks. Python keeps launch thresholds, severity overrides, deadlines, approval eligibility and Decimal cost arithmetic in functions independent of model or HTTP code. Application use cases communicate with storage and the model gateway through small contracts; database sessions never span a model call.

**Rejected alternative.** Django would supply useful administration and a broader application framework, but that extra surface is unnecessary for this small report-processing console. FastAPI keeps the HTTP layer narrow around the requested use cases.

**Customer concern.** A Flight Director needs explainable decisions during provider failure. Python owns the verdict and violations, invalid classification falls back to unknown/high, and unavailable checks require review. Exact boundary, prompt-injection and approval tests verify that advisory text cannot replace launch facts or become approval.

## Frontend: React, TypeScript and Vite

**Specific reason.** React supports the engineer form, Director review, confirmation dialog and execution cards without a second backend. TypeScript and runtime response validation protect the API boundary. Vite produces a static bundle served through Nginx; component tests and isolated Chromium journeys exercise the built interface.

**Rejected alternative.** Next.js adds server rendering and another server framework that this local, API-driven operational console does not need. Static delivery with a single FastAPI backend keeps the demonstration and deployment easier to inspect.

**Customer concern.** Operators must distinguish launch facts, advisory findings and human approval. The UI shows canonical GO/NO_GO separately, preserves form entries on failure, marks unavailable findings/costs explicitly and never treats evaluator acceptance as approval. Credentials stay in memory and model markup renders as text. Desktop/mobile browser tests cover these flows. Self-hosted fonts avoid external font requests; their required license notices are distributed with the app.

## Database: SQLite and SQLAlchemy

**Specific reason.** SQLite offers transactions and a durable database file without another service. SQLAlchemy provides explicit sessions and portable mappings, while Alembic records versioned schema changes. The current app runs migrations before readiness, uses WAL/foreign keys/a busy timeout and preserves its data in a Compose volume.

**Rejected alternative.** PostgreSQL would handle larger concurrent deployments well, but adds credentials, another service and operational setup that the single-replica assignment does not require.

**Customer concern.** Reports, model results and approvals must survive restart. A named volume, versioned migrations and short transactions preserve records. Approval and its trace commit atomically with uniqueness constraints; simultaneous requests cannot approve twice. Real process/crash and Compose restart checks retain history, usage and prices. The local demo uses one API worker/replica; multi-replica hosting would require revisiting storage and job execution.

## Model: OpenAI structured output through one gateway

**Specific reason.** One gateway handles classification, concurrent checks, drafting and separate evaluation calls. The adapter uses Responses structured output with strict schemas and Python validation. The default snapshot is `gpt-5.4-mini-2026-03-17`, configurable through `OPENAI_MODEL`, because it supports the required Responses/structured-output features. The SDK is locked at 3.51.0 and its HTTPX2 transport is intercepted in adapter tests. [Official model documentation](https://developers.openai.com/api/docs/models/gpt-5.4-mini), [structured-output guidance](https://developers.openai.com/api/docs/guides/structured-outputs?api-mode=responses), [SDK transport documentation](https://github.com/openai/openai-python/blob/main/httpx2.md).

**Rejected alternative.** A locally hosted open-weight model would remove an external provider dependency but add model hosting, resource requirements and output-quality verification to a short assignment. A single gateway still leaves provider replacement possible later.

**Customer concern.** Cost, latency and prompt injection must not compromise safety or human authority. Calls have 30-second limits and output caps; the pipeline has a 270-second ceiling, at most ten model calls and no automatic retries. Python preserves known usage even for invalid responses, calculates costs from versioned rates and keeps unknown totals visibly incomplete. Injection findings require review; models have no decision-mutating or approval tools. A stage/round-scripted fake uses the same interface offline. Rates were checked against the official model page on 2026-11-17; real provider access, writing/detection quality and paid usage remain unverified.

## Reproducibility

Runtime Python dependencies are pinned in `backend/requirements.lock`, test dependencies in `backend/requirements-dev.lock`, and frontend dependencies in `frontend/package-lock.json`. Python and Node images are pinned by digest. Playwright 1.64.1 and its matching Chromium binary are installed at test-image build time. Docker Compose runs the app; `make test` executes component, API, subprocess and browser checks without external networking or a real API key. The real deployment smoke command refuses live mode before filing.
