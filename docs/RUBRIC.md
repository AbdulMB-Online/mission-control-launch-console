# Rubric verification

Evidence-based self-assessment against the original assignment PDF, pages 2–3. The ten criteria total **100/100**; this is not a guarantee of an external grader's score. No credit is based on a future feature or a paid-model claim. Final branch: `abdul2shaik/mis-17-05-choretesting-docs`.

## All 100 grading points

| Gate | Mandatory criterion | Earned / max | Concrete evidence |
| --- | --- | ---: | --- |
| G1 | One working start command and one working test command | 10/10 | [README](../README.md), [Makefile](../Makefile). `make up` reaches healthy API/web; `make test` passes all 320 tests, type checking and production build. Both also pass from clean checkout `fde7e2c`. |
| G2 | Backend, frontend, database and model: specific reason, rejected alternative and customer concern for each | 10/10 | [TOOL_CHOICES.md](../TOOL_CHOICES.md): all twelve elements audited against the implemented stack. |
| G3 | Form sends every field, clear validation, saved reports survive restart | 10/10 | [Form](../frontend/src/features/reports/ReportForm.tsx), [schemas](../backend/app/api/schemas.py), [storage](../backend/app/infrastructure/repository.py); [API](../backend/tests/test_report_api.py), [form](../frontend/src/features/reports/ReportForm.test.tsx), [persistence](../backend/tests/test_report_persistence.py) and [system restart](../backend/tests/test_system_workflow.py) tests. |
| G4 | Python verdict/violations, exact limits and just-outside cases | 15/15 | [Pure rules](../backend/app/domain/launch_rules.py), [unit boundaries](../backend/tests/test_launch_rules.py), [API boundaries](../backend/tests/test_launch_rules_api.py). Wind ≤25, temperature ≥4, fuel 98–100 inclusive; any violation yields NO_GO. |
| G5 | Severity deadlines; any violation forces high | 10/10 | [Priority rules](../backend/app/domain/severity.py), [unit](../backend/tests/test_severity.py), [API](../backend/tests/test_severity_api.py) and [display](../frontend/src/features/reports/ReportPriority.test.tsx) tests. High/medium/low map to 5/15/30 minutes from the original submission. |
| G6 | Structured classification, validation and safe fallback | 10/10 | [Schemas](../backend/app/application/ai_schemas.py), [classification use case](../backend/app/application/reports.py), [adapter](../backend/app/infrastructure/llm/openai_gateway.py); [classification](../backend/tests/test_classification.py) and [adapter](../backend/tests/test_openai_gateway.py) tests. Invalid/refused/incomplete/failed responses fall back to unknown/high with review. |
| G7 | Three concurrent checks; hidden instructions flagged for review without verdict authority | 10/10 | [Concurrent checks](../backend/app/application/pipeline.py), [event-barrier tests](../backend/tests/test_parallel_checks.py), [injection regression](../backend/tests/test_prompt_injection.py), [check UI](../frontend/src/features/reports/ReportChecks.test.tsx). A failed check preserves siblings; missed detection also cannot change Python facts. |
| G8 | At most three draft/evaluation rounds, feedback propagation, human-only approval | 10/10 | [Loop](../backend/app/application/briefings.py), [approval](../backend/app/application/approvals.py), [authentication](../backend/app/api/auth.py); [loop](../backend/tests/test_briefing_loop.py), [approval API](../backend/tests/test_approval_api.py), [concurrency](../backend/tests/test_approval_concurrency.py), [Director UI](../frontend/src/features/reports/DirectorReview.test.tsx) and browser tests. Evaluator acceptance only selects a pending draft. |
| G9 | One console card per step with tokens; Python cost calculation | 10/10 | [Trace UI](../frontend/src/features/reports/ExecutionTrace.tsx), [Decimal costs](../backend/app/domain/costs.py); [23 arithmetic cases](../backend/tests/test_costs.py), [trace persistence/API](../backend/tests/test_trace_api.py), [trace UI cases](../frontend/src/features/reports/ExecutionTrace.test.tsx). Exact cached-subset example costs $0.001065; unknown prices/usage stay visibly incomplete. |
| G10 | Passing tests without network/API key through one gateway and fake | 5/5 | [Gateway contract](../backend/app/application/ports.py), [fake](../backend/app/infrastructure/llm/fake_gateway.py), [test container](../compose.yaml), [runner](../scripts/test.sh); [HTTP/process](../backend/tests/test_system_workflow.py), [browser](../backend/tests/test_browser_workflow.py) and [smoke](../backend/tests/test_deployment_smoke.py) tests. **289 Pytest + 31 Vitest tests pass** with external networking disabled and no real key. |

**Total: 100/100.** All earlier gates were rechecked after each later feature and during the final clean-checkout run. The final PR remains subject to review and merge.

## Functional and authority requirements

| Requirement | Implementation and verification |
| --- | --- |
| All six input fields and clear errors | Name/station/note are trimmed/bounded. Decimal strings preserve readings exactly; malformed, nonfinite, overprecision and forged fields are rejected with field messages. Form failure retains entries. G3 tests and both browser journeys verify filing. |
| Persistent SQLite/SQLAlchemy storage | Reports, decisions, priorities, checks, draft/evaluation history, traces, cost snapshots and approvals are migrated and stored. File-backed, real process and preserved-volume Compose restart checks pass. |
| Deterministic launch rules | Python receives only readings for the verdict. Models cannot write readings, verdicts or violations. Limit violations force effective high even when the classifier says low. G4/G5/injection tests cover the boundary. |
| One model interface | Classification, checks, drafts and evaluations all use `guarded_generate` and `LLMGateway`. Only the OpenAI adapter constructs the SDK client or sends a Responses request. Adapter transport is intercepted in tests; system factories reject live adapter construction. |
| Concurrent advisory checks | Hidden instructions, missing details and panic/urgency run concurrently with separate schemas and failure states. Event barriers prove overlap. Tone does not rewrite Python priority; unknown is never displayed as clear. |
| Bounded draft/review loop | Separate calls alternate; every revision receives full evaluator feedback and the preceding draft. Stop on acceptance or round three. Evaluation failure/exhaustion selects the latest valid draft for review; draft failure leaves approval unavailable. |
| Human approval | Configured credentials are checked on the backend; identity/time are server-owned. Only a completed report's selected pending draft is eligible. Review findings require acknowledgment. Foreign/missing/nonselected drafts, spoofed metadata, unfinished/failed work and duplicates are rejected. Concurrent requests save one approval and one trace. |
| Approval never grants launch clearance | Approving a NO_GO briefing leaves readings, verdict, violations, severity, deadline, checks and draft history unchanged. UI confirmation says that briefing approval does not authorize launch. |
| Complete Director console | Original data, canonical verdict/violations, effective priority/deadline, all checks, selected/prior drafts, feedback and pending/approved state are visible. Loading/errors/unavailable states are explicit. Active reports poll; overdue display uses the unchanged server deadline. |
| Trace, tokens and costs | Every executed Python/model/approval step has a persistent identity and card, including all rounds and failed replies. Parallel checks share a group. Running calls have no invented finish time or cost. Python sums exact saved amounts, with cached tokens a subset of input and reasoning already in output. Fake mode is explicitly simulated. |
| Restart and interruption | Queued work resumes; interrupted work becomes failed with partial history retained and unknown unfinished usage. Completed/failed work does not silently repeat potentially billed calls. [Lifecycle](../backend/tests/test_pipeline_lifecycle.py) and real hard-crash tests pass. |
| Untrusted data | Notes, feedback and model summaries render as text. Schemas reject decision/approval fields. Director credentials are cleared after requests and never stored or sent to models. Browser tests verify markup cannot execute and browser storage stays empty. |

## Final commands and observed results

Verified on 2026-11-17. Image/dependency/browser preparation may use networking; test execution does not.

| Check | Result |
| --- | --- |
| `make test` | Exit 0: **289 backend + 31 frontend = 320 tests**, no skips; TypeScript and Vite production build pass. Test service has `network_mode: none`, an empty API key and a temporary database. |
| Desktop Chromium GO journey | Engineer form → queued/processing state → three checks → feedback into draft 2 → pending human state → authenticated confirmation → approval → reload persistence. All requests stay on loopback. |
| Mobile Chromium injection NO_GO journey | Flagged hidden instructions, unchanged NO_GO, mandatory review acknowledgment, rejected credentials with cleared password, successful explicit approval, safe model markup and unchanged state after reload. No horizontal overflow or stored credentials. |
| Four real HTTP/process cases | Clean/injection full journeys, full approved-record process restart, and a hard crash during a model call all pass. Crash recovery closes the same trace without repeating the call. |
| `make up` and `make smoke` through Nginx | Healthy API/web; smoke files a fake NO_GO report, explicitly approves its briefing and verifies eleven trace steps. Bad credentials and live mode are rejected in regression tests. |
| Compose stop/start | Isolated `mission-control-acceptance` services restart with the same named volume. Full report list and trace JSON match before/after, including approval identity/time, results, costs, usage and IDs. |
| Clean checkout `fde7e2c` | Detached checkout with no `.env` or added branch. Commands use container Python/Node. `make test`, `make up` and `make smoke` all exit 0. Isolated project/port overrides avoid conflicts with the normal app. Final later edits change documentation only. |
| Historical rates and migration | Scripted usage totals exactly $0.006390 for six calls. Amounts/rates survive process restart and rate changes. Isolated 0008 → 0009 migration preserves report/check/draft/approval/trace records and leaves uncaptured historical prices unknown. |
| Visual review | Inspected captured desktop review and mobile confirmation screenshots. The verdict, findings, trace and modal controls remain legible. Screenshots and browser profiles remain local, outside Git. |
| Dependencies and CI | Existing dependency pins are unchanged; only Playwright 1.64.1/pyee 14.0.0 were added for testing. Matching Chromium is installed at build time. [CI](../.github/workflows/ci.yml) runs the same test/start/smoke commands; remote CI status is not claimed before the final PR runs. |
| Required-file audit | All **110** tracked/eligible files exactly match `.gitignore` exceptions. No PDF, local plan, credentials, database, dependency tree, screenshots, raw logs or generated build is tracked. `git diff --check` passes. |

Raw outputs and screenshots are ignored under `.local/validation/`. The tracked tests and commands reproduce this evidence.

## TDD and criterion progression

Tests preceded each behavioral implementation. After the user's checkpoint rule was introduced, each expected-red batch was explained and explicitly approved before implementation. Documentation uses a completeness audit. All red cases below are green in the final suite; raw logs remain local and full historical notes are retained in Git history.

| Batch | Observed expected failures | Implementation approval / final outcome |
| --- | --- | --- |
| G1 foundation | 5 backend / 3 frontend | Foundation red → green; predates the later explicit approval rule. |
| UI revision | 2 frontend | Requested frontend-design revision; connection/refresh behavior verified. |
| G2 tool choices | Documentation audit | All twelve required elements present; no artificial behavioral test. |
| G3 filing | 40 backend / 4 frontend | User: “yes”; filing, validation and persistence green. |
| G4 launch rules | 33 backend | User: “lets continue”; every boundary and violation green. |
| G5 priority/deadlines | 28 backend / 2 frontend | User: “lets start implementing”; mappings/overrides/anchored deadlines green. |
| G6 classification/gateway | 57 backend | User: “yes”; strict schema/fallback/adapter tests green. |
| G7 concurrent checks | 23 backend / 3 frontend | User: “go ahead”; concurrency, failure isolation and injection boundary green. |
| G8 bounded loop | 20 backend | User: “go ahead”; feedback and at most three rounds green. |
| G8 lifecycle | 7 backend | User: “ok go ahead”; scheduling, recovery and shutdown green. |
| G8 human approval | 22 backend / 9 frontend | User: “go”; auth, review, concurrency, persistence and Director UI green. G8 earned points only after this clause was complete. |
| G9 costs/trace | 34 backend / 6 frontend | User: “move on”; exact costs, persisted snapshots and cards green. |
| Overdue display | 2 frontend | User: “ok”; active work past the unchanged deadline is flagged. |
| G10 smoke/integration | 3 backend; 4 new HTTP/process cases already passed | User: “go on”; smoke command and isolated browser tooling added. Browser cases passed the existing app without an application repair. |

## Five sequential branches

Each branch started from updated merged main and used its parent Linear issue's generated name. No extra implementation branch or ticket was added. Each parent has two subtickets.

| Milestone | Canonical branch | Gate completion / PR status |
| --- | --- | --- |
| MIS-5 | `abdul2shaik/mis-5-01-choreproject-setup` | G1/G2; PR #1 merged at `252b0a1`. |
| MIS-8 | `abdul2shaik/mis-8-02-featurereport-processing` | G3/G4/G5; PR #2 merged at `a6d8863`. |
| MIS-11 | `abdul2shaik/mis-11-03-featureai-pipeline` | G6/G7 and G8 loop/lifecycle; PR #3 merged at `ef32061`. No advance G8 credit. |
| MIS-14 | `abdul2shaik/mis-14-04-featuredirector-console` | Complete G8, then G9; PR #4 merged at `55dfb71`. |
| MIS-17 | `abdul2shaik/mis-17-05-choretesting-docs` | G10, final documentation and revalidation; fifth focused PR prepared, pending review/merge. |

## Scope and limits

All mandatory rubric and user functional requirements above are implemented. Additional engineering safeguards—versioned migrations/rates, credential validation, atomic approval, interruption recovery and browser regression coverage—support those requirements and earn no extra points.

The demonstrated deployment is a local, single-worker application with one configured Director identity. Multi-user SSO, multi-replica hosting and production TLS infrastructure are outside the assignment scope. Real OpenAI access, paid usage and live writing/injection-detection quality have not been verified. Fake and mocked-provider results are never presented as live-model evidence.
