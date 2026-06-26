import WorkbenchShell from '@/components/live/WorkbenchShell';
import KnowledgeCenter from '@/components/live/KnowledgeCenter';
import PageHero from '@/components/ui/PageHero';
import { listKnowledgeDocuments, searchKnowledge } from '@/lib/api/workbench';

export default async function KnowledgePage() {
  const documents = await listKnowledgeDocuments();
  const chunks = await searchKnowledge('送礼 商务宴请 合规');
  return (
    <WorkbenchShell>
      <div className="page">
        <PageHero
          eyebrow="Knowledge Base"
          title="企业知识中心：Agent 的长期记忆"
          description="Brand KB、Product KB、Industry KB、Live KB、Best Practice KB、Prompt KB、Component KB、Performance KB 均按 RAG 思路沉淀。"
          action={<button>上传资料</button>}
        />
        <KnowledgeCenter initialDocuments={documents} initialChunks={chunks} />
      </div>
    </WorkbenchShell>
  );
}
