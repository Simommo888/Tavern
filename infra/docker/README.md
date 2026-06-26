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
