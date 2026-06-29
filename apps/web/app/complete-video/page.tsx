import WorkbenchShell from '@/components/live/WorkbenchShell';
import ProductVideoWorkflowRunner from '@/components/live/ProductVideoWorkflowRunner';
import PageHero from '@/components/ui/PageHero';
import { getProductVideoWorkflowRun, listProducts, listProjects, listWorkflowDefinitions, listWorkflowRuns } from '@/lib/api/workbench';
import type { ProductVideoWorkflowSnapshot } from '@/types/workbench';

export default async function CompleteVideoWorkflowPage() {
  const [projects, products, definitions, runs] = await Promise.all([
    listProjects(),
    listProducts(),
    listWorkflowDefinitions(),
    listWorkflowRuns(),
  ]);
  const productVideoDefinition = definitions.find((definition) => definition.version === 'product-video-v1');
  const latestRun = runs.find((run) => run.workflow_definition_id === productVideoDefinition?.workflow_definition_id);
  let initialSnapshot: ProductVideoWorkflowSnapshot | null = null;
  if (latestRun) {
    try {
      initialSnapshot = await getProductVideoWorkflowRun(latestRun.workflow_run_id);
    } catch {
      initialSnapshot = null;
    }
  }
  const n8nPort = process.env.N8N_HOST_PORT ?? '5678';
  const n8nUrl = process.env.N8N_EDITOR_BASE_URL ?? `http://127.0.0.1:${n8nPort}`;

  return (
    <WorkbenchShell>
      <div className="page">
        <PageHero
          eyebrow="Complete Video Workflow"
          title="商品/品牌资料到完整视频的逐节点 Agent 工作流"
          description="创建 WorkflowRun 后，n8n 和 Web 控制台都可以按节点驱动 Planner、Story、Script、Director、Visual Director、Asset、Image、Video、Editor，并查看每个 Agent 的输入、Provider 配置、产物 URI 与最终 complete_video。"
          action={<a href={n8nUrl} target="_blank" rel="noreferrer"><button>打开 n8n</button></a>}
        />
        <ProductVideoWorkflowRunner
          projects={projects}
          products={products}
          initialSnapshot={initialSnapshot}
          n8nImportPath="D:\\Tavern\\workflows\\n8n\\tavern-product-to-streaming.workflow.json"
          n8nUrl={n8nUrl}
        />
      </div>
    </WorkbenchShell>
  );
}
