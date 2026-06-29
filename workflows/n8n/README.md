# Tavern n8n workflows

该目录存放可导入 n8n 的 Tavern workflow 示例。n8n 用作外部图形化编排/演示层，不替代 Tavern 后端的 `WorkflowDefinition`、`WorkflowRun` 与 `WorkflowNodeRun`。

## 启动

```powershell
docker compose -f "D:\Tavern\infra\docker\docker-compose.yml" --env-file "D:\Tavern\infra\docker\.env.example" up --build
```

服务启动后：

- Tavern API: http://127.0.0.1:8770
- Tavern Web: http://127.0.0.1:5180
- n8n: http://127.0.0.1:5678

如果本机已有其他 n8n 占用 `5678`，可设置 `N8N_HOST_PORT=5679` 并同步调整 `N8N_EDITOR_BASE_URL`、`N8N_WEBHOOK_URL` 后再启动。

本地 basic auth 默认值：

- 用户名：`tavern`
- 密码：`tavern-n8n-local`

如果要保存真实 n8n credentials，请复制 `.env.example` 为本地 `.env`，并替换稳定私密的 `N8N_ENCRYPTION_KEY`。不要提交真实密钥。

## 导入 workflow

1. 打开 http://127.0.0.1:5678。
2. 按 n8n 首次启动提示创建 owner，或使用本地 basic auth。
3. 选择 **Import from File**。
4. 导入 `D:\Tavern\workflows\n8n\tavern-product-to-streaming.workflow.json`。
5. 确认画布中出现：商品 → 品牌 → 故事 → 剧本 → 分镜 → 导演 → 视觉导演 → 语音 → 数字人 → 直播间 → 视频 → 推流。

## 执行说明

示例 workflow 包含两类节点：

- 12 个 Tavern 主链路展示节点，用来在 n8n 画布中呈现 product-to-streaming DAG。
- HTTP Request 节点，调用现有 Tavern API：
  - `GET /api/v1/workflow/definitions`
  - `POST /api/v1/mvp/live-plans/run`
  - `GET /api/v1/workflow/runs/{workflow_run_id}/nodes`
  - `GET /api/v1/workflow/runs`

在 Docker Compose 网络内，n8n 通过 `http://api:8770` 访问 Tavern API。如果你在 Docker 外独立运行 n8n，请把 workflow 里的 API base 改为 `http://127.0.0.1:8770`。

执行 manual trigger 后，`Run Tavern MVP live plan` 会复用 Tavern Phase 9 MVP 闭环生成 live plan，并写入 Tavern 的 workflow run/node run 审计数据。你可以在 Tavern Web 的 `/workflow` 或 `/mvp` 页面查看结果。

## 边界

- n8n 示例不是 Tavern workflow runner 的替代品。
- Tavern 后端 `WorkflowDefinition` 仍是主链路定义来源。
- 当前可执行闭环复用 `POST /api/v1/mvp/live-plans/run`。
- 后续如需逐节点驱动 12 步主链路，应先在 Tavern 后端新增通用 workflow trigger/retry API，再让 n8n 调用这些 API。
