# Tavern Docker Compose

Docker Compose 是 Tavern LiveOS Phase 10 的本地运行时契约。它使用与后端 `TavernSettings` 对象一致的环境变量，并把运行时状态挂载到 `.working_dir/`。

## 启动

```bash
docker compose -f infra/docker/docker-compose.yml --env-file infra/docker/.env.example up --build
```

## 服务

- API: http://127.0.0.1:8770
- API health: http://127.0.0.1:8770/health
- API 就绪检查: http://127.0.0.1:8770/ready
- Web: http://127.0.0.1:5180
- n8n: http://127.0.0.1:5678
- n8n health: http://127.0.0.1:5678/healthz
- PostgreSQL: 127.0.0.1:5432
- Redis: 127.0.0.1:6379
- RabbitMQ: http://127.0.0.1:15672
- MinIO: http://127.0.0.1:9001

## 统一配置

`.env.example` 与后端 settings 契约保持一致：

- `TAVERN_APP_NAME`
- `TAVERN_ENV`
- `TAVERN_LOG_LEVEL`
- `TAVERN_WORKSPACE_ROOT`
- `TAVERN_STORAGE_BACKEND`
- `TAVERN_TTS_PROVIDER`
- `TAVERN_CORS_ORIGINS`
- `DATABASE_URL`
- `REDIS_URL`
- `RABBITMQ_URL`
- `MINIO_*`
- `NEXT_PUBLIC_API_BASE`
- `TAVERN_API_BASE_INTERNAL`
- `N8N_*`

`N8N_ENCRYPTION_KEY` 在 `.env.example` 中只是本地开发占位值。保存真实 n8n credentials 前，请复制成本地 `.env` 并换成稳定私密值。

## n8n workflow 导入

1. 启动 compose stack 后打开 http://127.0.0.1:5678。
2. 使用本地 basic auth 默认账号 `tavern / tavern-n8n-local`，或按 n8n 首次启动提示创建 owner。
3. 在 n8n 中选择 Import from File。
4. 导入 `workflows/n8n/tavern-product-to-streaming.workflow.json`。
5. 执行 manual trigger，`Run Tavern MVP live plan` 节点会调用 `api:8770` 的 Tavern API。
6. 回到 Tavern Web 的 `/workflow` 或 `/mvp` 页面查看 run 与产物。

n8n 容器内访问 Tavern API 使用 `http://api:8770`；如果在 Docker 外独立运行 n8n，请把 workflow 里的 API base 改为 `http://127.0.0.1:8770`。

如果本机已有其他 n8n 占用 `5678`，可以临时改用其他宿主机端口启动：

```powershell
$env:N8N_HOST_PORT="5679"
$env:N8N_EDITOR_BASE_URL="http://127.0.0.1:5679/"
$env:N8N_WEBHOOK_URL="http://127.0.0.1:5679/"
docker compose -f "D:\Tavern\infra\docker\docker-compose.yml" --env-file "D:\Tavern\infra\docker\.env.example" up -d n8n
```

## 数据库初始化

PostgreSQL 首次启动会执行：

```text
infra/docker/postgres/001_init.sql
```

该脚本创建 SaaS 租户、商品、直播、RAG、模型网关、数字人、平台、异步任务和审计日志基础表。

## Worker

默认 compose 不启动 worker profile。需要处理异步任务时运行：

```bash
docker compose -f infra/docker/docker-compose.yml --profile workers up worker
```

当前 worker 使用 file task queue 占位，后续会替换为 RabbitMQ 消费者。
