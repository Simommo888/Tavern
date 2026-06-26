# workflows

Workflow definitions, runners, node adapters, templates and visual workflow assets.

Phase 5 establishes the canonical live-commerce workflow used by the API seed data and `/workflow` visual console:

```text
商品
  -> 品牌
  -> 故事
  -> 剧本
  -> 分镜
  -> 语音
  -> 数字人
  -> 直播间
  -> 视频
  -> 推流
```

The current implementation keeps the runner lightweight and data-driven: `WorkflowDefinition.nodes` describes the visual DAG, `WorkflowRun` tracks run-level state, and `WorkflowNodeRun` tracks node logs, cost, token usage, artifacts and handoff state.

Future runner/provider work should extend these contracts instead of adding duplicate workflow pipelines.
