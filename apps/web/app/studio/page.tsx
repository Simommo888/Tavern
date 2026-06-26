import WorkbenchShell from '@/components/live/WorkbenchShell';
import PageHero from '@/components/ui/PageHero';
import StatusBadge from '@/components/ui/StatusBadge';
import { listAgents, listAssets, listProducts, listScriptTemplates, listWorkflowRuns } from '@/lib/api/workbench';

export default async function StudioPage() {
  const [products, assets, scripts, agents, runs] = await Promise.all([
    listProducts(),
    listAssets(),
    listScriptTemplates(),
    listAgents(),
    listWorkflowRuns(),
  ]);
  const activeAgents = agents.filter((agent) => ['working', 'blocked'].includes(agent.status));
  const latestRun = runs[0];
  return (
    <WorkbenchShell>
      <div className="page">
        <PageHero
          eyebrow="Creative Studio"
          title="创作中心：脚本、分镜、口播与视频预览"
          description="左侧是品牌/商品/知识库，中间是创作内容，右侧是 AI Agent 协作面板。每个片段都可以单独重新生成、优化和版本对比。"
          action={<button>运行 Script Agent</button>}
        />
        <section className="grid" style={{ gridTemplateColumns: '0.8fr 1.4fr 0.8fr' }}>
          <article className="card">
            <h2>项目资料</h2>
            <div className="timeline">
              {products.map((product) => (
                <article key={product.product_id} className="reply">
                  <span>Product</span>
                  <p>{product.product_name}</p>
                  <small>{product.selling_points.join('、')}</small>
                </article>
              ))}
              {assets.slice(0, 4).map((asset) => (
                <article key={asset.asset_id} className="reply">
                  <span>{asset.asset_type}</span>
                  <p>{asset.name}</p>
                  <small>{asset.tags.join('、')}</small>
                </article>
              ))}
            </div>
          </article>

          <article className="card">
            <div className="card-row">
              <div>
                <h2>当前创作内容</h2>
                <small>{latestRun ? `Workflow: ${latestRun.status} · ${Math.round(latestRun.progress * 100)}%` : '等待工作流'}</small>
              </div>
              {latestRun && <StatusBadge status={latestRun.status} />}
            </div>
            <div className="timeline">
              {scripts.map((script) => (
                <article key={script.template_id} className="reply">
                  <span>{script.category} · {script.ai_generated ? 'AI Generated' : 'Manual'}</span>
                  <p>{script.content}</p>
                  <small>{script.tags.join('、')}</small>
                </article>
              ))}
            </div>
          </article>

          <article className="card">
            <h2>AI Agent 面板</h2>
            <div className="timeline">
              {activeAgents.map((agent) => (
                <article key={agent.agent_id} className="reply">
                  <span>{agent.department} · {agent.status}</span>
                  <p>{agent.name}</p>
                  <small>{agent.current_task}</small>
                </article>
              ))}
            </div>
            <div className="quick">
              <button className="ghost-button">单独重新生成</button>
              <button className="ghost-button">优化当前段落</button>
              <button className="ghost-button">版本对比</button>
            </div>
          </article>
        </section>
      </div>
    </WorkbenchShell>
  );
}
