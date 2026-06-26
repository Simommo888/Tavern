import WorkbenchShell from '@/components/live/WorkbenchShell';
import PlatformCenter from '@/components/live/PlatformCenter';
import PageHero from '@/components/ui/PageHero';
import { listPlatformEvents, listPlatformMetrics } from '@/lib/api/workbench';

export default async function PlatformPage() {
  const [events, metrics] = await Promise.all([listPlatformEvents(), listPlatformMetrics()]);
  return (
    <WorkbenchShell>
      <div className="page">
        <PageHero
          eyebrow="Live Platform Adapter"
          title="直播平台接入与数据回流"
          description="统一适配抖音直播、淘宝直播、视频号和 OBS/RTMP。MVP 先支持手动模拟事件和指标快照，后续接真实平台。"
        />
        <PlatformCenter initialEvents={events} initialMetrics={metrics} />
      </div>
    </WorkbenchShell>
  );
}
