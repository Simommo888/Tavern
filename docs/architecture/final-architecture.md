# Tavern LiveOS 最终架构

Phase 10 将 Tavern 固化为企业级 AI Digital Live Commerce Operating System。系统按运行时边界拆分，并围绕两个原则优化：删除冗余 legacy 代码，以及通过插件复用成熟 provider，而不是重复构建引擎。

## 运行时边界

```text
apps/
  api/                 FastAPI 后端、domain services、plugin orchestration、基于文件的 MVP repositories
  web/                 面向 Studio、Workflow、Analytics、Assets、Components、MVP 的 Next.js 运营控制台
agent_runtime/         model gateway、prompt/config helpers、agent runtime 兼容层
interfaces/            生产时共享 primitives
packages/              后续共享 Python/TypeScript packages
services/              model、TTS、avatar、video、RAG、streaming、analytics 的服务边界占位
plugins/               顶层 plugin contracts/notes；后端实现位于 apps/api/app/plugins
workers/               异步/后台 workers
workflows/             workflow definitions/runners/visual assets
components/            可复用 live-room/studio/analytics 组合构件
assets/                Tavern 自有 raw/processed/generated assets
shared/                跨运行时 constants 与 shared types
infra/
  docker/              Dockerfiles、compose、本地服务依赖
  k8s/                 部署骨架
third_party/           OSS integration manifest，不放业务逻辑
legacy/                归档的 ViMax 时代 code/docs/assets
```

## 主产品流程

Phase 5 主生产工作流是 Agent Company、Workflow API 与 `/workflow` 控制台的统一主链路：

```text
商品 → 品牌 → 故事 → 剧本 → 分镜 → 导演 → 视觉导演 → 语音 → 数字人 → 直播间 → 视频 → 推流
```

Compliance Agent 作为酒类合规 gate，分别在脚本后、视觉导演后和推流前审查文案、视觉蓝图、素材映射、OBS 图层和发布方案；它不作为第 13 个主链路节点展示。

Phase 9 MVP 是独立参考黄金路径：

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

后端将 MVP 流程持久化为 `MvpLivePlan`，并同时产生 `WorkflowRun` / `WorkflowNodeRun` 记录以便审计。

## 插件架构

业务代码必须通过以下链路调用 provider：

```text
Plugin Interface
  ↓
Plugin Manager
  ↓
Plugin Loader
  ↓
Plugin Implementation
```

当前 providers：

| 类别 | Provider | 状态 | 说明 |
| --- | --- | --- | --- |
| Model | OpenAI Compatible Model Gateway | ready/由 gateway 配置 | 封装 `agent_runtime.llm.ModelGateway` |
| TTS | CosyVoice HTTP TTS | 配置后 ready | 外部 HTTP 服务，不将模型仓库和权重并入业务代码 |
| TTS | Edge TTS | ready | 本地/免费备用方案 |
| TTS | OpenAI Compatible TTS | 配置后 ready | 兼容 `/audio/speech` |
| TTS | Fish Speech | candidate_not_installed | 在 `third_party/manifest.json` 中跟踪 |
| Avatar | LiveTalking | candidate_not_installed | wrapper 候选 |
| Avatar | MuseTalk | candidate_not_installed | wrapper 候选 |
| Avatar | SadTalker | candidate_not_installed | 备用候选 |
| Video | FFmpeg / MoviePy Composer | ready | 本地 wrapper，不重复建设视频引擎 |
| RAG | Local Keyword RAG | ready | 基于文件的 MVP 检索 |

## 配置契约

统一环境变量：

- `TAVERN_APP_NAME`
- `TAVERN_ENV`
- `TAVERN_LOG_LEVEL`
- `TAVERN_WORKSPACE_ROOT`
- `TAVERN_STORAGE_BACKEND=file|postgres`
- `TAVERN_CORS_ORIGINS`
- `TAVERN_TTS_PROVIDER=edge|openai|sapi|placeholder`
- `TAVERN_MVP_TTS_PROVIDER=cosyvoice_tts|edge_tts|openai_compatible_tts|placeholder`
- `TAVERN_TTS_FALLBACK_PROVIDER=edge_tts|openai_compatible_tts|placeholder`
- `TAVERN_COSYVOICE_BASE_URL`
- `TAVERN_COSYVOICE_HEALTH_PATH`
- `TAVERN_COSYVOICE_SPEECH_PATH`
- `TAVERN_COSYVOICE_MODEL`
- `TAVERN_COSYVOICE_VOICE`
- `TAVERN_COSYVOICE_FORMAT`
- `TAVERN_COSYVOICE_TIMEOUT_SECONDS`
- `TAVERN_TTS_OUTPUT_DIR`
- `DATABASE_URL`
- `REDIS_URL`
- `RABBITMQ_URL`
- `MINIO_ENDPOINT`
- `MINIO_ACCESS_KEY`
- `MINIO_SECRET_KEY`
- `NEXT_PUBLIC_API_BASE`

本地密钥保存在 `configs/*.local.yaml` 和 `configs/agent.secrets.local.yaml`；这些文件不得提交。

## 日志与健康检查

- 后端日志通过 `apps/api/app/core/logging.py` 初始化。
- 运行时 settings 集中在 `apps/api/app/core/settings.py`。
- API 健康检查端点：
  - `/health` 返回 app/environment/storage 状态。
  - `/ready` 验证就绪契约；Postgres 模式要求配置 `DATABASE_URL`。

## 持久化

当前 MVP 存储仍然基于文件，以支持本地单机运行：

```text
.working_dir/workbench/*.json
.working_dir/live_rooms/**
```

PostgreSQL schema 位于 `infra/docker/postgres/001_init.sql`。迁移指南见 `docs/database/repository-migration.md`。

## Docker

本地 stack：

```bash
docker compose -f infra/docker/docker-compose.yml --env-file infra/docker/.env.example up --build
```

服务：

- `api`：FastAPI，`/ready` 健康检查
- `web`：支持 standalone build 的 Next.js，`/` 健康检查
- `worker`：可选 profile
- `postgres`
- `redis`
- `rabbitmq`
- `minio`

## CI/CD

GitHub Actions workflow：`.github/workflows/ci.yml`

Jobs：

- 后端：`uv sync --frozen --dev` + 选定回归测试
- 前端：`npm ci` + `npm run ci`（`typecheck` + `build`）

## Phase 10 后续规则

1. 新能力必须通过 plugin interfaces 或 workflow nodes 进入系统。
2. 不要把业务逻辑放进 `third_party/`。
3. 不要创建并行 API clients；使用 `apps/web/lib/api/config.ts`。
4. 运行时配置不要绕过 `apps/api/app/core/settings.py`。
5. 基于文件的 repositories 可用于 MVP/local 模式；Postgres 模式未配置时必须快速失败。
6. 任何新的运行时服务都必须暴露健康检查/就绪检查，并补充到 Docker/CI 文档。
