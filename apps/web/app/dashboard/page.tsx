import Link from 'next/link';
import WorkbenchShell from '@/components/live/WorkbenchShell';
import MetricGrid from '@/components/ui/MetricGrid';
import PageHero from '@/components/ui/PageHero';
import ProgressBar from '@/components/ui/ProgressBar';
import StatusBadge from '@/components/ui/StatusBadge';
import { getDashboardSummary, listAgents, listProjects, listWorkflowRuns } from '@/lib/api/workbench';

export default async function DashboardPage() {
  const [summary, agents, projects, workflowRuns] = await Promise.all([
    getDashboardSummary(),
    listAgents(),
    listProjects(),
    listWorkflowRuns(),
  ]);
  const latestRun = workflowRuns[0];
  return (
    <WorkbenchShell>
      <div className="page">
        <PageHero
          eyebrow="AI Company Control Center"
          title="你的 AI 直播公司正在工作"
          description="CEO、品牌、商品、脚本、导演、声音、数字人、场景、视频与数据 Agent 共同完成直播生产流水线。首页优先展示 AI 员工状态，而不是传统后台指标。"
          action={<Link href="/projects"><button>创建 / 进入项目</button></Link>}
        />

        <MetricGrid metrics={[
          { label: '活跃 Project', value: summary.project_count, hint: '所有内容归属项目' },
          { label: '工作中 Agent', value: summary.active_agent_count, hint: 'AI 公司当前产能' },
          { label: '可复用组件', value: summary.component_count, hint: '公司资产沉淀' },
          { label: 'Workflow Runs', value: summary.workflow_run_count, hint: '生产流程记录' },
        ]} />

        <section className="grid three">
          {agents.map((agent) => (
            <article key={agent.agent_id} className="card agent-card">
              <header>
                <div className="card-row">
                  <div className="agent-avatar">{agent.name.slice(0, 1)}</div>
                  <div>
                    <h2>{agent.name}</h2>
                    <small>{agent.department} · {agent.role}</small>
                  </div>
                </div>
                <StatusBadge status={agent.status} />
              </header>
              <p>{agent.current_task || '等待 CEO Agent 分配任务'}</p>
              <ProgressBar value={agent.progress} />
              <dl>
                <div><dt>Token</dt><dd>{agent.token_count.toLocaleString('zh-CN')}</dd></div>
                <div><dt>耗时</dt><dd>{agent.elapsed_seconds}s</dd></div>
              </dl>
              <div className="timeline">
                {agent.logs.slice(-2).map((log) => <small key={log}>• {log}</small>)}
              </div>
            </article>
          ))}
        </section>

        <section className="grid">
          <article className="card wide">
            <div className="card-row">
              <div>
                <h2>当前生产流程</h2>
                <p>{latestRun ? `正在执行节点：${latestRun.current_node_id || '等待调度'}` : '暂无运行中的工作流'}</p>
              </div>
              {latestRun && <StatusBadge status={latestRun.status} />}
            </div>
            {latestRun && <ProgressBar value={latestRun.progress} />}
            <div className="timeline">
              {(latestRun?.logs ?? ['等待上传品牌与商品资料']).map((log) => <article key={log} className="reply"><span>Workflow Log</span><p>{log}</p></article>)}
            </div>
          </article>

          {projects.map((project) => (
            <article key={project.project_id} className="card">
              <div className="card-row">
                <h2>{project.name}</h2>
                <StatusBadge status={project.status} />
              </div>
              <p>{project.objective}</p>
              <div className="tag-list">{project.tags.map((tag) => <span key={tag} className="tag">{tag}</span>)}</div>
            </article>
          ))}
        </section>
      </div>
    </WorkbenchShell>
  );
}
