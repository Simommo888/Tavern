import WorkbenchShell from '@/components/live/WorkbenchShell';
import { listPlatformMetrics } from '@/lib/api/workbench';

export default async function AnalyticsPage() {
  const metrics = await listPlatformMetrics();
  const latest = metrics.at(-1);
  return (
    <WorkbenchShell>
      <div className="page">
        <header className="hero">
          <div>
            <p className="eyebrow">Analytics Center</p>
            <h1>数据中心</h1>
            <p>观察 GMV、成交单量、在线人数、互动率和转化率，支撑直播复盘和话术优化。</p>
          </div>
        </header>
        <section className="metrics">
          <article className="card metric"><span>GMV</span><strong>¥{latest?.gmv.toLocaleString('zh-CN') ?? 0}</strong></article>
          <article className="card metric"><span>成交单量</span><strong>{latest?.order_count ?? 0}</strong></article>
          <article className="card metric"><span>在线人数</span><strong>{latest?.online_users.toLocaleString('zh-CN') ?? 0}</strong></article>
          <article className="card metric"><span>互动率</span><strong>{(((latest?.interaction_rate ?? 0) * 100).toFixed(1))}%</strong></article>
          <article className="card metric"><span>转化率</span><strong>{(((latest?.conversion_rate ?? 0) * 100).toFixed(1))}%</strong></article>
          <article className="card metric"><span>平台</span><strong>{latest?.platform ?? '-'}</strong></article>
        </section>
        <section className="card" style={{ marginTop: 20 }}>
          <h2>指标快照</h2>
          <pre>{JSON.stringify(metrics, null, 2)}</pre>
        </section>
      </div>
    </WorkbenchShell>
  );
}
