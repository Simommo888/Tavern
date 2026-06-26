'use client';

import { useState } from 'react';
import { createAsset } from '@/lib/api/workbench';
import type { Asset, Project } from '@/types/workbench';

export default function AssetCenter({ initialAssets, projects }: { initialAssets: Asset[]; projects: Project[] }) {
  const [assets, setAssets] = useState(initialAssets);
  const [form, setForm] = useState({
    project_id: projects[0]?.project_id ?? '',
    name: '直播间权益贴片',
    asset_type: 'image',
    object_key: 'minio://assets/promo-pop.png',
    preview_url: '/assets/promo-pop.png',
    tags: '促单\n权益\n贴片',
  });
  const [busy, setBusy] = useState(false);

  async function handleCreate() {
    if (!form.project_id) return;
    setBusy(true);
    try {
      const asset = await createAsset(form.project_id, {
        name: form.name,
        asset_type: form.asset_type,
        object_key: form.object_key,
        preview_url: form.preview_url,
        tags: form.tags.split('\n').map((tag) => tag.trim()).filter(Boolean),
        metadata: { source: 'studio_upload', phase: 'phase7_backend' },
        status: 'ready',
      });
      setAssets((items) => [asset, ...items]);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="grid">
      <article className="card wide">
        <h2>登记素材</h2>
        <div className="grid">
          <label>归属 Project
            <select value={form.project_id} onChange={(event) => setForm({ ...form, project_id: event.target.value })}>
              {projects.map((project) => <option key={project.project_id} value={project.project_id}>{project.name}</option>)}
            </select>
          </label>
          <label>素材名称<input value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} /></label>
          <label>素材类型<input value={form.asset_type} onChange={(event) => setForm({ ...form, asset_type: event.target.value })} /></label>
          <label>Object Key<input value={form.object_key} onChange={(event) => setForm({ ...form, object_key: event.target.value })} /></label>
          <label>预览 URL<input value={form.preview_url} onChange={(event) => setForm({ ...form, preview_url: event.target.value })} /></label>
          <label>Tags<textarea value={form.tags} onChange={(event) => setForm({ ...form, tags: event.target.value })} /></label>
        </div>
        <button onClick={handleCreate} disabled={busy || !form.project_id}>{busy ? '保存中...' : '保存 Asset'}</button>
      </article>
      {assets.map((asset) => (
        <article key={asset.asset_id} className="card">
          <p className="eyebrow">{asset.asset_type} · {asset.version}</p>
          <h2>{asset.name}</h2>
          <dl>
            <div><dt>UUID</dt><dd>{asset.uuid}</dd></div>
            <div><dt>Object</dt><dd>{asset.object_key || asset.source_uri || '-'}</dd></div>
            <div><dt>状态</dt><dd>{asset.status}</dd></div>
            <div><dt>已转组件</dt><dd>{asset.converted_component_ids.length}</dd></div>
          </dl>
          <div className="tag-list">{asset.tags.map((tag) => <span key={tag} className="tag">{tag}</span>)}</div>
        </article>
      ))}
    </section>
  );
}
