import WorkbenchShell from '@/components/live/WorkbenchShell';
import { listPlatformEvents, listPlatformMetrics } from '@/lib/api/workbench';

export default async function PlatformPage() {
  const [events, metrics] = await Promise.all([listPlatformEvents(), listPlatformMetrics()]);
  return (
    <WorkbenchShell>
      <div className="page">
        <header className="hero">
          <div>
            <p className="eyebrow">Live Platform Adapter</p>
            <h1>直播平台接入</h1>
            <p>统一适配抖音直播、淘宝直播、视频号，提供 start_stream、stop_stream、send_comment、get_comment、get_order 接口。</p>
          </div>
          <button>绑定平台账号</button>
        </header>
        <section className="metrics">
          <article className="card metric"><span>平台事件</span><strong>{events.length}</strong></article>
          <article className="card metric"><span>指标快照</span><strong>{metrics.length}</strong></article>
          <article className="card metric"><span>当前平台</span><strong>{metrics.at(-1)?.platform ?? 'manual'}</strong></article>
        </section>
        <section className="grid">
          <article className="card wide">
            <h2>平台事件流</h2>
            <pre>{JSON.stringify(events, null, 2)}</pre>
          </article>
          <article className="card wide">
            <h2>平台指标</h2>
            <pre>{JSON.stringify(metrics, null, 2)}</pre>
          </article>
        </section>
      </div>
    </WorkbenchShell>
  );
}
