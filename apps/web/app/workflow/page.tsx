import WorkbenchShell from '@/components/live/WorkbenchShell';
import PageHero from '@/components/ui/PageHero';
import ProgressBar from '@/components/ui/ProgressBar';
import StatusBadge from '@/components/ui/StatusBadge';
import WorkflowCenter from '@/components/live/WorkflowCenter';
import { listWorkflowDefinitions, listWorkflowNodeRuns, listWorkflowRules, listWorkflowRuns } from '@/lib/api/workbench';

const canonicalStages = ['商品', '品牌', '故事', '剧本', '分镜', '导演', '视觉导演', '语音', '数字人', '直播间', '视频', '推流'];

export default async function WorkflowPage() {
  const [rules, definitions, runs] = await Promise.all([
    listWorkflowRules(),
    listWorkflowDefinitions(),
    listWorkflowRuns(),
  ]);
  const definition = definitions.find((item) => item.nodes.some((node) => node.id === 'streaming')) ?? definitions[0];
  const run = runs.find((item) => item.workflow_definition_id === definition?.workflow_definition_id) ?? runs[0];
  const nodeRuns = run ? await listWorkflowNodeRuns(run.workflow_run_id) : [];
  const completedCount = nodeRuns.filter((item) => item.status === 'succeeded').length;
  const currentNode = definition?.nodes.find((node) => node.id === run?.current_node_id);

  return (
    <WorkbenchShell>
      <div className="page">
        <PageHero
          eyebrow="Visual Workflow"
          title="商品到推流的 AI 直播生产工作流"
          description="Phase 5 将 Workflow 固化为商品→品牌→故事→剧本→分镜→导演→视觉导演→语音→数字人→直播间→视频→推流。每个节点都产出可审计、可复用、可重跑的生产资产。"
          action={<button>重跑当前节点</button>}
        />

        <section className="workflow-strip card wide">
          {canonicalStages.map((stage, index) => <span key={stage}>{index + 1}. {stage}</span>)}
        </section>

        {run && (
          <section className="card wide" style={{ marginTop: 20 }}>
            <div className="card-row">
              <div>
                <h2>{definition?.name ?? 'Product-to-Streaming Workflow'}</h2>
                <p>{definition?.description ?? '商品到推流的直播生产主链路。'}</p>
              </div>
              <StatusBadge status={run.status} />
            </div>
            <ProgressBar value={run.progress} />
            <dl className="plain workflow-run-meta">
              <div><dt>当前节点</dt><dd>{currentNode?.label || run.current_node_id || '等待调度'}</dd></div>
              <div><dt>已完成</dt><dd>{completedCount}/{definition?.nodes.length ?? 0}</dd></div>
              <div><dt>Token</dt><dd>{run.token_count.toLocaleString('zh-CN')}</dd></div>
              <div><dt>Cost</dt><dd>${run.cost_estimate.toFixed(2)}</dd></div>
              <div><dt>耗时</dt><dd>{run.duration_seconds}s</dd></div>
            </dl>
            <div className="timeline">
              {run.logs.map((log) => <small key={log}>• {log}</small>)}
            </div>
          </section>
        )}

        <section className="workflow-board visual-workflow-board">
          {(definition?.nodes ?? []).map((node, index) => {
            const nodeRun = nodeRuns.find((item) => item.node_id === node.id);
            const next = definition?.edges.find((edge) => edge.source === node.id)?.target;
            const nextNode = definition?.nodes.find((item) => item.id === next);
            return (
              <article key={node.id} className={`card workflow-node workflow-node-${nodeRun?.status ?? 'queued'}`}>
                <p className="eyebrow">{String(node.stage ?? node.id).toUpperCase()}</p>
                <div className="workflow-node-index">{index + 1}</div>
                <h2>{node.label}</h2>
                <StatusBadge status={nodeRun?.status ?? 'queued'} />
                <p>{node.description ?? '等待定义节点职责'}</p>
                <dl>
                  <div><dt>Agent</dt><dd>{node.agent}</dd></div>
                  <div><dt>产物</dt><dd>{node.artifact ?? 'artifact'}</dd></div>
                  <div><dt>复用</dt><dd>{node.reusable ? '可复用' : '按运行生成'}</dd></div>
                  <div><dt>交接</dt><dd>{nextNode ? `→ ${nextNode.label}` : '完成推流'}</dd></div>
                </dl>
                <div className="timeline">
                  {(nodeRun?.logs ?? ['等待上游节点完成']).slice(-2).map((log) => <small key={log}>• {log}</small>)}
                </div>
                <small>Token {(nodeRun?.token_count ?? 0).toLocaleString('zh-CN')} · {nodeRun?.duration_seconds ?? 0}s</small>
              </article>
            );
          })}
        </section>

        <section className="card wide" style={{ marginTop: 20 }}>
          <div className="card-row">
            <div>
              <h2>事件触发规则</h2>
              <p>触发规则只负责启动或驱动 Workflow，不再替代商品到推流的主链路。</p>
            </div>
          </div>
          <WorkflowCenter initialRules={rules} />
        </section>
      </div>
    </WorkbenchShell>
  );
}
