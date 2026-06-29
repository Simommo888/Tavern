# workflows 目录

Workflow definitions、runners、node adapters、templates 与可视化 workflow assets 的边界。

Phase 5 建立 API seed data 与 `/workflow` 可视化控制台使用的标准直播电商工作流：

```text
商品
  -> 品牌
  -> 故事
  -> 剧本
  -> 分镜
  -> 导演
  -> 视觉导演
  -> 语音
  -> 数字人
  -> 直播间
  -> 视频
  -> 推流
```

当前实现保持 runner 轻量且数据驱动：`WorkflowDefinition.nodes` 描述可视化 DAG，`WorkflowRun` 跟踪 run 级状态，`WorkflowNodeRun` 跟踪节点日志、成本、token 用量、产物与交接状态。

Compliance Agent 是脚本后、视觉导演后和推流前的酒类合规 gate；它可以审查主链路产物，但不作为第 13 个主 DAG 节点展示。

`n8n/` 存放可导入 n8n 的 visual workflow assets。当前 n8n 示例映射上述主链路，并调用 Tavern 现有 API 触发 MVP 闭环；Tavern 后端 `WorkflowDefinition` 仍是 source of truth。

后续 runner/provider 工作应扩展这些契约，而不是新增重复的 workflow pipelines。
