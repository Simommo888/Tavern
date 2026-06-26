# Tavern LiveOS

Tavern is an enterprise-grade **AI Digital Live Commerce Operating System** for digital-human live commerce operations.

Phase 10 finalizes the operating-system shape: FastAPI backend, Next.js console, plugin-based AI/media providers, visual workflows, file-backed MVP storage, Docker runtime, and CI verification.

Current active application roots:

```text
apps/api/   # FastAPI backend
apps/web/   # Next.js operating console
infra/      # Docker, database, queue and deployment assets
docs/       # architecture and migration documentation
tests/      # regression tests
```

## Golden MVP flow

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

Open `/mvp` in the web console to run this flow through the existing Plugin Manager / Avatar Job / LiveRoom Composition / FFmpeg wrapper boundaries.

## Local development

```powershell
# API
uv --directory "D:\Tavern" run uvicorn apps.api.app.main:app --host 127.0.0.1 --port 8770

# Web
npm --prefix "D:\Tavern\apps\web" run dev
```

Phase 2 established the target top-level boundaries without adding new business features:

```text
packages/    # shared domain/config/testing packages
services/    # service boundaries for model, TTS, avatar, video, RAG, streaming and analytics
plugins/     # future plugin interfaces, manager, loader and providers
workers/     # background workers
agents/      # active agent code; Agent Company refactor happens in a later phase
workflows/   # workflow definitions/runners/nodes/visual assets
components/  # reusable live-room/studio/analytics UI and composition building blocks
assets/      # Tavern-owned raw/processed/generated assets
shared/      # cross-runtime shared types, constants and utilities
legacy/      # archived ViMax-era docs/assets and deprecated entry points
third_party/ # external OSS integrations tracked by manifest
```

Legacy ViMax documentation and branding assets are archived under `legacy/vimax/`.

## Local verification

```powershell
uv --directory "D:\Tavern" run pytest tests/test_workbench_api.py tests/test_plugin_system.py tests/test_agent_config.py tests/test_hygiene_guards.py
npm --prefix "D:\Tavern\apps\web" run test
npm --prefix "D:\Tavern\apps\web" run build
```

## Docker

```powershell
docker compose -f "D:\Tavern\infra\docker\docker-compose.yml" --env-file "D:\Tavern\infra\docker\.env.example" up --build
```

## Final architecture

See `docs/architecture/final-architecture.md` for the Phase 10 architecture, runtime boundaries, configuration contract, plugin matrix, Docker layout, and CI/CD contract.
