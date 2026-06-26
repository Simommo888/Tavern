import WorkbenchShell from '@/components/live/WorkbenchShell';
import PageHero from '@/components/ui/PageHero';
import ProgressBar from '@/components/ui/ProgressBar';
import StatusBadge from '@/components/ui/StatusBadge';
import { listAgentRuns, listAgents } from '@/lib/api/workbench';

export default async function AgentsPage() {
  const [agents, runs] = await Promise.all([listAgents(), listAgentRuns()]);
  return (
    <WorkbenchShell>
      <div className="page">
        <PageHero
          eyebrow="Agent Company"
          title="AI 员工组织架构"
          description="每个 Agent 都有岗位、任务、日志、成本和输出。用户管理的是一家 AI 公司，而不是一堆按钮。"
          action={<button>配置 Agent</button>}
        />
        <section className="grid three">
          {agents.map((agent) => (
            <article key={agent.agent_id} className="card agent-card">
              <header>
                <div className="card-row">
                  <div className="agent-avatar">{agent.name.slice(0, 1)}</div>
                  <div>
                    <h2>{agent.name}</h2>
                    <small>{agent.department}</small>
                  </div>
                </div>
                <StatusBadge status={agent.status} />
              </header>
              <p>{agent.role}</p>
              <strong>{agent.current_task || '等待任务'}</strong>
              <ProgressBar value={agent.progress} />
              <dl>
                <div><dt>模型</dt><dd>{agent.model_provider}</dd></div>
                <div><dt>Token</dt><dd>{agent.token_count.toLocaleString('zh-CN')}</dd></div>
                <div><dt>成本</dt><dd>${agent.cost_estimate.toFixed(3)}</dd></div>
                <div><dt>耗时</dt><dd>{agent.elapsed_seconds}s</dd></div>
              </dl>
            </article>
          ))}
        </section>
        <section className="card wide" style={{ marginTop: 20 }}>
          <h2>Agent Run 历史</h2>
          <div className="timeline">
            {runs.map((run) => (
              <article key={run.run_id} className="reply">
                <span>{run.status} · {run.token_count.toLocaleString('zh-CN')} tokens</span>
                <p>{run.task}</p>
                <small>{run.logs.join(' / ')}</small>
              </article>
            ))}
          </div>
        </section>
      </div>
    </WorkbenchShell>
  );
}
