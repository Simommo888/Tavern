import WorkbenchShell from '@/components/live/WorkbenchShell';
import PromptCenter from '@/components/live/PromptCenter';
import MetricGrid from '@/components/ui/MetricGrid';
import PageHero from '@/components/ui/PageHero';
import { listPromptTemplates, listPromptVersions } from '@/lib/api/workbench';

export default async function PromptLibraryPage() {
  const [prompts, versions] = await Promise.all([listPromptTemplates(), listPromptVersions()]);
  const totalUse = versions.reduce((sum, item) => sum + item.use_count, 0);
  const best = [...versions].sort((a, b) => b.score - a.score)[0];
  return (
    <WorkbenchShell>
      <div className="page">
        <PageHero
          eyebrow="Prompt Library"
          title="Prompt 是可版本化、可回滚、可 A/B 的生产资产"
          description="Brand Analysis、Product Selling Point、Story、Script、Storyboard、Voice、Scene、QA、Optimization Prompt 都要记录成本和效果；后台支持新建模板和渲染检查。"
          action={<button>新建 Prompt</button>}
        />
        <MetricGrid metrics={[
          { label: 'Prompt', value: prompts.length, hint: '模板数量' },
          { label: '版本', value: versions.length, hint: '可回滚版本' },
          { label: '累计使用', value: totalUse, hint: '调用次数' },
          { label: '最佳版本', value: best?.version ?? '-', hint: best?.name ?? '暂无' },
        ]} />
        <PromptCenter initialPrompts={prompts} initialVersions={versions} />
      </div>
    </WorkbenchShell>
  );
}
