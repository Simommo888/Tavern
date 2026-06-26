import WorkbenchShell from '@/components/live/WorkbenchShell';
import AnalyticsCenter from '@/components/live/AnalyticsCenter';
import MetricGrid from '@/components/ui/MetricGrid';
import PageHero from '@/components/ui/PageHero';
import { getAnalyticsOverview } from '@/lib/api/workbench';

export default async function AnalyticsPage() {
  const overview = await getAnalyticsOverview();
  const bestComponent = overview.component_ranking[0];
  const bestPrompt = overview.prompt_ranking[0];
  const bestAvatar = overview.avatar_ranking[0];
  return (
    <WorkbenchShell>
      <div className="page">
        <PageHero
          eyebrow="Company Memory Analytics"
          title="数据中心沉淀 GMV / CTR / CVR / Prompt / Component / Avatar 经验"
          description="Phase 8 不再只展示平台快照，而是把直播场次、组件、Prompt、数字人和 Best Practice 统一排名，形成可复用的 AI 直播经验库。"
          action={<button>一键复用最佳方案</button>}
        />
        <MetricGrid metrics={[
          { label: 'GMV', value: `¥${overview.summary.gmv.toLocaleString('zh-CN')}`, hint: `${overview.summary.session_count} 场直播累计` },
          { label: 'CTR / CVR', value: `${(overview.summary.ctr * 100).toFixed(1)}% / ${(overview.summary.cvr * 100).toFixed(1)}%`, hint: '全局平均转化表现' },
          { label: '最佳组件', value: bestComponent?.component_code ?? '-', hint: bestComponent?.name ?? '暂无' },
          { label: '最佳 Prompt / Avatar', value: `${bestPrompt?.version ?? '-'} / ${bestAvatar?.name ?? '-'}`, hint: '生产资产效果归因' },
        ]} />
        <AnalyticsCenter overview={overview} />
      </div>
    </WorkbenchShell>
  );
}
