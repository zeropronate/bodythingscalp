Task receipt and plan

- Purpose: produce a single-file, engineer- and LLM-friendly reference for the repository.
- Plan: (1) summarize purpose in 3–5 sentences, (2) include a high-level text architecture diagram, (3) enumerate subsystems with responsibilities, files and key functions/classes, (4) document data flow, external integrations, DB schema, configuration and entry points, (5) list technical debt and safe extension guidance.

Checklist

- [x] One-line purpose (3–5 sentences)
- [x] High-level architecture diagram (text)
- [x] Subsystems with responsibilities, files, functions
- [x] Data flow and external integrations
- [x] Background jobs and async processes
- [x] Database schema (inferred) and relationships
- [x] Configuration, env vars, secrets handling
- [x] Entry points and critical execution paths
- [x] Known technical debt, limitations, scalability notes
- [x] "How to extend this system safely" section


---

CODEBASE CONTEXT

1. Overall purpose (3–5 sentences)

This repository implements a small document-intelligence service focused on medical/blood-test reports. It accepts PDF and image uploads via a FastAPI backend, extracts and preprocesses textual content (PDF parser and OCR), then uses a local LLM (via an Ollama HTTP endpoint) to convert free-form report text into a strict JSON analysis (summary + parameter list). There is a Streamlit frontend for user uploads and a separate MQTT consumer that ingests real-time body-metrics messages and persists computed features to a PostgreSQL database. The codebase provides report generation utilities and test coverage for pipeline components.


2. High-level architecture (text diagram)

Frontend (Streamlit) <--HTTP--> FastAPI API (main.py + analyze router)
                                   |
                                   |-- Extract layer: PDF parser (pdfplumber) / OCR (pytesseract)
                                   |-- Preprocess layer: heuristics to compress relevant lines
                                   |-- LLM client: build prompt -> call Ollama HTTP API -> clean output
                                   |-- JSON validation: json_safe + Pydantic schemas
                                   |
                                   V
                             Response (structured JSON)

MQTT Broker --> mqtt_consumer.py --> PostgreSQL (body_metrics_raw, body_metrics_features, users)

Auxiliary: generate_reports.py (creates sample PDF reports) and sample_reports/ for examples


3. Major subsystems / modules

Each subsystem lists: responsibility | main files | key classes/functions

3.1 FastAPI HTTP API
- Responsibility: Accept uploaded documents, orchestrate extraction/preprocessing/LLM analysis, return structured JSON to clients.
- Main files: `main.py`, `app/routers/analyze.py`
- Key functions/classes:
  - FastAPI instance in `main.py` (CORS and logging middleware).
  - `analyze` router handler (POST `/analyze`) in `app/routers/analyze.py` — performs validation, file size/type checks, calls extraction and LLM client, validates and returns AnalysisResult.
  - Request/response logging middleware and a generic exception handler in `main.py`.

3.2 Text Extraction and OCR
- Responsibility: Convert uploaded bytes (PDF or image) to plain text.
- Main files: `app/services/pdf_parser.py`, `app/services/ocr_service.py`, `app/services/extract_text.py`
- Key functions:
  - `extract_text_from_pdf_bytes(data: bytes)` — uses `pdfplumber` to read pages and extract text while skipping problematic pages.
  - `extract_text_from_image_bytes(data: bytes)` — opens images with Pillow and runs `pytesseract.image_to_string`.
  - `extract_text_from_upload(ext, data)` — simple router that selects PDF vs. image flow.

3.3 Preprocessing
- Responsibility: Reduce and prioritize long report text to lines likely containing parameters (unit/value heuristics) to keep LLM prompt compact.
- Main files: `app/services/preprocess.py`
- Key functions:
  - `compress_report_text(text: str, max_chars: int)` — heuristics using regex for numbers, units, and a set of parameter hints to keep parameter-relevant lines.

3.4 LLM Client
- Responsibility: Build a strict prompt, call local Ollama HTTP API, and sanitize output.
- Main files: `app/services/llm_client.py`
- Key functions/classes:
  - `build_prompt(report_text: str)` and `_truncate_text()` — enforce input size limits and append the base prompt.
  - `_call_ollama_api(prompt: str, timeout: int)` — performs blocking `requests.post` to `{OLLAMA_API_URL}/api/generate`.
  - `_clean_llm_output(output: str)` — strip fences, prefixes, and common artifacts.
  - `analyze_text_with_llm(report_text: str, max_retries: int = 1)` — retry loop and public API used by the router.
- Important config variables read from env: `OLLAMA_API_URL`, `OLLAMA_MODEL`, temperature/num_predict/num_ctx and timeouts.

3.5 JSON safety and schema validation
- Responsibility: Robustly parse LLM output and coerce into stable Pydantic models.
- Main files: `app/utils/json_safe.py`, `app/schemas/analysis.py`
- Key functions/classes:
  - `parse_json_safe(s: str)` — strip code fences, attempt direct loads, extract outermost JSON object, and some simple repairs.
  - `Parameter`, `Summary`, `AnalysisResult` Pydantic models — provide multiple field validators and mappings for common LLM variations (e.g., `parameter` -> `name`, `result` -> `status`, inference defaults).

3.6 MQTT Consumer (background process)
- Responsibility: Subscribe to MQTT topics, parse body-metric messages, persist raw JSON and derived features into Postgres.
- Main file: `mqtt_consumer.py`
- Key functions/classes:
  - `start_mqtt()` — creates paho-mqtt client, sets callbacks, and starts `loop_forever()`.
  - `on_connect` and `on_message` callbacks — `on_message` decodes payload, inserts raw row (via `insert_raw`), retrieves user profile (`get_user_profile`), computes features (`compute_features`) and inserts feature row (`insert_features`), using `psycopg2`.
  - Helper math: `calculate_age`, `compute_features` (BMI, BMR, TDEE, fat_mass, lean_mass).
- Note: DB config currently hard-coded in module-level `DB_CONFIG`.

3.7 Reporting & Frontend
- Responsibility: Provide a simple Streamlit UI and sample PDF generation utilities.
- Main files: `frontend/app.py`, `generate_reports.py`, `sample_reports/` (static examples)
- Key items:
  - Streamlit app does file upload and POSTs to backend `/analyze`.
  - `generate_reports.py` contains sample report text and ReportLab-based PDF writer to create examples.

3.8 Tests
- Responsibility: Unit and integration tests for schema, JSON parsing, LLM prompt/output handling, pipeline behavior.
- Main files: `test/` (multiple test modules such as `test_llm.py`, `test_json_parser.py`, `test_pipeline.py`, `test_schema.py`, `test_none_handling.py`, `test_alt_fields.py`, `test_range_field.py`)


4. Data flow (end-to-end)

Primary (HTTP analysis):
1. Client uploads file -> POST `/analyze`.
2. Router verifies file type/size and reads bytes.
3. `extract_text_from_upload()` returns raw text (pdfplumber or pytesseract path).
4. `compress_report_text()` reduces the text to likely parameter-bearing lines.
5. `analyze_text_with_llm()` builds a strict prompt and sends it to Ollama via HTTP.
6. LLM returns text; `_clean_llm_output()` strips extraneous content.
7. `parse_json_safe()` attempts to parse the JSON. Pydantic `AnalysisResult` validates and normalizes fields.
8. Final structured JSON returned to caller; frontend renders results and highlights abnormal parameters.

Secondary (MQTT ingestion):
1. MQTT broker publishes messages to configured topic(s).
2. `mqtt_consumer.py` subscribes (`#` by default), decodes each message as JSON.
3. Inserts raw payload into `body_metrics_raw`.
4. Fetches user profile from `users` table, computes BMI/BMR/TDEE/fat/lean mass, inserts derived values into `body_metrics_features`.


5. External integrations

- Local LLM: Ollama HTTP API (`/api/generate`). Configured via `OLLAMA_API_URL`, `OLLAMA_MODEL` and related env vars. The system uses blocking HTTP calls (`requests`).
- OCR: `pytesseract` (Tesseract) for image extraction — requires system Tesseract binary and potentially Poppler for PDF conversion.
- PDF parsing: `pdfplumber` for direct PDF text extraction.
- MQTT broker: `paho-mqtt` client used in `mqtt_consumer.py`. Defaults to `127.0.0.1:1883` and subscribes to `#`.
- PostgreSQL: `psycopg2` used by MQTT consumer; DB credentials currently hardcoded in `mqtt_consumer.py`.
- Streamlit frontend: talks to backend via HTTP.
- Docker: a `docker/Dockerfile` is present for containerized deployment; note system deps installed (tesseract, poppler-related libraries).


6. Background jobs and async processes

- `mqtt_consumer.py`: long-running process using `client.loop_forever()`; synchronous DB I/O in callbacks.
- LLM calls: synchronous blocking HTTP requests inside request handler; not scheduled to background by default.
- `generate_reports.py`: one-off batch-style script to create example PDFs; not scheduled.
- Tests: run via `pytest` as a development-time background verification.


7. Database schema (inferred from code)

This codebase does not include an ORM or migration files. Schema below is inferred from SQL used in `mqtt_consumer.py`.

Tables (inferred):

- `users`
  - Columns used: `id` (UUID primary key), `height_cm` (int), `sex` (text; values like 'male'/'female'), `date_of_birth` (date)
  - Purpose: provide demographic data required for feature computation (age, BMR/BMI).

- `body_metrics_raw`
  - Columns (in INSERT): `id` (serial/UUID primary key returned), `user_id` (UUID), `weight_kg` (numeric), `fat_percent` (numeric), `muscle_percent` (numeric), `water_percent` (numeric), `measured_at` (timestamp with timezone), `source` (text, e.g., 'openscale'), `raw_json` (json/jsonb)
  - Purpose: raw messages captured from MQTT for audit and replay.

- `body_metrics_features`
  - Columns (in INSERT): `raw_id` (foreign key to `body_metrics_raw.id`), `bmi` (numeric), `bmr` (numeric), `tdee` (numeric), `fat_mass` (numeric), `lean_mass` (numeric)
  - Purpose: derived metrics computed from raw measurements and user profile for analytics.

Relationships
- `body_metrics_features.raw_id` references `body_metrics_raw.id` (one-to-one or one-to-many depending on insert behavior).
- `body_metrics_raw.user_id` references `users.id` (many raw measurements per user).

Notes and recommendations: No schema/DDL included; add proper types, indexes (on `user_id`, `measured_at`), and constraints (foreign keys, not-null where appropriate). Use migrations (Alembic) and model layer (SQLAlchemy or similar).


8. Configuration, environment variables, and secrets handling

Configuration methods in codebase:
- Environment variables are consumed in `app/services/llm_client.py` for Ollama-related configuration.
- The Streamlit frontend reads `BACKEND_URL` from env.
- `requirements.txt` and `pyproject.toml` are present for dependency management.
- `mqtt_consumer.py` currently uses module-level constants for MQTT broker and a hard-coded `DB_CONFIG` dictionary (host, dbname, user, password, port).

Environment variables referenced in code (explicit):
- `OLLAMA_MODEL` (default `mistral`) — model id for Ollama
- `OLLAMA_API_URL` (default `http://localhost:11434`) — endpoint for local Ollama instance
- `OLLAMA_TEMPERATURE`, `OLLAMA_NUM_PREDICT`, `OLLAMA_NUM_CTX` — numeric tuning options for generation
- `MAX_INPUT_CHARS` — truncate length used for prompt
- `LLM_TIMEOUT_SECONDS` — HTTP request timeout for LLM calls
- `BACKEND_URL` — used by Streamlit frontend to locate backend

Secrets handling:
- Currently the repository relies on environment variables for LLM config and frontend URL, which is appropriate for non-secret config.
- However, `mqtt_consumer.py` contains cleartext DB credentials (`user: healthuser`, `password: healthpass`) and should be migrated to env variables and/or a secrets manager.
- There is no centralized config loader (e.g., pydantic BaseSettings) or `.env` usage in the code. Adoption of `python-dotenv` or preferably a typed settings pattern (`pydantic` BaseSettings) is recommended.

Recommendations:
- Move all secrets and credentials (DB, MQTT auth if used, API keys) to environment variables or a secrets store (Vault, AWS Secrets Manager).
- Add a `config.py` or `app/config.py` that uses `pydantic.BaseSettings` to centrally validate and document expected env vars.
- Do not commit `.env` to source control.


9. Entry points and critical execution paths

Entry points
- `main.py` — primary HTTP app. Run with `uvicorn main:app --reload` in development or via container CMD in production.
- `mqtt_consumer.py` — run as standalone process: `python mqtt_consumer.py` (long-running subscriber).
- `frontend/app.py` — Streamlit: `streamlit run frontend/app.py`.
- `generate_reports.py` — script to create sample PDF reports.

Critical execution paths
- HTTP analysis path:
  - Client -> `main.py` router -> validations -> `extract_text_from_upload()` -> `compress_report_text()` -> `analyze_text_with_llm()` -> `_call_ollama_api()` -> `_clean_llm_output()` -> `parse_json_safe()` -> `AnalysisResult` model -> response.
- LLM request path: building prompt, truncation, HTTP POST to Ollama, single-threaded blocking call; this is in the path of the request lifecycle (latency impacts end-user experience).
- MQTT ingestion path: `on_message` performs DB inserts and computations synchronously; any DB slowness will block processing of subsequent messages unless paho handles callbacks concurrently (default behavior: callbacks run in network loop thread).


10. Asynchronous and background processes

- FastAPI request handlers are async-capable but the LLM client uses blocking `requests`. Consider switching to `httpx` async client or dispatching LLM requests to a background worker/task queue.
- `mqtt_consumer.py` is an independent long-running synchronous process (no async/await). It uses `paho.mqtt` and synchronous DB calls (`psycopg2`). For higher throughput, delegate DB writes to a queue and use worker pool.
- There is no job queue (Celery, RQ) present. Adding a task queue is recommended for long-running external calls and CPU-bound tasks like OCR.


11. Known technical debt

- Hard-coded DB credentials in `mqtt_consumer.py` (secrets in code).
- No ORM or migration strategy; schema is inferred and not maintained via migrations.
- Blocking LLM calls inside request handlers (no background job queue or async HTTP client).
- Limited error handling and retries for DB and LLM failures (some retry logic exists in LLM, minimal error handling in MQTT DB writes).
- No authentication/authorization on API endpoints.
- Minimal logging/observability: no metrics, structured logging, or request tracing integrations.
- No rate limiting or request quota protection on LLM usage.
- No caching for repeated document analysis (recompute same PDF repeatedly).
- Limited validation of LLM output beyond Pydantic; some repairs are heuristic and may fail for malformed outputs.


12. Architectural limitations and scalability constraints

- Single-process LLM calls: with synchronous HTTP calls, concurrency is limited by worker processes/threads and LLM throughput. For production, front-end should dispatch LLM tasks to a worker pool.
- MQTT consumer is single-instance and synchronous; to scale, either run multiple consumers partitioned by client or use a message queue that supports consumer groups.
- Large PDFs and OCR are CPU- and memory-intensive; no streaming/chunked extraction is implemented.
- No persistent job queue, worker autoscaling, or cloud storage for large files. Storage of raw files is not implemented (only in-memory during analysis).
- Database access is limited to the MQTT consumer; other parts are stateless and require a persistence plan (e.g., results storage) to scale horizontally.


13. How to extend this system safely

General principles
- Add small, well-tested incremental changes. Keep the public API stable. Add feature flags (env var toggles) for large changes.
- Prefer adding new files under `app/services/` and wiring them into `app/routers/` rather than changing router logic directly.
- Write unit tests and integration tests for every new external integration (mock external LLM or the Ollama API for CI).

Step-by-step examples

A. Add database-backed analysis result persistence
1. Create `app/models/` and define SQLAlchemy models for `User`, `Document`, `Analysis`, `BodyMetricsRaw`, `BodyMetricsFeatures`.
2. Add Alembic for migrations and create migration scripts for the inferred schema.
3. Implement a `DatabaseService` in `app/services/database.py` that provides a session factory and transactional helpers.
4. Modify `analyze` router to persist the Analysis result (with minimal schema changes) after successful validation.
5. Add tests that use a temporary test database (sqlite in-memory or test Postgres via docker-compose).

B. Move LLM calls to an async worker pattern
1. Introduce a task queue (Celery + Redis, or RQ) and create a worker function `tasks.analyze_document` which calls `analyze_text_with_llm` in a worker process.
2. Change `/analyze` to either (a) return a job ID and provide a status endpoint, or (b) call the worker synchronously with a long timeout.
3. Use an async HTTP client (httpx) in `llm_client` if remaining in-process.
4. Add rate limiting and backoff for LLM requests.

C. Secure credentials
1. Replace hard-coded credentials with env vars or a `pydantic.BaseSettings` config.
2. Integrate a secrets manager for production (Vault or cloud provider secrets).
3. Add runtime checks and fail-fast on missing critical env vars.

D. Scale OCR and PDF processing
1. Offload OCR to background workers; store intermediate images or text in cloud storage (S3) if needed.
2. Use streaming PDF parsers or page-level processing to bound memory usage.
3. Add concurrency controls (thread/process pools) with worker limits and graceful shutdown.

E. Observability and production hardening
1. Add structured logging (JSON) and request IDs.
2. Expose `/health` and `/metrics` endpoints and integrate Prometheus exporters.
3. Add centralized error reporting (Sentry, Datadog).


14. Quick operational notes

- Run backend locally: `uvicorn main:app --reload` (requires Ollama running and Tesseract installed for OCR tests).
- Run Streamlit frontend: `streamlit run frontend/app.py` (set `BACKEND_URL` if backend not on localhost).
- Start MQTT consumer: `python mqtt_consumer.py` (ensure PostgreSQL accessible and credentials provided);
- Build Docker image: `docker build -t blood-analyzer -f docker/Dockerfile .`


15. Mapping to repository files (quick reference)
- `main.py` — FastAPI app and middleware
- `app/routers/analyze.py` — main analysis endpoint and request orchestration
- `app/services/pdf_parser.py` — pdfplumber extraction logic
- `app/services/ocr_service.py` — pytesseract-based image OCR
- `app/services/extract_text.py` — upload ext router
- `app/services/preprocess.py` — heuristics to compress and select lines
- `app/services/llm_client.py` — Ollama client, prompt builder, cleaners
- `app/utils/json_safe.py` — robust LLM JSON parsing heuristics
- `app/schemas/analysis.py` — Pydantic models and validators
- `mqtt_consumer.py` — MQTT consumer and Postgres persistence logic
- `frontend/app.py` — Streamlit UI
- `generate_reports.py` and `sample_reports/` — sample report generation and examples
- `docker/Dockerfile` — container build recipe
- `requirements.txt`, `app/requirements.txt`, `pyproject.toml` — dependency lists


16. Next recommended work (priority)
- Remove hard-coded secrets and centralize config into `app/config.py` using `pydantic.BaseSettings`.
- Add persistence for analysis results and migration tooling (Alembic + SQLAlchemy models).
- Move LLM calls off the request thread into a job queue or convert LLM client to async with bounded concurrency.
- Add authentication (JWT/OAuth2) for API endpoints and rate limiting for LLM calls.
- Add production observability (metrics, structured logs) and health checks.


End of CODEBASE_CONTEXT.md
