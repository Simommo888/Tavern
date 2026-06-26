# Repository 迁移计划

当前 `apps/api` 使用 file-backed repository 保持 MVP 本地可运行。PostgreSQL schema 已由 `infra/docker/postgres/001_init.sql` 固化，下一步按以下顺序替换存储层。

## Phase 1：Workbench CRUD

替换：

- `JsonCollectionRepository(products)` -> `products` / `product_faqs`
- `JsonCollectionRepository(scripts)` -> `script_templates`
- `JsonCollectionRepository(workflow_rules)` -> `workflow_rules`
- `JsonCollectionRepository(avatars)` -> `avatar_profiles`

验收：现有 `/api/v1/products`、`/api/v1/scripts/templates`、`/api/v1/workflow/rules`、`/api/v1/avatars` 行为不变。

## Phase 2：Live Session

替换：

- `FileLiveRoomRepository.save_session` -> `live_sessions`
- `events.jsonl` -> `audience_events` / `anchor_replies` / `speech_artifacts`
- `speech` 本地目录 -> MinIO object key + `speech_artifacts`

验收：同步和异步弹幕模式都能通过 SSE 收到 `anchor_reply`。

## Phase 3：RAG / Model / Platform

替换：

- `knowledge_documents.json` -> `knowledge_documents`
- `knowledge_chunks.json` -> `knowledge_chunks` + Milvus primary key
- `model_providers.json` -> `model_provider_configs`
- `platform_events.json` -> `platform_events`
- `platform_metrics.json` -> `platform_metrics`

## Phase 4：Async Tasks

替换：

- `FileTaskQueue` -> RabbitMQ publisher + `async_tasks` 状态表
- `TaskDispatcher.drain_once` -> long-running RabbitMQ consumer

## 安全要求

- 每个 SQL repository 必须通过当前 API focused tests。
- 存储切换应由环境变量控制：`TAVERN_STORAGE_BACKEND=file|postgres`。
- 未配置 `DATABASE_URL` 时必须 fail fast，不能静默回退到空数据库。
