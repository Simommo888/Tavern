'use client';

import { useState } from 'react';
import { generateScriptTemplate } from '@/lib/api/workbench';
import type { ScriptTemplate } from '@/types/workbench';

const categories = [
  ['opening', '开场话术'],
  ['product', '讲品话术'],
  ['sales', '促单话术'],
  ['interaction', '互动话术'],
  ['thanks', '感谢话术'],
];

export default function ScriptCenter({ initialTemplates }: { initialTemplates: ScriptTemplate[] }) {
  const [templates, setTemplates] = useState(initialTemplates);
  const [busy, setBusy] = useState('');

  async function handleGenerate(category: string) {
    setBusy(category);
    try {
      const template = await generateScriptTemplate(category);
      setTemplates((items) => [template, ...items]);
    } finally {
      setBusy('');
    }
  }

  return (
    <section className="grid">
      <article className="card wide">
        <h2>AI 生成话术</h2>
        <div className="quick">
          {categories.map(([category, label]) => (
            <button key={category} onClick={() => handleGenerate(category)} disabled={busy === category}>
              {busy === category ? '生成中...' : label}
            </button>
          ))}
        </div>
      </article>
      {templates.map((template) => (
        <article key={template.template_id} className="card">
          <h2>{template.name}</h2>
          <p className="eyebrow">{template.category}{template.ai_generated ? ' · AI Generated' : ''}</p>
          <p>{template.content}</p>
          <small>{template.tags.join('、')}</small>
        </article>
      ))}
    </section>
  );
}
