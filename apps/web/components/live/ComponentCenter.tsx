'use client';

import { useState } from 'react';
import { createComponent } from '@/lib/api/workbench';
import type { Asset, LiveComponent, Project } from '@/types/workbench';

export default function ComponentCenter({ initialComponents, assets, projects }: { initialComponents: LiveComponent[]; assets: Asset[]; projects: Project[] }) {
  const [components, setComponents] = useState(initialComponents);
  const [form, setForm] = useState({
    project_id: projects[0]?.project_id ?? '',
    name: '礼盒促单价格卡',
    component_type: 'ProductCard',
    source_asset_id: assets[0]?.asset_id ?? '',
    tags: '商品\n价格卡\n可复用',
    slot: 'product_card',
  });
  const [busy, setBusy] = useState(false);

  async function handleCreate() {
    if (!form.project_id) return;
    setBusy(true);
    try {
      const component = await createComponent(form.project_id, {
        name: form.name,
        component_type: form.component_type,
        source_asset_ids: form.source_asset_id ? [form.source_asset_id] : [],
        tags: form.tags.split('\n').map((tag) => tag.trim()).filter(Boolean),
        metadata: { slot: form.slot, phase: 'phase7_backend' },
        status: 'ready',
      });
      setComponents((items) => [component, ...items]);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="grid">
      <article className="card wide">
        <h2>从 Asset 生成 Component</h2>
        <div className="grid">
          <label>归属 Project
            <select value={form.project_id} onChange={(event) => setForm({ ...form, project_id: event.target.value })}>
              {projects.map((project) => <option key={project.project_id} value={project.project_id}>{project.name}</option>)}
            </select>
          </label>
          <label>组件名称<input value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} /></label>
          <label>组件类型<input value={form.component_type} onChange={(event) => setForm({ ...form, component_type: event.target.value })} /></label>
          <label>来源 Asset
            <select value={form.source_asset_id} onChange={(event) => setForm({ ...form, source_asset_id: event.target.value })}>
              <option value="">无</option>
              {assets.map((asset) => <option key={asset.asset_id} value={asset.asset_id}>{asset.name}</option>)}
            </select>
          </label>
          <label>Slot<input value={form.slot} onChange={(event) => setForm({ ...form, slot: event.target.value })} /></label>
          <label>Tags<textarea value={form.tags} onChange={(event) => setForm({ ...form, tags: event.target.value })} /></label>
        </div>
        <button onClick={handleCreate} disabled={busy || !form.project_id}>{busy ? '生成中...' : '生成 Component'}</button>
      </article>
      {components.map((component) => (
        <article key={component.component_id} className="card">
          <p className="eyebrow">{component.component_code} · {component.current_version}</p>
          <h2>{component.name}</h2>
          <dl>
            <div><dt>UUID</dt><dd>{component.uuid}</dd></div>
            <div><dt>类型</dt><dd>{component.component_type}</dd></div>
            <div><dt>来源 Asset</dt><dd>{component.source_asset_ids.length || '内置/Provider'}</dd></div>
            <div><dt>Slot</dt><dd>{String(component.metadata.slot ?? '-')}</dd></div>
            <div><dt>GMV</dt><dd>¥{component.gmv.toLocaleString('zh-CN')}</dd></div>
          </dl>
          <div className="tag-list">{component.tags.map((tag) => <span key={tag} className="tag">{tag}</span>)}</div>
        </article>
      ))}
    </section>
  );
}
