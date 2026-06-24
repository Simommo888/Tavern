# Tavern AI 数字人直播工作台数据库 Schema

## 目标

`infra/docker/postgres/001_init.sql` 是企业级 PostgreSQL 数据底座的第一版初始化脚本，覆盖 SaaS 租户、权限、商品、直播、Agent 回复、合规、RAG、模型网关、数字人、平台接入、异步任务和审计日志。

## 核心边界

- PostgreSQL 保存业务事实和审计记录。
- MinIO 保存音频、视频、图片、原始文档等对象。
- Milvus 保存向量索引；PostgreSQL 只保存 chunk metadata 和 Milvus 主键。
- RabbitMQ 负责任务投递；`async_tasks` 表保存任务状态、幂等键和结果。
- Redis 负责实时事件 fan-out、锁和限流，不作为长期事实存储。

## 表分组

### SaaS 与权限

- `tenants`
- `users`
- `roles`
- `permissions`
- `user_roles`
- `audit_logs`

### 商品与直播

- `products`
- `product_faqs`
- `avatar_profiles`
- `live_rooms`
- `live_sessions`
- `audience_events`
- `anchor_replies`
- `speech_artifacts`
- `compliance_reviews`

### 话术与工作流

- `script_templates`
- `workflow_rules`
- `async_tasks`

### RAG 与模型

- `knowledge_documents`
- `knowledge_chunks`
- `model_provider_configs`
- `prompt_templates`
- `model_invocations`

### 数字人与平台

- `avatar_jobs`
- `platform_accounts`
- `platform_events`
- `platform_metrics`

## 迁移策略

当前应用仍使用 JSON file repository 保障本地 MVP 可运行。后续迁移顺序：

1. 为 `products`、`script_templates`、`workflow_rules` 建 SQL repository。
2. 为 `live_sessions`、`audience_events`、`anchor_replies`、`speech_artifacts` 建 SQL repository。
3. 将 `knowledge_documents` / `knowledge_chunks` 接入 Milvus 主键回写。
4. 将 `async_tasks` 与 RabbitMQ publisher/worker 绑定，启用幂等键。
5. 将所有写操作补充 `audit_logs`。

## 幂等与审计

- 平台事件通过 `(session_id, external_event_id)` 防止重复消费。
- 异步任务通过 `async_tasks.idempotency_key` 防止重复执行。
- 所有运营操作最终应写入 `audit_logs`。

## 合规要求

酒类直播相关的主播回复、话术生成、RAG 检索注入都必须进入 `compliance_reviews`，并记录策略版本、风险等级、输入输出文本和命中 notes。
