import WorkbenchShell from '@/components/live/WorkbenchShell';
import WorkflowCenter from '@/components/live/WorkflowCenter';
import { listWorkflowRules } from '@/lib/api/workbench';

export default async function WorkflowPage() {
  const rules = await listWorkflowRules();
  return (
    <WorkbenchShell>
      <div className="page">
        <header className="hero">
          <div>
            <p className="eyebrow">Event Driven Workflow</p>
            <h1>工作流引擎</h1>
            <p>配置用户进入、关注、加粉丝团、发弹幕、下单、退款、冷场等事件触发流程。</p>
          </div>
        </header>
        <WorkflowCenter initialRules={rules} />
      </div>
    </WorkbenchShell>
  );
}
