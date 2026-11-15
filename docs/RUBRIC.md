# Rubric scorecard

Scores are evidence-based self-assessments. Full points require every clause to be verified. A future feature, unrun check or missing runtime evidence earns no advance credit.

| Gate | Criterion | Maximum | Status | Verified score |
| --- | --- | ---: | --- | --- |
| G1 | Working README start/test commands | 10 | Passed | 10/10 |
| G2 | Four technology decisions | 10 | Passed | 10/10 |
| G3 | Filing, validation and persistence | 10 | Passed | 10/10 |
| G4 | Python launch limits | 15 | Passed | 15/15 |
| G5 | Severity and deadlines | 10 | Not started | Not assessed |
| G6 | Structured classification and fallback | 10 | Not started | Not assessed |
| G7 | Concurrent checks and injection protection | 10 | Not started | Not assessed |
| G8 | Draft/evaluation and human approval | 10 | Not started | Not assessed |
| G9 | Trace cards, tokens and Python costs | 10 | Not started | Not assessed |
| G10 | Complete offline suite through one model interface/fake | 5 | Not started | Not assessed |

**Fully verified total: 45/100.** MIS-5 is complete: merged PR #1 verified at main commit `252b0a1` on 2026-11-12. Current branch: `abdul2shaik/mis-8-02-featurereport-processing`. G3 and G4 are verified after separate explicit user approvals. G5 requires its own red-test review and approval before implementation.

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
