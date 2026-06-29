# Tavern LiveOS

Tavern 是面向数字人直播电商运营的企业级 **AI Digital Live Commerce Operating System**。

Phase 10 已固化操作系统形态：FastAPI 后端、Next.js 控制台、基于插件的 AI/媒体 provider、可视化工作流、基于文件的 MVP 存储、Docker 运行时与 CI 验证。

当前活跃应用根目录：

```text
apps/api/   # FastAPI 后端
apps/web/   # Next.js 运营控制台
infra/      # Docker、数据库、队列与部署资源
docs/       # 架构与迁移文档
tests/      # 回归测试
```

## 主生产工作流

Phase 5 的 Agent Company、Workflow API 与 `/workflow` 控制台统一使用以下主链路：

```text
商品 → 品牌 → 故事 → 剧本 → 分镜 → 导演 → 视觉导演 → 语音 → 数字人 → 直播间 → 视频 → 推流
```

Compliance Agent 作为酒类合规 gate 审查脚本、视觉蓝图和发布方案，不插入 12 步主链路。

## 黄金 MVP 流程

Phase 9 MVP 保留为独立的可运行闭环：

```text
上传商品
↓
品牌分析
↓
生成脚本
↓
数字人口播
↓
数字人视频
↓
直播视频
↓
保存直播方案
```

在 Web 控制台打开 `/mvp`，即可通过现有 Plugin Manager / Avatar Job / LiveRoom Composition / FFmpeg wrapper 边界运行该流程。

## n8n 图形化编排

`workflows/n8n/` 提供可导入 n8n 的 product/brand-to-complete-video workflow 示例。n8n 作为外部图形化编排/演示层展示 Tavern 主链路，并通过 `POST /api/v1/workflow/product-videos/runs` 创建 run、再逐节点调用 `/nodes/{node_id}/run`，触发商品/品牌资料到完整视频的端到端闭环；Tavern 后端 `WorkflowDefinition` 仍是主工作流定义来源。

## 本地开发

```powershell
# 后端 API
uv --directory "D:\Tavern" run uvicorn apps.api.app.main:app --host 127.0.0.1 --port 8770

# 前端 Web
npm --prefix "D:\Tavern\apps\web" run dev
```

## 媒体生成 Provider

Product/Brand-to-Complete-Video 工作流的 Image Agent / Video Agent 已接入真实媒体 provider：

- Image Agent：配置 `OPENAI_API_KEY` 后调用 OpenAI Images API，默认 `TAVERN_OPENAI_IMAGE_MODEL=gpt-image-1`、`TAVERN_OPENAI_IMAGE_SIZE=1024x1536`。
- Video Agent：配置 `TAVERN_JIMENG_API_KEY`（Bearer 代理）或 `TAVERN_JIMENG_ACCESS_KEY` + `TAVERN_JIMENG_SECRET_KEY`（火山 HMAC）后调用即梦视频 API，默认 `TAVERN_JIMENG_REQ_KEY=jimeng_t2v_v30`、`CVSync2AsyncSubmitTask` / `CVSync2AsyncGetResult`。
- 未配置密钥或 provider 失败时，系统自动回退到 `placeholder_image` / `placeholder_video`，并在资产 metadata 中记录 `fallback_reason`。
- 本地/CI 如需强制离线占位，可设置 `TAVERN_FORCE_PLACEHOLDER_MEDIA=true`。


Phase 2 建立了目标顶层边界，不新增业务功能：

```text
packages/    # 共享 domain/config/testing packages
services/    # model、TTS、avatar、video、RAG、streaming、analytics 的服务边界
plugins/     # 后续 plugin interfaces、manager、loader 与 providers
workers/     # 后台 worker
agents/      # 当前活跃 agent 代码；Agent Company 重构在后续阶段完成
workflows/   # workflow definitions/runners/nodes/visual assets
components/  # 可复用 live-room/studio/analytics UI 与组合构件
assets/      # Tavern 自有 raw/processed/generated assets
shared/      # 跨运行时共享 types、constants 与 utilities
legacy/      # 归档的 ViMax 时代文档/资产和废弃入口
third_party/ # 由 manifest 跟踪的外部 OSS 集成
```

Legacy ViMax 文档和品牌资产归档在 `legacy/vimax/`。

## 本地验证

```powershell
uv --directory "D:\Tavern" run pytest tests/test_workbench_api.py tests/test_plugin_system.py tests/test_agent_config.py tests/test_hygiene_guards.py
npm --prefix "D:\Tavern\apps\web" run test
npm --prefix "D:\Tavern\apps\web" run build
```

## Docker

```powershell
docker compose -f "D:\Tavern\infra\docker\docker-compose.yml" --env-file "D:\Tavern\infra\docker\.env.example" up --build
```

本地服务地址：

- Tavern API: http://127.0.0.1:8770
- Tavern Web: http://127.0.0.1:5180
- n8n: http://127.0.0.1:5678

n8n 可导入 `workflows/n8n/tavern-product-to-streaming.workflow.json` 查看并触发 Tavern 商品/品牌资料到完整视频的主链路示例。

## 最终架构

Phase 10 架构、运行时边界、配置契约、插件矩阵、Docker 布局与 CI/CD 契约见 `docs/architecture/final-architecture.md`。
