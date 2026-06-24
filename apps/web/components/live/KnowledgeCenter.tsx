'use client';

import { useState } from 'react';
import { createKnowledgeDocument, searchKnowledge } from '@/lib/api/workbench';
import type { KnowledgeChunk, KnowledgeDocument } from '@/types/workbench';

export default function KnowledgeCenter({ initialDocuments, initialChunks }: { initialDocuments: KnowledgeDocument[]; initialChunks: KnowledgeChunk[] }) {
  const [documents, setDocuments] = useState(initialDocuments);
  const [chunks, setChunks] = useState(initialChunks);
  const [form, setForm] = useState({ name: '龙八酱香酒商品资料', source_type: 'text', text: '龙八酱香酒适合成年人商务宴请和节日送礼。\n卖点包括酱香风格、礼盒包装、聚会场景。\n合规提醒：不宣传保健、养生或医疗功效。' });
  const [query, setQuery] = useState('送礼 商务宴请');

  async function handleCreate() {
    const document = await createKnowledgeDocument(form);
    setDocuments((items) => [document, ...items]);
  }

  async function handleSearch() {
    setChunks(await searchKnowledge(query));
  }

  return (
    <section className="grid">
      <article className="card wide">
        <h2>上传并索引资料</h2>
        <label>资料名称<input value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} /></label>
        <label>资料类型<input value={form.source_type} onChange={(event) => setForm({ ...form, source_type: event.target.value })} /></label>
        <label>文本内容<textarea value={form.text} onChange={(event) => setForm({ ...form, text: event.target.value })} /></label>
        <button onClick={handleCreate}>保存并自动切片</button>
      </article>
      {documents.map((document) => (
        <article key={document.document_id} className="card">
          <h2>{document.name}</h2>
          <dl>
            <dt>类型</dt><dd>{document.source_type}</dd>
            <dt>状态</dt><dd>{document.status}</dd>
            <dt>切片数</dt><dd>{document.chunk_count}</dd>
          </dl>
        </article>
      ))}
      <article className="card wide">
        <h2>知识检索</h2>
        <div className="ask-row">
          <input value={query} onChange={(event) => setQuery(event.target.value)} />
          <button onClick={handleSearch}>检索</button>
        </div>
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
  );
}
