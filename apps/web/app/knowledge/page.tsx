import WorkbenchShell from '@/components/live/WorkbenchShell';
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
        <section className="grid">
          {documents.map((document) => (
            <article key={document.document_id} className="card">
              <h2>{document.name}</h2>
              <dl>
                <dt>类型</dt><dd>{document.source_type}</dd>
                <dt>状态</dt><dd>{document.status}</dd>
                <dt>切片数</dt><dd>{document.chunk_count}</dd>
                <dt>商品</dt><dd>{document.product_id || '-'}</dd>
              </dl>
            </article>
          ))}
          <article className="card wide">
            <h2>检索样例</h2>
            <div className="timeline">
              {chunks.map((chunk) => (
                <article key={chunk.chunk_id} className="reply">
                  <span>{chunk.embedding_status}</span>
                  <p>{chunk.text}</p>
                </article>
              ))}
            </div>
          </article>
        </section>
      </div>
    </WorkbenchShell>
  );
}
