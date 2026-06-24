import WorkbenchShell from '@/components/live/WorkbenchShell';
import KnowledgeCenter from '@/components/live/KnowledgeCenter';
import { listKnowledgeDocuments, searchKnowledge } from '@/lib/api/workbench';

export default async function KnowledgePage() {
  const documents = await listKnowledgeDocuments();
  const chunks = await searchKnowledge('送礼 商务宴请 合规');
  return (
    <WorkbenchShell>
      <div className="page">
        <header className="hero">
          <div>
            <p className="eyebrow">Product RAG</p>
            <h1>商品知识库</h1>
            <p>支持 PDF、Word、Excel、CSV 自动切片、向量化和知识检索，回复前经过酒类合规过滤。</p>
          </div>
          <button>上传资料</button>
        </header>
        <KnowledgeCenter initialDocuments={documents} initialChunks={chunks} />
      </div>
    </WorkbenchShell>
  );
}
