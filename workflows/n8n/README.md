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
5. 确认画布中出现：商品/品牌资料 → Planner Agent（任务规划） → Story Agent（故事生成） → Script Agent（直播话术） → Director Agent（镜头拆解） → Visual Director Agent（画面设计 + Prompt） → Asset Agent（素材匹配/生成） → Image Agent（背景/贴图生成） → Video Agent（镜头视频生成） → Editor Agent（剪辑/BGM/合成）。

## 执行说明

示例 workflow 包含两类节点：

- 10 个 Tavern Agent HTTP 节点，每个节点都会单独调用 Tavern API 并在 n8n 画布里显示该 Agent 的输入输出。
- HTTP Request 节点，调用 Tavern API：
  - `GET /api/v1/workflow/definitions`
  - `POST /api/v1/workflow/product-videos/runs`
  - `POST /api/v1/workflow/product-videos/runs/{workflow_run_id}/nodes/{node_id}/run`
  - `GET /api/v1/workflow/runs/{workflow_run_id}/nodes`
  - `GET /api/v1/workflow/runs`

在 Docker Compose 网络内，n8n 通过 `http://api:8770` 访问 Tavern API。如果你在 Docker 外独立运行 n8n，请把 workflow 里的 API base 改为 `http://127.0.0.1:8770`。

执行 manual trigger 后，`Create Tavern video workflow run` 会先创建 Tavern `WorkflowRun`，随后 n8n 按顺序逐节点调用商品/品牌资料、Planner、Story、Script、Director、Visual Director、Asset、Image、Video、Editor。每个 HTTP 节点响应都会返回当前 workflow snapshot，最终 Editor 节点写入 `complete_video` 产物 URI、workflow run/node run 审计数据与资产中心记录。无外部媒体生成器密钥时，Image/Video/Editor 会生成可追踪的本地占位产物，便于演示和集成验证。

## 边界

- n8n 示例不是 Tavern workflow runner 的替代品。
- Tavern 后端 `WorkflowDefinition` 仍是主链路定义来源。
- 当前 n8n 闭环使用 `POST /api/v1/workflow/product-videos/runs` + `POST /api/v1/workflow/product-videos/runs/{workflow_run_id}/nodes/{node_id}/run` 逐节点执行。
- 后续如需真实图片/视频生成，应在 Image Agent / Video Agent 节点接入具体 provider，并保持 `WorkflowRun` 与 `WorkflowNodeRun` 审计契约不变。
