# Rubric scorecard

Scores are evidence-based self-assessments. Full points require every clause to be verified. A future feature, unrun check or missing runtime evidence earns no advance credit.

| Gate | Criterion | Maximum | Status | Verified score |
| --- | --- | ---: | --- | --- |
| G1 | Working README start/test commands | 10 | Passed | 10/10 |
| G2 | Four technology decisions | 10 | Passed | 10/10 |
| G3 | Filing, validation and persistence | 10 | Not started | Not assessed |
| G4 | Python launch limits | 15 | Not started | Not assessed |
| G5 | Severity and deadlines | 10 | Not started | Not assessed |
| G6 | Structured classification and fallback | 10 | Not started | Not assessed |
| G7 | Concurrent checks and injection protection | 10 | Not started | Not assessed |
| G8 | Draft/evaluation and human approval | 10 | Not started | Not assessed |
| G9 | Trace cards, tokens and Python costs | 10 | Not started | Not assessed |
| G10 | Complete offline suite through one model interface/fake | 5 | Not started | Not assessed |

**Fully verified total: 20/100.** Current branch: `abdul2shaik/mis-5-01-choreproject-setup` (foundation milestone); Linear: MIS-5 / MIS-6 / MIS-7. Implementation authorized by the user on 2026-11-11. Branch 1 still requires its focused PR and user review; branch 2 has not started. The user requested the canonical Linear-generated branch name on 2026-11-12; this renames the same workstream and adds no milestone.

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
