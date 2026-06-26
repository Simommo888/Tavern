# workflows 目录

Workflow definitions、runners、node adapters、templates 与可视化 workflow assets 的边界。

Phase 5 建立 API seed data 与 `/workflow` 可视化控制台使用的标准直播电商工作流：

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

当前实现保持 runner 轻量且数据驱动：`WorkflowDefinition.nodes` 描述可视化 DAG，`WorkflowRun` 跟踪 run 级状态，`WorkflowNodeRun` 跟踪节点日志、成本、token 用量、产物与交接状态。

后续 runner/provider 工作应扩展这些契约，而不是新增重复的 workflow pipelines。
