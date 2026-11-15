# Mission Control: Go/No-Go Launch Console

Engineer anomaly reports become concise briefings for a Flight Director. Python owns launch decisions; models provide advisory analysis; a person approves briefings.

## Run locally

Prerequisites: Docker Desktop (or Docker Engine) running with Docker Compose v2.20+ and GNU Make. No local Python, Node, or API key is required. Initial image/dependency downloads need internet access.

Start the app:

```sh
make up
```

Open **http://localhost:8080**. Change `WEB_PORT` if 8080 is occupied. Engineers can file reports, view saved reports and retry validation or connection failures without losing their form entries. Launch assessment and model processing are still pending; the UI displays saved readings without claiming launch clearance.

Run all current tests, TypeScript checking and the frontend production build:

```sh
make test
```

Dependencies are installed while building the test image. Test execution runs in an isolated container with external networking disabled and no API key. Pytest also blocks external sockets; local loopback/Unix sockets are permitted for in-process testing. The test container has a temporary database and cannot access the application data volume.

## Configuration and data

Defaults work without a `.env` file. `.env.example` lists optional settings. Fake mode is clearly labeled and makes no paid calls. Live-mode configuration is validated, but model calls are not implemented yet. OpenAI mode requires an API key and explicit non-demo director credentials; the key stays on the backend.

SQLite lives in the `mission-control_mission-data` Docker volume. `make down` stops containers and preserves that volume. Do not use `docker compose down -v` when preserving application data. The API runs migrations before it becomes ready. `GET /healthz` checks database/migration readiness and is available through the web proxy. `make logs` shows recent service output.

## Report API

`POST /api/v1/reports` accepts the following JSON and returns HTTP 201 with the saved fields, a server-generated UUID, a UTC `created_at` and a `Location` header:

```json
{
  "engineer_name": "Alex Rivera",
  "station": "PROP",
  "wind_knots": "25.000",
  "temp_c": "4.000",
  "fuel_pct": "98.000",
  "note": "Valve response lagged during the final check."
}
```

All six fields are required. Name, station and note are trimmed and limited to 100, 50 and 4000 characters. Readings use decimal strings with up to six integer digits and three decimal places; JSON numbers, exponent notation and nonfinite values are rejected rather than rounded. Wind and fuel must be nonnegative. Readings outside launch limits, including fuel above 100%, are valid anomaly data and are saved for assessment. Extra fields, including verdict and approval metadata, are rejected.

`GET /api/v1/reports/{id}` reads one report. `GET /api/v1/reports?limit=20&offset=0` returns `{items, total, limit, offset}`, newest first; limit must be 1–100 and offset nonnegative. Validation errors return HTTP 422 with `{error: {code, message, fields: [{field, message}]}}`. Unknown reports return HTTP 404. Reports are committed before submission succeeds and survive application process restarts.

## Development rules

Follow the five sequential Linear branch milestones. Use the parent issue's exact generated Git branch name and announce it before starting. MIS-5 uses `abdul2shaik/mis-5-01-choreproject-setup`. For every new behavioral TDD cycle, write tests, observe expected failures, explain them and wait for the user's explicit approval before implementation. Then implement, verify green and grade the active rubric criterion. Proceed only at full points. Present each branch/PR for review before moving to the next merged-main milestone. The running evidence is in [docs/RUBRIC.md](docs/RUBRIC.md); technology decisions are in [TOOL_CHOICES.md](TOOL_CHOICES.md).

Git uses an exact file allowlist: commit only required source, tests, build/configuration, lock files, migrations and requested documents. Keep secrets, local references (including the assignment PDF), databases, dependencies, generated builds and raw verification output ignored.
