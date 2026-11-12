# Technology choices

These decisions follow the requested stack and the assignment's separation of authority. Branch 1 implements the application shell, configuration, database/migration readiness and offline test runner. Report processing and the LLM gateway are later milestones; no live model call has been made.

## Backend: Python and FastAPI

**Specific reason.** FastAPI provides typed request validation alongside async execution for the three concurrent report checks. Python also keeps the launch thresholds, effective severity, deadlines and Decimal cost arithmetic in small functions that can be tested independently of a model or HTTP server. The current foundation has an app factory, validated settings, managed database lifetime and a readiness endpoint.

**Rejected alternative.** Django would supply useful administration and a broader application framework, but that extra surface is unnecessary for this small report-processing console. FastAPI keeps the HTTP layer narrow around the requested use cases.

**Customer concern.** A Flight Director needs decisions that remain explainable during an AI/provider failure. Keep deterministic decisions in Python, give models advisory fields only, persist results and expose explicit failure states. The business-rule implementation and its boundary tests belong to the report-processing branch.

## Frontend: React, TypeScript and Vite

**Specific reason.** React supports the engineer form and director review panels without introducing a second backend. TypeScript checks the API-facing UI, and Vite produces a static bundle served through Nginx. The foundation already verifies connection, error, retry and refresh states with component tests.

**Rejected alternative.** Next.js adds server rendering and another server framework that this local, API-driven operational console does not need. Static delivery with a single FastAPI backend keeps the demonstration and deployment easier to inspect.

**Customer concern.** Operators must distinguish an actual launch verdict from missing data or an unavailable service. The redesigned UI shows an explicit unassessed state, separates connection readiness from launch assessment and never invents reports/readings. Self-hosted fonts avoid external font requests. Required distribution notices are preserved in `frontend/public/FONT-LICENSES.txt`. The user's requested frontend-design skill is installed outside the repository.

## Database: SQLite and SQLAlchemy

**Specific reason.** SQLite offers transactions and a durable database file without another service. SQLAlchemy provides explicit sessions and portable mappings, while Alembic records versioned schema changes. The current app runs migrations before readiness, uses WAL/foreign keys/a busy timeout and preserves its data in a Compose volume.

**Rejected alternative.** PostgreSQL would handle larger concurrent deployments well, but adds credentials, another service and operational setup that the single-replica assignment does not require.

**Customer concern.** Reports and approvals must survive restart. Keep the database in a named volume, never recreate tables on startup, use short transactions and test real file-backed persistence. The foundation tests repeat migrations without losing existing data. Report/approval persistence tests follow with those features. This choice intentionally assumes one API worker/replica; multi-replica hosting would require revisiting storage and job execution.

## Model: OpenAI structured output through one gateway

**Specific reason.** The planned OpenAI adapter will use structured outputs for bounded classification/check/draft/evaluation payloads, with Python validation and conservative failure handling. The proposed snapshot is `gpt-5.4-mini-2026-03-17`, configurable through `OPENAI_MODEL`; its documented support includes the Responses API and structured output. Drafting and evaluation will use separate calls. [Official model documentation](https://developers.openai.com/api/docs/models/gpt-5.4-mini), [structured-output guidance](https://developers.openai.com/api/docs/guides/structured-outputs?api-mode=responses).

**Rejected alternative.** A locally hosted open-weight model would remove an external provider dependency but add model hosting, resource requirements and output-quality verification to a short assignment. A single gateway still leaves provider replacement possible later.

**Customer concern.** Cost, latency and prompt injection must not compromise launch rules or human authority. Bound call/token counts, run the three checks concurrently, record actual usage/rate snapshots and route suspicious/unknown analysis to review. Models receive no decision-mutating or approval tools. A fake adapter will run deterministic offline tests through the same interface. Provider/model access, current rates and a paid live smoke remain unverified and require separate live configuration; the current branch makes no model calls.

## Reproducibility and review

Runtime Python dependencies are pinned in `backend/requirements.lock`, test dependencies in `backend/requirements-dev.lock`, and frontend dependencies in `frontend/package-lock.json`. Python and Node build images are pinned by digest. Docker Compose is the agreed deployment mechanism. Keep the four decisions accurate as later branches add the planned features; review all twelve reason/alternative/customer-concern elements again before final submission.

For new behavioral work, write tests and observe the expected failures, explain those tests to the user, and wait for explicit approval before implementation. Documentation uses a completeness audit rather than artificial behavioral tests.
