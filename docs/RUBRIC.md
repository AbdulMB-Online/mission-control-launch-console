# Rubric scorecard

Scores are evidence-based self-assessments. Full points require every clause to be verified. A future feature, unrun check or missing runtime evidence earns no advance credit.

| Gate | Criterion | Maximum | Status | Verified score |
| --- | --- | ---: | --- | --- |
| G1 | Working README start/test commands | 10 | Passed | 10/10 |
| G2 | Four technology decisions | 10 | Passed | 10/10 |
| G3 | Filing, validation and persistence | 10 | Passed | 10/10 |
| G4 | Python launch limits | 15 | Passed | 15/15 |
| G5 | Severity and deadlines | 10 | Passed | 10/10 |
| G6 | Structured classification and fallback | 10 | Passed | 10/10 |
| G7 | Concurrent checks and injection protection | 10 | Passed | 10/10 |
| G8 | Draft/evaluation and human approval | 10 | Not started | Not assessed |
| G9 | Trace cards, tokens and Python costs | 10 | Not started | Not assessed |
| G10 | Complete offline suite through one model interface/fake | 5 | Not started | Not assessed |

**Fully verified total: 75/100.** MIS-5/PR #1 merged at `252b0a1`; MIS-8/PR #2 merge verified at `a6d8863`. Both parents are Done. Current branch: `abdul2shaik/mis-11-03-featureai-pipeline`, created from updated main after PR #2 merged. G6 and G7 are verified after separate explicit approvals. G8 requires its next red-test review and approval; it cannot receive full credit before the human-approval workflow in branch 4.

## G1: required evidence

- [x] README documents a working one-command start and one-command test run.
- [x] `make up` reaches a usable frontend and healthy backend through the real deployment.
- [x] `make test` runs the current backend/frontend tests, TypeScript checking and production build successfully.
- [x] Tests need no external API/key; external network is disabled during execution.
- [x] SQLite/migration readiness and foundation configuration have meaningful passing tests.
- [x] Expected behavioral red failures are observed before implementing each behavior; commands/results are recorded here.

Verified on 2026-11-11:

| Check | Observed result |
| --- | --- |
| Red backend run, `docker run --rm --network none -w /workspace/backend mission-control-tests:local python -m pytest` | 5 failed, 4 passed: missing runtime validation, disabled SQLite foreign keys and 503 instead of healthy readiness. Tests preceded implementation. |
| Red frontend run, `docker run --rm --network none -w /workspace/frontend mission-control-tests:local npm test` | All 3 failed: missing connected/error/retry UI in the minimal shell. |
| Final `make test` | Exit 0: 9 backend tests and 3 frontend tests passed; TypeScript checking and Vite production build passed. |
| `make up` | Exit 0: API and web containers healthy. |
| `GET http://localhost:8080/healthz` | HTTP 200: `{"status":"ok","service":"mission-control","provider":"fake"}` through Nginx. |
| Frontend deployment | HTML title/root plus both compiled JavaScript/CSS assets returned successfully; readiness/retry behavior separately verified by component tests. |
| Isolation | Compose test service uses `network_mode: none`, an empty API key and a temporary database; Pytest socket guard also enabled. |
| Database readiness | Version `0001`, foreign keys enabled, WAL and busy timeout verified; repeat migrations preserve existing file-backed data. |

G1 self-assessment: **10/10**, no unmet clauses for the README/start/test rubric criterion. This covers the implemented foundation; later features must preserve the commands and reopen G1 if they regress. Visual browser review was unavailable because access to the browser was not approved; no screenshot or visual-review claim is made. The HTTP deployment and component-test evidence above are verified.

Raw output stays in ignored `.local/validation/`. G2 may now begin.

### UI revision revalidation, 2026-11-12

The user requested the frontend-design skill and a redesigned interface. The skill was installed outside the repository. Before the rebuild, the two new behavior tests failed and the original three frontend tests passed. After implementation, `make test` exited 0: **9 backend and 5 frontend tests passed**, followed by TypeScript checking and the production build. `make up` exited 0 with healthy API/web services. Real HTTP checks verified the new HTML, JavaScript, CSS, a self-hosted WOFF2 font, the required font licenses, and the expected `/healthz` JSON.

The new tests verify an operator-triggered refresh and that an unavailable connection never invents launch clearance/readings. G1 is revalidated at **10/10**; cumulative verified score remains **10/100**. Visual browser review remains unverified; the tests and HTTP checks above are the evidence actually obtained.

## G2: technology decisions, 2026-11-12

| Required choice | Specific reason | Rejected alternative | Customer concern/response | Evidence |
| --- | --- | --- | --- | --- |
| Backend | Typed HTTP validation and async checks alongside independent Python rules | Django | Explainable decisions during model failure; pure rule ownership | TOOL_CHOICES.md, backend app/config/readiness source |
| Frontend | Typed component-based console and static Vite deployment | Next.js | Clear distinction between connection, missing readings and launch assessment | TOOL_CHOICES.md, App.tsx and five component tests |
| Database | Durable local transactions without a separate database service | PostgreSQL | Restart durability; volume, migrations and file-backed tests | TOOL_CHOICES.md, db.py, compose.yaml and database tests |
| Model | Planned structured-output adapter with separate draft/evaluation calls | Locally hosted open-weight model | Bounded cost/latency, injection review, deterministic authority and offline fake | TOOL_CHOICES.md; model integration clearly identified as a later milestone |

All **12 required decision elements** were audited against the actual foundation and the remaining plan. The model snapshot is proposed/configurable; live access, rates and model quality have not been tested, and no paid call is claimed. Official structured-output/model documentation was checked when finalizing the choice.

Repository audit: **39 required project files** exactly match the Git allowlist after keeping the implementation plan local and ignored. The assignment PDF, environment secrets, raw validation output, dependency/build directories and scratch-file examples are also ignored. Font license notices are required distribution material. The frontend-design skill itself is outside this repository. `git diff --check` passed. The README links the required tool-choice document and rubric evidence; it does not link the local planning file.

The application's code/configuration is unchanged since the successful 2026-11-12 run: **9 backend + 5 frontend tests**, TypeScript checking and production build passed; Compose services/HTTP checks passed. G2 changes are documentation and its exact ignore exception, so no artificial behavioral test was added.

G2 self-assessment: **10/10**, no unmet clauses. Cumulative full-gate score: **20/100**. No credit is awarded to G3-G10 yet, and no next branch starts before the first PR merges.

## User approval checkpoint for future TDD cycles

Added 2026-11-12: announce each new branch and ticket; write tests and observe expected failures; explain their intended behavior and why they failed; then **wait for explicit user approval before implementation**. Record approval in the existing ticket/PR. Silence is not approval. Historical branch-1 work predates this checkpoint. Present each branch for user review; documentation-only changes use completeness audits.

## G3 / MIS-9: red checkpoint, 2026-11-12

Branch: `abdul2shaik/mis-8-02-featurereport-processing`, created from merged main `252b0a1`. The user explicitly approved this batch with **“yes”** after the red-test explanation. The following records the checkpoint before implementation.

| Test group | Intended behavior |
| --- | --- |
| API filing/read/list | Persist all six fields, return server-owned UUID/UTC metadata, read records and paginate from stored ordering. |
| Input validation | Require every field; trim/bound text; reject invalid decimal strings, precision loss, nonfinite values and malformed/negative readings where prohibited. Return clear field messages without saving invalid data. |
| Trust boundary | Reject engineer-supplied verdict, approval, severity and timestamp metadata. |
| Safety-data distinction | Accept syntactically valid readings outside launch limits (including fuel 100.001) for later Python limit checking. No launch-rule implementation or G4 credit yet. |
| Persistence | Preserve saved input and metadata across a new application instance and an actual API process stop/start against the same file-backed database. |
| Form | Send six fields with decimal strings, show errors without losing inputs, allow network retry and prevent duplicate pending submissions. |

Observed with external network disabled: backend **40 failed / 9 passed**, frontend **4 failed / 5 passed**. All 14 existing foundation tests pass. New backend tests reach the live/in-process app but fail because report routes are absent (404/default error format); the real process starts successfully. New UI tests fail because the File report action/form is absent. No collection/import/socket setup errors are being counted as behavioral evidence.

Only tests, their shared fixture, exact ignore exceptions and this scorecard changed. Production code/migrations remain identical to merged main. No report implementation, G4/G5 work, failing-test commit or push has occurred. **Stop here for the user's test review and explicit implementation approval.** G3 earns no points yet; cumulative verified score stays **20/100**. Raw logs stay ignored in `.local/validation/`.

### G3: approved implementation and green assessment

After approval, implemented the six-field form, a typed API, an independent report use case and SQLAlchemy storage with migration `0002`. Exact decimal text and UTC metadata survive storage without float conversion. Validation rejects unknown privileged properties. The UI renders submitted notes as text, preserves inputs on failure and blocks duplicate submissions while pending.

| Verification | Observed evidence |
| --- | --- |
| `make test` | Exit 0: **49 backend + 9 frontend tests passed**, then TypeScript checking and Vite production build passed. External networking disabled; no API key. |
| API validation and filing | 38 report API cases cover all six fields, bounds, decimal precision, forged metadata, saved read/list ordering and understandable errors. |
| Restart durability | Two tests verify a new application instance and a real Uvicorn process stop/start against the same SQLite file. All six fields, ID and timestamp are retained. |
| Form | Four new component tests cover exact submission, field errors with retained values, network retry and duplicate-pending prevention. Five foundation tests still pass. |
| Deployment | `make up` exited 0, API and web healthy. Proxied `/healthz` returned expected fake-mode JSON; `/api/v1/reports` returned the real empty persisted collection. |
| Required-file audit | 58 required files exactly match the ignore allowlist. Local plan, PDF, secrets, databases, logs, generated outputs and dependencies remain ignored. `git diff --check` passed. |

G3 self-assessment: **10/10**, no unmet clauses. Cumulative verified score: **30/100**. Visual browser review remains unverified; no visual QA claim is made. This gate covers filing, validation and persistence only. Python verdicts, severity/deadlines and model processing receive no advance credit. MIS-8 remains in progress until G4 and G5 pass and its focused PR is reviewed and merged.

## G4 / MIS-10: red checkpoint, 2026-11-15

Same branch: `abdul2shaik/mis-8-02-featurereport-processing`. Passing G3 implementation committed at `2df2bf4`; it has not been pushed. The user approved this batch with **“lets continue”** after the expected-red explanation. The following records the checkpoint before implementation.

| New test group | Intended behavior |
| --- | --- |
| 13 boundary cases, each at the use-case and API boundaries | Wind 24.999/25/25.000 passes and 25.001 fails; temperature 3.999 fails and 4/4.001 passes; fuel 97.999 fails, 98/98.001/99.999/100 passes and 100.001 fails. Exact Decimal comparisons; all other readings stay safe. |
| Combined violations | Return every violated measurement in fixed wind/temperature/fuel order, for both low and high fuel. Each violation has observed value, operator, limit and a readable message. |
| Decision ownership | Compute before persistence without a model or DB; domain decision and violations are immutable. Report text requesting either GO or NO_GO cannot select the verdict. |
| Saved assessment | Filing, read and list expose the same decision/version/violations. Check actual stored columns, then reopen the app and verify the assessment remains intact. |
| Upgrade existing G3 reports | Migrate a real version-0002 database with an existing above-100 fuel report; preserve every original field and metadata while adding a Python assessment. Repeated startup keeps one report. |

`make test` observed **33 expected failures / 49 existing backend passes** with external networking disabled. Every new failure is a missing authoritative verdict assertion, not a missing import, collection error or failed process setup. The command stops at backend failures, so frontend/build were not rerun in this red cycle; their most recent G3 run passed 9 frontend tests, TypeScript checking and production build.

Only tests, their boundary fixture, exact ignore exceptions and this evidence changed since the passing G3 commit. No launch-rule source or migration has been added. The failing tests remain uncommitted and unpushed. G4 has no score yet; total stays **30/100**. Explain these results and **wait for explicit user approval before implementing G4**. G5 remains untouched. Raw output is ignored at `.local/validation/g4-red.log`.

### G4: approved implementation and green assessment

Implemented `domain/launch_rules.py` using only standard-library dataclasses, Decimal and literal types. The rule function accepts only the three readings, returns every violation in fixed order and produces an immutable result. The filing use case computes the decision before committing it with the report. Read/list deserialize the saved assessment rather than recalculating it or consulting a model. API schemas expose typed verdicts, rule version and exact decimal violation details.

Migration `0003` backfills existing reports using a frozen v1 rule snapshot and adds required assessment columns plus a verdict check constraint. It preserves original readings, notes, identity and timestamps. Historical migration rules are kept independent of future application/ORM changes.

| Verification | Observed evidence |
| --- | --- |
| `make test` | Exit 0: **82 backend + 9 frontend tests passed**, then TypeScript checking and production build passed. No external network or API key. |
| Boundaries and ownership | All 33 approved G4 cases pass: 13 boundary cases through each of use case/API, combined violations, immutability, adversarial report text, actual stored columns/restart and upgrade of existing data. |
| Previous gates | All 49 prior backend and 9 frontend tests remain green, including the real API process restart. |
| Deployment | `make up` exited 0; API/web healthy after migration. Proxied health and report collection returned HTTP 200 with the expected JSON. |
| Repository audit | 62 required files exactly match the ignore allowlist. `git diff --check` passed. Local plan, assignment PDF, validation output, dependencies, databases and secrets remain ignored. |

G4 self-assessment: **15/15**, no unmet clauses. Cumulative verified score: **45/100**. This is the launch-limit criterion only; model injection detection and the complete Director display retain their later gates. No G5 implementation or credit yet. MIS-10 and its parent MIS-8 remain in progress.

## G5 / MIS-10: red checkpoint, 2026-11-15

Same branch: `abdul2shaik/mis-8-02-featurereport-processing`. Passing G4 committed locally at `0ab919b`. The user approved this batch with **“lets start implementing”** after the expected-red review. The following records the checkpoint before implementation.

| New test group | Intended behavior |
| --- | --- |
| Before classification | File reports with classified severity null, effective high, provisional true and a five-minute deadline, for both GO and NO_GO readings. |
| Python severity mapping | Internal `ReportService.resolve_priority` maps high/medium/low to 5/15/30 minutes through a pure domain calculator and persists the result. It is not an engineer-facing endpoint. |
| Every violation overrides | Each of wind, temperature, low fuel and high fuel forces high/five minutes for every model severity. Preserve the classified severity separately from effective severity and leave safety facts intact. |
| Anchored time and fallback | Fixed UTC submission at 23:58; classification two days later cannot restart the clock. Cover midnight rollover and malformed/missing severity falling back to high. |
| Durable deadlines | Provisional and each resolved priority survive database reload/application restart. Upgrade existing version-0003 reports using their original submission time. |
| Trust boundary | Reject all five new severity/deadline properties when supplied by an engineer. |
| Display | Show provisional high priority with an explanatory label, or resolved priority without that label; render the exact server deadline as an accessible UTC time. |

Observed offline: backend **28 failed / 87 passed**, frontend **2 failed / 9 passed**. All 91 existing tests remain green; five new forged-metadata tests already pass due to strict submission validation. Failures are missing report priority/deadline fields, the absent internal priority-resolution operation and missing priority display. Tests collect successfully; no import or process-setup failures are counted.

Only the new tests and exact ignore exceptions changed after the passing G4 commit, plus this evidence. No G5 source or migration has been added. Failing tests remain uncommitted and unpushed. Raw logs stay ignored in `.local/validation/g5-backend-red.log` and `g5-frontend-red.log`. G5 earns no advance credit; verified total remains **45/100**. Explain these failures and **wait for explicit user approval before implementing G5**.

### G5: approved implementation and green assessment

Implemented the pure `domain/severity.py` calculator with no database, model or current-clock dependency. Submission commits provisional high priority with the report and launch assessment. Internal classification resolution preserves the original timestamp and safety facts, computes effective priority in Python, and writes only the five priority fields. No public endpoint permits an engineer to select severity or deadline.

Migration `0004` adds durable priority columns and checks the severity/deadline mapping and NO_GO override. Existing reports receive provisional high priority with deadlines based on their original timestamps. The UI validates priority response fields, displays the returned UTC time and distinguishes provisional from resolved priority using the established console design. The later AI pipeline will call the internal resolution operation; no model processing is claimed in this branch.

| Verification | Observed evidence |
| --- | --- |
| `make test` | Exit 0: **115 backend + 11 frontend tests passed**, followed by TypeScript checking and production build. External networking disabled; no API key. |
| Mapping and overrides | All three severities map to 5/15/30 minutes. Each of four limit violations overrides every classification to high/five minutes. Invalid or missing severity falls back high. |
| Time and persistence | Fixed UTC clock, midnight rollover and two-day classification delay tests pass. Both provisional and all resolved priorities survive reload. Migration uses the original report timestamp. |
| UI and trust boundary | Provisional/resolved component tests pass with exact server datetime/UTC labels. All five engineer-supplied priority properties are rejected. Existing form/retry/pending and foundation tests remain green. |
| Deployment | `make up` exited 0; API/web healthy after migration. Proxied health and report collection returned HTTP 200 with expected JSON. |
| Repository audit | 67 required files exactly match the allowlist; source whitespace and `git diff --check` pass. Local plan, PDF, raw evidence, dependencies, generated builds, databases and secrets remain ignored. |

G5 self-assessment: **10/10**, no unmet clauses. Cumulative verified score: **55/100**. G3/G4 remain fully verified. Browser visual review remains unverified; component tests and HTTP deployment checks are the evidence obtained. Branch 2 is ready for review. Keep MIS-8 in progress until its PR merges; then start the AI branch from updated main and repeat the explicit test-review approval workflow. G6–G10 have no advance credit.

## G6 / MIS-12: red checkpoint, 2026-11-15

Verified PR #2 merged at `a6d8863`, containing the complete `1ab5c42` branch head. Fast-forwarded local main, then created Linear's exact branch `abdul2shaik/mis-11-03-featureai-pipeline`. The user explicitly approved this G6 batch with **“yes”** after the red-test review. The following records the checkpoint before implementation.

| Test group | Intended behavior |
| --- | --- |
| Structured classification: 34 cases | Accept all seven subsystem values and three severities; preserve Python safety facts; keep every violation high; reject invalid enums/types, missing fields, blank/overlong rationale and extra authority fields. |
| Conservative failures | Refusal, incomplete response, malformed output, timeout and provider failure produce unknown/high fallback and a visible review reason. Preserve available usage; sanitize errors; propagate cancellation. |
| Prompt boundary and persistence | Keep report text outside system instructions, use a strict three-field schema and a 300-token cap, persist classification/priority/review metadata and token usage across restart. |
| Gateway/fake: 9 cases | One injected async interface; key-free default fake; stage/round scripts independent of call order; payload, refusal, malformed output, usage, transport-failure and event-gate simulation. Scripted draft responses exercise the generic fake contract only; no drafting loop is implemented. |
| OpenAI adapter: 14 cases | Mock HTTP transport; strict Responses schema, bounded timeout/output, no tools, no stored provider response, untrusted user data separated from instructions. Refusal/incomplete/malformed output retain usage; HTTP 401/429/503 and timeouts have no hidden retry or fake success; cancellation propagates; invalid/missing usage remains unknown. |

`make test` observed **57 expected failures / 115 existing backend passes** with external networking disabled. Classification cases fail because the classification operation is absent; gateway cases fail because the contract/lifespan adapter is absent. No collection, missing dependency/import or process-startup failure is counted. The command stops before frontend/build; their most recent passing G5 run had 11 frontend tests plus TypeScript checking and production build.

The strict request and refusal/incomplete cases follow the [official structured-output guide](https://developers.openai.com/api/docs/guides/structured-outputs) and [Responses API contract](https://developers.openai.com/api/reference/resources/responses/methods/create). OpenAI adapter tests intercept HTTP in memory and use only an explicit dummy key. No live call or model quality claim is made.

Only three test files and their exact ignore exceptions changed, plus this scorecard. Production source, migrations and dependency locks remain identical to merged main. Required-file audit: 70 files match the allowlist. Raw log stays ignored at `.local/validation/g6-red.log`; local plan, PDF, secrets, dependencies and generated output remain ignored. Tests remain uncommitted and unpushed. G6 is unassessed and total remains **55/100**. Explain this test batch and **wait for explicit user approval before implementation**. No G7/G8 work yet.

### G6: approved implementation and green assessment

Implemented one injected async `LLMGateway` contract, immutable request/result metadata, a stage/round-scripted fake, and the sole OpenAI-client adapter. The application revalidates strict classification output and falls back to unknown/high with explicit review reasons. It recalculates effective priority in Python, preserves original safety facts and commits classification, review metadata and usage trace together. Database sessions are closed before awaiting model output.

The current official SDK uses HTTPX2, so the adapter test harness was adjusted to intercept HTTPX2 instead of HTTPX; all behavioral assertions were retained. Locked SDK 3.51.0 and its dependencies without upgrading existing locked packages. Live gateway creation is explicit; the fake never constructs a real client. Both gateways close through the application lifespan. There are no tools or model-accessible approval operations.

| Verification | Observed evidence |
| --- | --- |
| `make test` | Exit 0: **172 backend + 11 frontend tests passed**, followed by TypeScript checking and production build. External networking disabled, no real key or provider call. |
| Classification | All 34 cases pass: seven subsystems, all severities, every violation override, invalid/extra-authority payloads, failures/refusals/incomplete replies, prompt isolation, cancellation and persisted result/usage after restart. |
| Fake and interface | All nine gateway cases pass, including per-stage/per-round scripts and event gates independent of call order. |
| Provider contract | All 14 OpenAI adapter cases pass through mocked HTTP: strict Responses schema, bounded output/timeouts, no tools, no hidden retries, explicit errors, retained usage and cancellation. |
| Previous gates | All 115 previous backend and 11 frontend tests stay green, including real API process restart and upgrades of historical databases. |
| Deployment | `make up` exited 0; API/web healthy. Proxied health and report collection return HTTP 200 with expected JSON after migration 0005. |
| Repository audit | 77 required files exactly match the allowlist. `git diff --check` passes; scratch compiler files, local references, raw logs, secrets and generated outputs remain ignored. |

G6 self-assessment: **10/10**, no unmet clauses for classification/gateway/fallback. Cumulative verified score: **65/100**. Real provider access, model quality and current prices remain unverified. Classification is an internal operation; automatic scheduling, three concurrent checks and drafting/evaluation are later work on this branch. G7/G8 have no advance credit. Parent MIS-11 remains in progress.

## G7 / MIS-13: red checkpoint, 2026-11-15

Same branch: `abdul2shaik/mis-11-03-featureai-pipeline`. Passing G6 committed locally at `aa1eeac`. The user explicitly approved this G7 batch with **“yes”** after the red-test explanation. The following records the checkpoint before implementation.

| New tests | Intended behavior |
| --- | --- |
| Event barrier | All three gateway calls must start before any is released; no timing-based performance assertion. All three traces share a parallel-group ID. |
| Partial/complete failures | A timeout, refusal, incomplete output or invalid schema leaves that check unknown/error and retains successful siblings and available usage. All failed checks require review. |
| Detection and authority | Detect missing information and calm/urgent/panic tone without rewriting severity or deadlines. Preserve earlier review reasons. Flagged and missed injection detection cannot select either GO or NO_GO, alter violations or create approval. |
| Prompt/schema boundary | Report text remains untrusted user data; each check uses a strict schema and a 500-token cap. Extra verdict/approval fields are rejected. |
| Cancellation and persistence | Cancel every outstanding call when the group is cancelled. Persist results, usage, review reasons and parallel grouping across restart without sharing sessions between model calls. |
| Interim display | Prominent human-review alert plus all three check groups. Unavailable is distinct from clear; completed siblings remain visible. Model HTML is rendered as text. |

Observed offline: **23 backend failures / 172 passes**, **3 frontend failures / 11 passes**. Every existing G1–G6 test passes. Backend failures are the absent `run_checks` operation; frontend failures are the absent check groups/review alert. No import/collection/setup errors are counted. Production source and dependencies remain identical to the passing G6 commit.

Only three tests, exact ignore exceptions and this evidence changed. Required-file audit: 80 files match the allowlist. Failing tests are uncommitted and unpushed. Raw logs stay ignored in `.local/validation/g7-backend-red.log` and `g7-frontend-red.log`. G7 has no advance credit; verified total remains **65/100**. Explain the test batch and **wait for explicit user approval before implementing G7**. G8 remains untouched.

### G7: approved implementation and green assessment, 2026-11-16

Implemented guarded concurrent checks with `asyncio.gather`, strict schemas and independent error outcomes. Every task receives its own report-data object and no database session. Group cancellation cancels and joins all outstanding tasks. The caller persists three separate outcome rows, usage traces and their shared group after collection, together with the union of review reasons. Check storage cannot write launch readings, verdicts, severity/deadlines or approvals. Read/list load saved outcomes explicitly without ORM lazy-loading during model calls.

The report UI shows all three advisory results and a prominent human-review warning. Unavailable checks are distinct from clear results. Submitted notes and model explanations use React text rendering. The fake gateway supports all three checks as labeled simulations; the live adapter still has no approval or decision-mutating tools.

| Verification | Observed evidence |
| --- | --- |
| `make test` | Exit 0: **195 backend + 14 frontend tests passed**, followed by TypeScript checking and production build. Offline with no real key or live provider call. |
| Concurrency and isolation | Event-barrier test proves all three calls start before any finishes; successful siblings survive timeouts/refusals/incomplete/invalid replies. Cancellation, shared grouping and original review reasons are covered. |
| Safety and display | Safe/unsafe readings with flagged or missed injection retain Python verdicts/violations. Panic does not rewrite priority. Unknown checks require review; model HTML stays text. All 26 new G7 tests pass. |
| Persistence | Check outcomes, usage, review reasons and group ID survive application restart. Historical migrations and all earlier tests remain green. |
| Default fake smoke | Isolated temporary SQLite container passed filing → classification → concurrent checks → saved read: NO_GO retained, injection flagged, human review required, three persisted checks. No application-volume data created. |
| Deployment | `make up` succeeded with API/web healthy; resumed proxied health/report reads return HTTP 200 and expected JSON after migration 0006. |
| Repository audit | 84 required files exactly match the allowlist; source whitespace and `git diff --check` pass. Local references, scratch files, logs, secrets and generated output stay ignored. |

G7 self-assessment: **10/10**, no unmet clauses. Cumulative verified score: **75/100**. Browser visual review and real model quality remain unverified; the evidence is component tests, mocked transport, fake smoke and HTTP deployment checks. Scheduling/recovery and drafting/evaluation are remaining branch-3 work; human approval completes G8 in branch 4. Parent MIS-11 stays in progress.
