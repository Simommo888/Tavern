import WorkbenchShell from '@/components/live/WorkbenchShell';
import AssetCenter from '@/components/live/AssetCenter';
import MetricGrid from '@/components/ui/MetricGrid';
import PageHero from '@/components/ui/PageHero';
import { listAssets, listProjects } from '@/lib/api/workbench';

export default async function AssetsPage() {
  const [assets, projects] = await Promise.all([listAssets(), listProjects()]);
  const converted = assets.filter((asset) => asset.converted_component_ids.length > 0).length;
  return (
    <WorkbenchShell>
      <div className="page">
        <PageHero
          eyebrow="Asset Library"
          title="Asset 是直播间组件化的原材料"
          description="产品图、品牌 Logo、背景图、视频片段、音频、BGM、字体和资料文档先作为 Asset 入库，再转换成可追踪 Component。Phase 7 在后台补齐登记入口，Phase 6 的 UUID、Version、Metadata、Tags 继续保留。"
          action={<button>上传素材</button>}
        />
        <MetricGrid metrics={[
          { label: 'Asset 数量', value: assets.length, hint: '原始素材入口' },
          { label: '已组件化', value: converted, hint: 'Asset -> Component' },
          { label: '版本协议', value: 'UUID + Version', hint: '可审计可追踪' },
          { label: '组合链路', value: 'Asset → Component', hint: '下一层进入组件库' },
        ]} />
        <AssetCenter initialAssets={assets} projects={projects} />
      </div>
    </WorkbenchShell>
  );
}
