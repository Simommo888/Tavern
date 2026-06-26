# Tavern LiveOS Final Architecture

Phase 10 freezes Tavern as an enterprise-grade AI Digital Live Commerce Operating System. The system is intentionally split by runtime boundary and optimized around two principles: delete redundant legacy code, and reuse mature providers through plugins instead of rebuilding engines.

## Runtime boundaries

```text
apps/
  api/                 FastAPI backend, domain services, plugin orchestration, file-backed MVP repositories
  web/                 Next.js operating console for Studio, Workflow, Analytics, Assets, Components, MVP
agent_runtime/         model gateway, prompt/config helpers, agent runtime compatibility layer
interfaces/            shared production-time primitives
packages/              future shared Python/TypeScript packages
services/              service-boundary placeholders for model, TTS, avatar, video, RAG, streaming, analytics
plugins/               top-level plugin contracts/notes; backend implementations live in apps/api/app/plugins
workers/               async/background workers
workflows/             workflow definitions/runners/visual assets
components/            reusable live-room/studio/analytics composition building blocks
assets/                Tavern-owned raw/processed/generated assets
shared/                cross-runtime constants and shared types
infra/
  docker/              Dockerfiles, compose, local service dependencies
  k8s/                 deployment skeleton
third_party/           OSS integration manifest, not business logic
legacy/                archived ViMax-era code/docs/assets
```

## Main product flow

Phase 9 MVP is now the reference golden path:

```text
Upload Product
  ↓
Brand Analysis
  ↓
Script
  ↓
Digital Human Speech
  ↓
Avatar Video
  ↓
Live Video
  ↓
Saved Live Plan
```

The backend persists this as `MvpLivePlan` and also emits `WorkflowRun` / `WorkflowNodeRun` records for auditability.

## Plugin architecture

Business code must call providers through this chain:

```text
Plugin Interface
  ↓
Plugin Manager
  ↓
Plugin Loader
  ↓
Plugin Implementation
```

Current providers:

| Category | Provider | Status | Notes |
| --- | --- | --- | --- |
| Model | OpenAI Compatible Model Gateway | ready/configured by gateway | wraps `agent_runtime.llm.ModelGateway` |
| TTS | Edge TTS | ready | local/free fallback |
| TTS | OpenAI Compatible TTS | ready when configured | `/audio/speech` compatible |
| TTS | Fish Speech | candidate_not_installed | tracked in `third_party/manifest.json` |
| Avatar | LiveTalking | candidate_not_installed | wrapper candidate |
| Avatar | MuseTalk | candidate_not_installed | wrapper candidate |
| Avatar | SadTalker | candidate_not_installed | fallback candidate |
| Video | FFmpeg / MoviePy Composer | ready | local wrapper, no duplicate video engine |
| RAG | Local Keyword RAG | ready | file-backed MVP retrieval |

## Configuration contract

Unified environment variables:

- `TAVERN_APP_NAME`
- `TAVERN_ENV`
- `TAVERN_LOG_LEVEL`
- `TAVERN_WORKSPACE_ROOT`
- `TAVERN_STORAGE_BACKEND=file|postgres`
- `TAVERN_CORS_ORIGINS`
- `TAVERN_TTS_PROVIDER=edge|openai|sapi|placeholder`
- `DATABASE_URL`
- `REDIS_URL`
- `RABBITMQ_URL`
- `MINIO_ENDPOINT`
- `MINIO_ACCESS_KEY`
- `MINIO_SECRET_KEY`
- `NEXT_PUBLIC_API_BASE`

Local secrets remain in `configs/*.local.yaml` and `configs/agent.secrets.local.yaml`; they must not be committed.

## Logging and health

- Backend logging is initialized via `apps/api/app/core/logging.py`.
- Runtime settings are centralized in `apps/api/app/core/settings.py`.
- API health endpoints:
  - `/health` returns app/environment/storage status.
  - `/ready` verifies readiness contract; Postgres mode requires `DATABASE_URL`.

## Persistence

Current MVP storage remains file-backed for local single-machine operation:

```text
.working_dir/workbench/*.json
.working_dir/live_rooms/**
```

PostgreSQL schema exists at `infra/docker/postgres/001_init.sql`. Migration guidance is in `docs/database/repository-migration.md`.

## Docker

Local stack:

```bash
docker compose -f infra/docker/docker-compose.yml --env-file infra/docker/.env.example up --build
```

Services:

- `api`: FastAPI, `/ready` healthcheck
- `web`: Next.js standalone-capable build, `/` healthcheck
- `worker`: optional profile
- `postgres`
- `redis`
- `rabbitmq`
- `minio`

## CI/CD

GitHub Actions workflow: `.github/workflows/ci.yml`

Jobs:

- Backend: `uv sync --frozen --dev` + selected regression tests
- Web: `npm ci` + `npm run ci` (`typecheck` + `build`)

## Phase 10 rules going forward

1. New capabilities must enter through plugin interfaces or workflow nodes.
2. Do not put business logic in `third_party/`.
3. Do not create parallel API clients; use `apps/web/lib/api/config.ts`.
4. Do not bypass `apps/api/app/core/settings.py` for runtime configuration.
5. File-backed repositories are acceptable for MVP/local mode; Postgres mode must fail fast when not configured.
6. Any new runtime service must expose health/readiness and be added to Docker/CI docs.
