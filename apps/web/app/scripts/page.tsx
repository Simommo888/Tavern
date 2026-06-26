import WorkbenchShell from '@/components/live/WorkbenchShell';
import ScriptCenter from '@/components/live/ScriptCenter';
import PageHero from '@/components/ui/PageHero';
import { listScriptTemplates } from '@/lib/api/workbench';

export default async function ScriptsPage() {
  const templates = await listScriptTemplates();
  return (
    <WorkbenchShell>
      <div className="page">
        <PageHero
          eyebrow="Script Library"
          title="直播剧本与话术资产"
          description="开场、讲品、促单、互动、感谢话术都可以被 Agent 生成、人工编辑、版本对比，并关联历史表现。"
        />
        <ScriptCenter initialTemplates={templates} />
      </div>
    </WorkbenchShell>
  );
}
