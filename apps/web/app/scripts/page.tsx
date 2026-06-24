import WorkbenchShell from '@/components/live/WorkbenchShell';
import ScriptCenter from '@/components/live/ScriptCenter';
import { listScriptTemplates } from '@/lib/api/workbench';

export default async function ScriptsPage() {
  const templates = await listScriptTemplates();
  return (
    <WorkbenchShell>
      <div className="page">
        <header className="hero">
          <div>
            <p className="eyebrow">Script Center</p>
            <h1>话术中心</h1>
            <p>管理开场、讲品、促单、互动、感谢话术，并支持酒类合规 AI 生成。</p>
          </div>
        </header>
        <ScriptCenter initialTemplates={templates} />
      </div>
    </WorkbenchShell>
  );
}
