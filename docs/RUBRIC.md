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
| G8 | Draft/evaluation and human approval | 10 | Passed | 10/10 |
| G9 | Trace cards, tokens and Python costs | 10 | Passed | 10/10 |
| G10 | Complete offline suite through one model interface/fake | 5 | Not started | Not assessed |

**Fully verified total: 95/100.** PR #1 merged at `252b0a1`, PR #2 at `a6d8863`, and PR #3 verified at `ef32061`. MIS-5/MIS-8/MIS-11 are Done. Current branch: `abdul2shaik/mis-14-04-featuredirector-console`, created from updated main after PR #3 merged. G8 is complete through MIS-15 at `2c32bdd`; G9 is complete through MIS-16 at `2e87175`. Branch 4's final acceptance checks pass and it is ready for PR review; its parent remains in progress until merge. G10/final integration belongs to branch 5 after that merge.

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

## G8 / MIS-11: bounded-loop red checkpoint, 2026-11-16

Same branch: `abdul2shaik/mis-11-03-featureai-pipeline`. Passing G7 committed locally at `45fdcf2`. The user approved this G8 batch with **“go ahead”** after the expected-red review. The following records the checkpoint before implementation. This batch covers the internal briefing loop and persistence; scheduling/recovery has a separate test review before branch-3 completion.

| New tests | Intended behavior |
| --- | --- |
| Accepted in rounds 1, 2 or 3 | Separate draft/evaluation requests, exact alternating order, stop immediately on acceptance, select one valid draft and keep approval pending for a human. |
| Feedback and context | Pass the full evaluator feedback and preceding draft into the next round; provide original report, canonical Python decision and all check results. Caps: draft 700, evaluation 400. Strict schemas contain no approval/decision authority. |
| Three rejections | Stop after round 3 (ten total calls including classification/checks), retain the latest valid draft and mark exhausted evaluation for human review. Never round 4. |
| Evaluator failure | Invalid/refused/incomplete/timed-out evaluation retains the current valid draft, flags review and stops; it does not approve or silently accept the draft. |
| Draft failure | Invalid/refused/provider-failed draft leaves approval unavailable. A second-round failure retains history without selecting an earlier draft. Preserve safety facts and usage. |
| Durable human boundary | Save each valid draft before evaluation; persist rounds, evaluations, usage traces and selected/pending state across restart. Deceptive text or feedback cannot change verdicts or become human approval. |

Offline run observed **20 expected new failures / 195 existing backend passes**. Every new failure is the missing `generate_briefing` operation; classification and checks execute successfully first. No import/collection/setup failures. The command stops before frontend/build; the latest G7 run passed all 14 frontend tests, TypeScript checking and production build.

Only the new test file and its exact ignore exception changed after G7, plus this evidence. Production source, migrations and dependencies remain identical to `45fdcf2`. Required-file audit: 85 files match the allowlist. Failing tests remain uncommitted/unpushed; raw output stays ignored in `.local/validation/g8-loop-red.log`. G8 earns no advance credit; total remains **75/100**. Explain these tests and **wait for explicit user approval before implementing this batch**. No G9 work.

### G8 bounded loop: approved implementation verified

Implemented immutable draft records, strict draft/evaluation schemas and the three-round loop. Each valid draft commits before a separate evaluation call; revisions receive the complete feedback and preceding draft. Evaluation error selects the latest valid draft for human review; draft failure selects nothing, including after an earlier successful round. Terminal selection and report state commit together. A partial unique index permits at most one selected draft; approval remains a derived pending state, with no model-writable approval flag.

Migration 0007 adds report status/error and round metadata plus briefing history. It adds report columns directly instead of rebuilding the parent table, preserving existing checks/traces and their cascade relationships. Storage updates cannot alter readings, verdicts, violations, priority or timestamps. No database transaction spans a model call.

| Verification | Observed evidence |
| --- | --- |
| `make test` | Exit 0: **215 backend + 14 frontend tests passed**, followed by TypeScript checking and production build. Offline; no real provider call. |
| Loop cases | All 20 new cases pass: acceptance in rounds 1/2/3, feedback/context propagation, max three rounds, evaluation failures, draft failures, no selection of earlier history after later failure, deceptive text and persisted history/usage. |
| Human boundary | Accepted evaluation, exhausted revisions and evaluator errors leave selected drafts pending human approval. Draft errors leave approval unavailable. G8 remains unassessed until branch-4 human approval is complete. |
| Default fake smoke | Isolated temporary SQLite container completed filing → classification → checks → draft/evaluation in six fake calls. NO_GO remained intact, one accepted draft was selected, human review remained required and approval pending. |
| Deployment | `make up` succeeded with healthy API/web; proxied health/report reads passed after migration 0007. |
| Repository audit | 88 required files match the allowlist; whitespace and `git diff --check` pass. Local references, logs, scratch files, secrets and generated output remain ignored. |

This approved sub-batch is complete; **verified rubric total remains 75/100**. Scheduling/restart recovery is the next test-review checkpoint on the same branch. Parent MIS-11 stays in progress; no G9 work begins.

## G8 / MIS-11: scheduling/recovery red checkpoint, 2026-11-16

Same branch: `abdul2shaik/mis-11-03-featureai-pipeline`. Passing bounded loop committed locally at `57c6b6a`. The user confirmed this work belongs to branch 3 and approved it with **“ok go ahead”**, then resumed after interruption. The following records the checkpoint before implementation.

| New tests | Intended behavior |
| --- | --- |
| Responsive filing and serialization | Filing returns 201 with queued state while classification is gated; health/read/filing remain available. Process one report at a time, with that report's three checks still concurrent. |
| Duplicate scheduling | Repeated scheduling cannot claim an already-processing/completed report or repeat its model calls. |
| Commit-before-scheduling recovery | Startup finds and processes reports saved as queued even when the previous process never scheduled their task. |
| Interrupted work | Startup marks processing reports failed/interrupted, retains checks/draft history and closes running traces with unknown usage. Do not repeat potentially billable calls. |
| Terminal records and shutdown | Completed/failed reports never rerun on restart. Shutdown cancels and joins active work before closing gateway/database; preserve report facts and unavailable approval. |
| Timeout and worker resilience | Enforce a total pipeline timeout without resetting the submission deadline. Unknown scheduled IDs do not break later jobs. |

Observed offline: **7 expected failures / 217 passes**. All previous 215 backend tests pass, plus two new terminal-record restart cases. Failures are absent runner wiring, classification never starting automatically and processing records not being recovered. There are no import/collection/setup errors. The command stops before frontend/build; the most recent bounded-loop run passed 14 frontend tests, TypeScript checking and production build.

The shared settings fixture now requests `pipeline_autostart=False`, and the filing-only subprocess test sets the matching environment flag, so earlier tests can continue to inspect pre-processing states explicitly. Dedicated lifecycle tests request autostart. The setting is not implemented yet (currently ignored); these test preparations do not alter application behavior.

Only tests/shared test setup, their exact ignore exception and this evidence changed after the passing loop commit. The README development-rules section was removed in response to the user's question; operational workflow remains documented in Linear and this scorecard. No scheduling application code, migration or dependency change. Required-file audit: 89 files match the allowlist; new tests remain uncommitted/unpushed. Raw output stays ignored at `.local/validation/g8-lifecycle-red.log`. **Wait for explicit user approval before implementing this batch.** Verified total stays **75/100**; G8 remains unassessed and G9 untouched.

### G8 scheduling/recovery: approved implementation verified

Implemented a tracked async queue worker in the application layer. The API schedules only after the report commit and returns the immutable queued snapshot immediately. Storage atomically claims only queued reports; unknown, processing and terminal IDs do not repeat calls. One report runs at a time while its three checks remain concurrent. Startup reschedules queued work and marks interrupted processing failed, preserving committed history. Cancellation/timeout closes running traces as unavailable rather than inventing usage. Shutdown joins the worker before gateway/database cleanup.

The default total timeout is 270 seconds, validated positive and capped at 270. Autostart defaults on; focused filing/unit tests explicitly disable it, while lifecycle tests exercise the actual automatic path. No new dependency or migration was needed. The README development-rules section remains removed as requested.

| Verification | Observed evidence |
| --- | --- |
| `make test` | Exit 0: **224 backend + 14 frontend tests passed**, then TypeScript checking and production build. Offline, with fake responses or mocked HTTP and no real provider call. |
| Lifecycle | All nine cases pass: responsive filing/reads, serialized reports, duplicate claims, commit-before-schedule recovery, interrupted history/trace preservation, terminal-record non-reexecution, shutdown cancellation, total timeout and worker resilience. |
| Real HTTP/restart smoke | Isolated Uvicorn process and temporary SQLite: queued HTTP 201 → full fake pipeline completed; NO_GO, three checks, selected/evaluated briefing, pending approval and timestamps survived process restart. Six model traces remained unchanged after restart. |
| Deployment | `make up` succeeded; API/web healthy and proxied `/healthz` returned expected fake-mode JSON. |
| Repository audit | 90 required files exactly match the allowlist; whitespace and `git diff --check` pass. Local plan/PDF, scratch files, raw output, dependencies, databases, secrets and generated builds stay ignored. |

Branch 3 implementation is ready for focused PR review; parent MIS-11 stays in progress until merge. **Verified rubric total remains 75/100**: G6 10/10 and G7 10/10, with G8 deliberately incomplete until human approval in branch 4. Browser visual review, live model quality and current rates remain unverified. Do not start branch 4 before this PR merges; continue G8 there before G9.

## G8 / MIS-15: human-approval red checkpoint, 2026-11-16

Verified PR #3 merged at `ef32061`, containing reviewed branch head `9af6a47`. Fast-forwarded main and created Linear's exact branch `abdul2shaik/mis-14-04-featuredirector-console`. The user explicitly approved these 31 expected failures with **“go”** before implementation. The following records the original red checkpoint.

| New tests | Intended behavior |
| --- | --- |
| Director authorization | Backend validates configured HTTP Basic credentials; absent/bad credentials and client role headers cannot approve. Response identity/time come from the server; forged body metadata is rejected. |
| Eligibility and acknowledgment | Require a completed pipeline and selected valid draft. Reject queued/processing/failed, missing/foreign/nonselected drafts and duplicate approvals. Strict boolean acknowledgment required for injection, exhausted evaluations and evaluation errors; snapshot reasons with approval. |
| Durable safety boundary | Human approval of a NO_GO briefing does not alter readings, verdict, violations, severity, deadline, history or clearance. Evaluator acceptance alone creates no approval. Approval and its deterministic trace survive restart. |
| Concurrent requests | Two simultaneous valid requests produce exactly one 201, one 409, one approval row and one approval trace. |
| Director review UI | Inspect original data, canonical verdict/violations/deadline, selected and earlier drafts, feedback and all checks. Pending human approval is separate from evaluator status. Explicit confirmation uses credentials and review acknowledgment; no credential storage; rejected requests do not mark approved. |
| Active states and untrusted text | Poll selected processing reports, stop polling on unmount, disable unavailable approval and render model markup as text. |

Offline runs observed **22 expected backend failures / 224 existing passes** and **9 expected frontend failures / 14 existing passes**. All 238 earlier tests remain green. Backend failures are the absent approval endpoint (404/default error shape); frontend failures are the absent Review report control/Director view. There are no import/collection/setup errors.

Only tests/shared approval fixture and exact ignore exceptions changed, plus this scorecard. Production code, migrations and dependency locks remain identical to merged main. Required-file audit: 93 files match the allowlist. Raw logs stay ignored at `.local/validation/g8-approval-backend-red.log` and `g8-approval-frontend-red.log`. Tests remain uncommitted/unpushed. **Wait for explicit user approval before implementing this batch.** G8 remains unassessed and total stays **75/100**; G9 untouched. README development rules remain removed.

### G8: human approval implemented and complete gate verified

The user approved implementation after reviewing the red checkpoint. The approval endpoint validates configured Director credentials, accepts only a selected briefing ID and strict review acknowledgment, and derives identity/time on the server. A separate application approval capability is unavailable to the pipeline. SQLite reserves the writer before checking eligibility; approval and its zero-token trace commit together with unique report/draft constraints. Approval does not update report facts, draft history or launch decisions. Migration 0008 adds approval rows without rebuilding existing tables.

The Director view shows original data, canonical GO/NO_GO and violations, priority/deadline, selected and earlier drafts, evaluation feedback, advisory checks and human approval status. Selected active reports poll every two seconds and stop on unmount. The confirmation requires credentials and acknowledgment when flagged; credentials are never stored and are cleared after the request. Model text renders as text. The README documents actual usage and the local single-Director scope; development rules remain removed.

| Verification | Observed evidence |
| --- | --- |
| Full `make test` | Exit 0: **246 backend + 23 frontend tests passed**, then TypeScript checking and production build. External networking disabled; no real API key/call. |
| Entire loop | All 20 existing loop cases pass: separate calls, feedback propagation, acceptance in rounds 1–3, maximum three rounds, evaluator/draft failures, persistent history and pending human state. Nine lifecycle cases remain green. |
| Approval safeguards | All 22 new backend cases pass: authentication, forged metadata, strict acknowledgment, incomplete/failed/missing/foreign/nonselected drafts, duplicates, simultaneous requests, identity/time, review snapshot, restart and unchanged NO_GO facts. |
| Review UI | All nine new component cases pass: original/canonical data, history/feedback/checks, explicit confirmation and credentials, flagged acknowledgment, no credential storage, rejection handling, unavailable states, safe markup and polling cleanup. |
| Real HTTP/restart smoke | Temporary SQLite and real Uvicorn process: queued → complete fake pipeline → 401 without auth → 201 approval → 409 duplicate → process restart. Full approved report retained, including NO_GO/violations/priority/deadline/history. Exactly one approval and one approval trace; migration 0008. |
| Deployment | `make up` exited 0 with healthy API/web; proxied `/healthz` returned expected fake-mode JSON. |
| Required-file audit | 99 required files exactly match the allowlist; `git diff --check` passes. Local plan/PDF, smoke script, raw logs, secrets, databases and generated output stay ignored. |

G8 self-assessment: **10/10**, no unmet rubric clauses. Cumulative verified score: **85/100**. Browser visual review and live model quality remain unverified; component, HTTP and restart checks are the evidence obtained. G9 requires its own red-test explanation and explicit approval before implementation. Parent MIS-14 remains in progress until its focused PR is merged.

## G9 / MIS-16: cost and trace red checkpoint, 2026-11-17

Same canonical MIS-14 branch, based on passing G8 commit `2c32bdd`. The user explicitly approved the 40 expected failures with **“move on”** before implementation. The following records the original red checkpoint.

| New cases | Intended behavior |
| --- | --- |
| 23 Python arithmetic cases | Decimal calculation subtracts cached tokens from standard input, retains tiny costs, sums before rounding, rejects invalid/missing counts and treats unknown model rates as unknown cost. Fake/Python/human operations have no provider charge. |
| 11 trace API cases | Record filing, Python launch limits, provisional/resolved priority, all classification/check/draft/evaluation calls and human approval exactly once. Preserve timing, running-call identity and parallel grouping. Include known usage/cost for invalid/refused/incomplete responses. Unknown usage/rates produce incomplete subtotals. Persist rate snapshots and amounts across rate changes/restart; reading traces makes no model call. |
| 6 console cases | One article per executed step, tokens and cached subset, timing, round labels and parallel grouping; display server totals without browser arithmetic, retain small amounts, clearly label unknown/incomplete and simulated values, and keep briefing access when traces cannot load. |

The [official GPT-5.4 mini model page](https://developers.openai.com/api/docs/models/gpt-5.4-mini), checked 2026-11-17, lists standard text rates per million tokens of $0.75 input, $0.075 cached input and $4.50 output. These proposed versioned rates give exactly **$0.001065** for 1000 total input, 200 cached input and 100 total output tokens. Cached tokens are a subset; output already includes reasoning usage. This console uses standard Responses requests, without Batch/Flex/regional pricing or tools.

Observed offline: **34 expected new backend failures / 246 existing passes**, **6 expected new frontend failures / 23 existing passes**. All 269 prior tests pass. Cost tests explicitly assert the missing Python calculator at test execution rather than failing collection. API cases reach the missing `/traces` route (404/default error envelope); UI cases reach the existing Director review but cannot find the absent execution-trace region. No collection/setup/network failures count as behavior evidence.

Production source, migrations and dependency locks remain identical to the passing G8 commit. Only three new test files, exact ignore exceptions and this scorecard changed. Required-file audit: 102 files match the allowlist. Failing tests remain uncommitted/unpushed; raw logs stay ignored in `.local/validation/g9-backend-red.log` and `g9-frontend-red.log`. G9 earns no advance credit; total stays **85/100**. Explain the tests and **wait for explicit user approval before implementing G9**, per the user's TDD checkpoint rule.

### G9: approved implementation and complete gate verified

Implemented the pure Python Decimal calculator and versioned standard-price snapshot. Cached input is subtracted from standard input; total output is counted once. Each call persists its original rate and exact decimal cost. Missing/invalid usage and unknown rates stay unknown; Python/human steps and explicit fake simulations incur zero provider charge. Totals sum saved amounts without per-call rounding or repricing on read.

Filing, launch limits and provisional priority commit with the report. Classification commits its resolved Python priority trace. Model traces are committed as running before calls, then completed under the same identity. Parallel checks use separate short storage sessions and persist completed siblings independently. No transaction spans a model request. Every round and error remains visible; cancellation/recovery closes running calls with unknown usage/cost. Approval adds its zero-token trace atomically. Migration 0009 changes only the trace leaf table and preserves existing report/check/draft/approval relationships; historical uncaptured prices remain unknown.

The trace API exposes ordered steps and server totals. The console displays one article per step, nested parallel groups, timestamps, model/prompt/rate metadata, input/cached/output counts and server-provided decimal amounts. Tiny costs remain visible; unknown/incomplete and simulated values are explicit. Trace loading/failure is independent of briefing approval. Active traces poll and cancel on cleanup; approval refreshes the trace. No dependency was added. Existing model-focused fakes now implement the trace lifecycle contract, and model-only persistence assertions filter out newly added Python steps.

| Verification | Observed evidence |
| --- | --- |
| Full `make test` | Exit 0: **280 backend + 29 frontend tests passed**, followed by TypeScript checking and production build. No API key or external networking. |
| Arithmetic | All 23 new cases pass: exact $0.001065 example, fully cached/zero/tiny/large usage, invalid/missing counts, unknown prices, deterministic/fake zero charge and summation before rounding. |
| Trace API | All 11 new cases pass: fifteen unique steps for three rounds plus approval; original running identity/time, parallel grouping, known usage on invalid/refused/incomplete calls, incomplete totals, simulated data and persisted prices across rate changes/restart. |
| Console | All six new component cases pass: step cards, rounds/groups/timing/tokens, server-owned totals/tiny values, failure/unknown states, running calls without invented finish time, simulation and independent retrieval errors. |
| Real HTTP/restart | Temporary SQLite and real Uvicorn process: six scripted-metadata calls total exactly **$0.006390**, with 6000 input / 1200 cached / 600 output tokens and eleven steps after approval. Fake trace is explicitly simulated/zero. Full reports, NO_GO/violations, approval, traces and costs survive process restart unchanged. No paid call. |
| Legacy migration | Isolated 0008 → 0009 upgrade preserves reports, checks, drafts, approvals, trace IDs and timestamps. Uncaptured historical provider rates remain unknown; no invented prices. |
| Deployment | `make up` exited 0; API/web healthy. Proxied health and rebuilt JS/CSS assets return successfully with trace UI/style content. |
| Repository audit | 106 required files exactly match the allowlist. `git diff --check` passes; local plan/PDF, smoke scripts/logs, credentials, databases, dependencies and build output remain ignored. |

G9 self-assessment: **10/10**, no unmet rubric clauses. Cumulative verified score: **95/100**. Browser visual review and live model quality remain unverified; component/HTTP evidence is reported without a screenshot claim. No branch 5 starts until branch 4 is reviewed and merged.

## MIS-14 final acceptance: overdue-display red checkpoint

G9 is committed at `2e87175`. The existing branch-4 checklist also calls for an overdue state. The UI preserves and shows the server UTC deadline, but does not yet flag active work past that deadline. This is a small remaining branch acceptance item; it does not change Python deadline calculation or add rubric points.

The user explicitly approved these two failures with **“ok”** before implementation. The following records the original red checkpoint.

Two tests were added to the existing Director review test file before changing production code:

- An already overdue processing report shows **Briefing overdue**, keeps its exact server deadline and NO_GO verdict, and leaves approval disabled with no approval request.
- A processing report initially before its deadline becomes visibly overdue when the normal two-second polling cycle crosses it; the deadline remains anchored to submission.

Offline frontend run: **2 expected failures / 29 existing passes**. Both failures are the missing overdue label; the existing app, polling, review and trace UI work normally. The previous complete run passed 280 backend + 29 frontend tests, type checking and build. Production code remains identical to `2e87175`; only the test file and this checkpoint changed. All 106 files still match the allowlist. Tests are local/uncommitted and raw output is ignored at `.local/validation/mis14-deadline-red.log`.

Proposed implementation: a clearly labeled warning for queued/processing reports when current time passes the server's `brief_by_at`, refreshed through existing polling. Do not calculate/reset deadlines, rewrite verdicts, enable approval or introduce another scheduler. **Wait for explicit approval before implementing**, per the user's TDD rule. Verified rubric total remains **95/100**; MIS-14 remains in progress and its PR is not ready until this acceptance item is green.

### MIS-14 final acceptance: approved overdue display verified

Implemented the warning for queued/processing reports whose original server deadline is past. Existing two-second polling updates the display; no new timer, scheduler, backend state or deadline rule was added. Approval eligibility and canonical launch facts remain unchanged. Terminal reports use their completed/failed state rather than an active-processing warning.

| Verification | Observed evidence |
| --- | --- |
| Full `make test` | Exit 0: **280 backend + 31 frontend tests passed**, followed by TypeScript checking and production build. Offline; no key or live model call. |
| Overdue cases | Both new cases pass: already overdue active work and crossing the deadline during polling. Exact server deadline/NO_GO retained; approval remains unavailable with no automatic request. |
| Prior gates | All prior approval, loop, concurrency, persistence, trace and cost tests remain green. G8 and G9 stay at 10/10 each; total stays **95/100**. |
| Deployment | `make up` exited 0 with healthy API/web. Proxied health and final JS/CSS assets return successfully; warning text/style are present in deployed assets. |
| Repository audit | All 106 required files exactly match the allowlist; `git diff --check` passes. PR notes, local plan/PDF, raw logs, scripts, secrets, data, dependencies and build output remain ignored. No new tracked file was needed. |

Branch 4 implementation is ready for its single focused PR. MIS-15/MIS-16 are Done; parent MIS-14 remains In Progress pending review/merge. The PR title must include MIS-14 and use the parent's canonical branch. Browser visual review and live model quality remain unverified; do not claim either. Begin branch 5 only from updated main after this PR merges.
