# Tavern Phase 5 Workflow

Tavern Phase 5 focuses on the canonical live-commerce workflow.

## Canonical DAG

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

## Operating rules

- Treat every stage as a reusable artifact-producing node.
- Prefer deleting duplicate stage logic over adding new variants.
- Keep the workflow API, seed data, and UI visualization in sync with the canonical DAG above.
- When a run is mid-pipeline, resume from the current node instead of recreating earlier stages.
- Event-trigger rules are separate from the main DAG; they start workflow runs but do not replace the pipeline.
- The final node is `streaming`; a run is complete only after it succeeds.

## Stage contract

Each workflow node should surface:

- stage name
- agent or owner
- current status
- latest log or output summary
- token count and duration
- downstream handoff

## Visual requirements

- `/workflow` must render the full DAG as a connected lane.
- Completed stages should remain visible for audit and reuse.
- The current stage must be obvious at a glance.
- The board should support later reuse for branching workflows.

## Output expectations

When discussing or generating workflow output, describe:

1. which stage is running,
2. what artifact it produces,
3. what the next handoff is,
4. whether the stage can be reused or skipped.

Use live-commerce terminology only.
Do not fall back to legacy ViMax planning language.
