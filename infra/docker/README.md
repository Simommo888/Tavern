# Tavern Docker Compose

## 启动

```bash
docker compose -f infra/docker/docker-compose.yml --env-file infra/docker/.env.example up --build
```

## 服务

- API: http://127.0.0.1:8770
- Web: http://127.0.0.1:5180
- PostgreSQL: 127.0.0.1:5432
- Redis: 127.0.0.1:6379
- RabbitMQ: http://127.0.0.1:15672
- MinIO: http://127.0.0.1:9001

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

当前 worker 使用 file task queue 占位，后续会替换为 RabbitMQ consumer。
