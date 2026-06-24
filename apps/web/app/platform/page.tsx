import WorkbenchShell from '@/components/live/WorkbenchShell';
import PlatformCenter from '@/components/live/PlatformCenter';
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
        </header>
        <PlatformCenter initialEvents={events} initialMetrics={metrics} />
      </div>
    </WorkbenchShell>
  );
}
