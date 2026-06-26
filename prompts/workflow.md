# Tavern Phase 5 Workflow

Tavern Phase 5 聚焦标准直播电商工作流。

## 标准 DAG

```text
product
  -> brand
  -> story
  -> script
  -> storyboard
  -> voice
  -> avatar
  -> live_room
  -> video
  -> streaming
```

## 运行规则

- 将每个 stage 都视为可复用、会产生产物的节点。
- 优先删除重复 stage 逻辑，而不是新增变体。
- workflow API、seed data 与 UI 可视化必须和上方标准 DAG 保持同步。
- 当 run 已处于 pipeline 中段时，从当前节点恢复，不要重新创建早期 stage。
- 事件触发规则独立于主 DAG；它们可以启动 workflow runs，但不能替代 pipeline。
- 最终节点是 `streaming`；只有该节点成功后，run 才算完成。

## 阶段契约

每个 workflow node 都应展示：

- stage name
- agent 或 owner
- current status
- 最新 log 或 output summary
- token count 和 duration
- 下游 handoff

## 可视化要求

- `/workflow` 必须把完整 DAG 渲染成连通 lane。
- 已完成 stage 应继续可见，以便审计和复用。
- 当前 stage 必须一眼可见。
- 看板应支持后续复用于分支 workflow。

## 输出期望

讨论或生成 workflow output 时，必须说明：

1. 当前正在运行哪个 stage；
2. 该 stage 产出什么 artifact；
3. 下一个 handoff 是什么；
4. 该 stage 是否可复用或跳过。

只使用直播电商术语。
不要回退到 legacy ViMax planning language。
