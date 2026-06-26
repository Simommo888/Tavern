import WorkbenchShell from '@/components/live/WorkbenchShell';
import ComponentCenter from '@/components/live/ComponentCenter';
import MetricGrid from '@/components/ui/MetricGrid';
import PageHero from '@/components/ui/PageHero';
import { listAssets, listComponents, listLiveScenes, listProjects } from '@/lib/api/workbench';

export default async function ComponentsPage() {
  const [components, scenes, assets, projects] = await Promise.all([listComponents(), listLiveScenes(), listAssets(), listProjects()]);
  const totalGmv = components.reduce((sum, item) => sum + item.gmv, 0);
  const best = [...components].sort((a, b) => b.gmv - a.gmv)[0];
  const usedInScene = new Set(scenes.flatMap((scene) => scene.component_ids));
  return (
    <WorkbenchShell>
      <div className="page">
        <PageHero
          eyebrow="Component Library"
          title="Component 是可复用的直播间积木"
          description="Background、Avatar、ProductCard、POP、Subtitle、Camera 等组件全部编号、版本化、可追踪，并可组合成 Scene，再进入 LiveRoom。"
          action={<button>从 Asset 生成组件</button>}
        />
        <MetricGrid metrics={[
          { label: '组件数量', value: components.length, hint: '可复用资产' },
          { label: '进入 Scene', value: usedInScene.size, hint: 'Component -> Scene' },
          { label: '累计 GMV', value: `¥${totalGmv.toLocaleString('zh-CN')}`, hint: '组件归因表现' },
          { label: '最佳组件', value: best?.component_code ?? '-', hint: best?.name ?? '暂无' },
        ]} />
        <ComponentCenter initialComponents={components} assets={assets} projects={projects} />
      </div>
    </WorkbenchShell>
  );
}
