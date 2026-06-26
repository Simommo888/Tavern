'use client';

import { useState } from 'react';
import { runMvpLivePlan } from '@/lib/api/workbench';
import type { AvatarProfile, MvpLivePlan, ProductRecord, Project } from '@/types/workbench';

const stepOrder = ['上传商品', '品牌分析', '剧本', '数字人口播', '数字人', '直播视频', '保存方案'];

export default function MvpLivePlanRunner({ projects, products, avatars, initialPlans }: { projects: Project[]; products: ProductRecord[]; avatars: AvatarProfile[]; initialPlans: MvpLivePlan[] }) {
  const [plans, setPlans] = useState(initialPlans);
  const [busy, setBusy] = useState(false);
  const [form, setForm] = useState({
    project_id: projects[0]?.project_id ?? '',
    product_id: products[0]?.product_id ?? '',
    avatar_id: avatars[0]?.avatar_id ?? '',
    brand_name: projects[0]?.brand_name || '张裕 / 可雅',
    script_note: '突出礼盒送礼、直播间权益和酒类合规提醒。',
  });

  async function handleRun() {
    setBusy(true);
    try {
      const plan = await runMvpLivePlan({
        project_id: form.project_id || undefined,
        product_id: form.product_id || undefined,
        avatar_id: form.avatar_id || undefined,
        brand_name: form.brand_name,
        script_note: form.script_note,
      });
      setPlans((items) => [plan, ...items.filter((item) => item.plan_id !== plan.plan_id)]);
    } finally {
      setBusy(false);
    }
  }

  const latestPlan = plans[0];

  return (
    <section className="grid">
      <article className="card wide">
        <div className="card-row">
          <div>
            <h2>一键打通 MVP</h2>
            <p>复用现有 Product、Agent、Plugin、Component、Workflow 能力，不新造视频/数字人引擎。</p>
          </div>
          <button onClick={handleRun} disabled={busy || (!form.product_id && products.length > 0)}>{busy ? '运行中...' : '运行 Phase 9 MVP'}</button>
        </div>
        <div className="grid three">
          <label>Project
            <select value={form.project_id} onChange={(event) => setForm({ ...form, project_id: event.target.value })}>
              {projects.map((project) => <option key={project.project_id} value={project.project_id}>{project.name}</option>)}
            </select>
          </label>
          <label>商品
            <select value={form.product_id} onChange={(event) => setForm({ ...form, product_id: event.target.value })}>
              {products.map((product) => <option key={product.product_id} value={product.product_id}>{product.product_name}</option>)}
            </select>
          </label>
          <label>数字人
            <select value={form.avatar_id} onChange={(event) => setForm({ ...form, avatar_id: event.target.value })}>
              {avatars.map((avatar) => <option key={avatar.avatar_id} value={avatar.avatar_id}>{avatar.name}</option>)}
            </select>
          </label>
        </div>
        <div className="grid">
          <label>品牌名称<input value={form.brand_name} onChange={(event) => setForm({ ...form, brand_name: event.target.value })} /></label>
          <label>剧本提示<textarea value={form.script_note} onChange={(event) => setForm({ ...form, script_note: event.target.value })} /></label>
        </div>
      </article>

      <article className="card wide">
        <h2>Phase 9 主链路</h2>
        <div className="workflow-strip">
          {stepOrder.map((step, index) => <span key={step}>{index + 1}. {step}</span>)}
        </div>
        {latestPlan ? (
          <div className="mvp-plan-grid">
            {latestPlan.steps.map((step) => (
              <article key={String(step.id)} className="reply">
                <span>{String(step.label)} · {String(step.status)}</span>
                <p>{String(step.summary)}</p>
                <small>{String(step.artifact_uri || '')}</small>
              </article>
            ))}
          </div>
        ) : <p>暂无保存方案，点击上方按钮生成第一条 MVP 方案。</p>}
      </article>

      {latestPlan && (
        <>
          <article className="card">
            <p className="eyebrow">Brand Analysis</p>
            <h2>{String(latestPlan.brand_analysis.brand_name ?? '品牌分析')}</h2>
            <p>{String(latestPlan.brand_analysis.positioning ?? '')}</p>
            <div className="tag-list">
              {((latestPlan.brand_analysis.trust_points as string[] | undefined) ?? []).map((tag) => <span key={tag} className="tag">{tag}</span>)}
            </div>
          </article>
          <article className="card">
            <p className="eyebrow">Digital Human Script</p>
            <h2>{String(latestPlan.script_snapshot.name ?? '数字人口播')}</h2>
            <p>{String(latestPlan.script_snapshot.content ?? '').slice(0, 220)}...</p>
          </article>
          <article className="card">
            <p className="eyebrow">Saved Outputs</p>
            <h2>直播方案已保存</h2>
            <dl>
              <div><dt>Plan</dt><dd>{latestPlan.plan_id}</dd></div>
              <div><dt>Workflow</dt><dd>{latestPlan.workflow_run_id}</dd></div>
              <div><dt>Speech</dt><dd>{latestPlan.speech_artifact_uri}</dd></div>
              <div><dt>Avatar</dt><dd>{latestPlan.avatar_video_uri}</dd></div>
              <div><dt>Video</dt><dd>{latestPlan.live_video_uri}</dd></div>
            </dl>
          </article>
          <article className="card">
            <p className="eyebrow">Reuse Contract</p>
            <h2>能复用就复用</h2>
            <p>当前方案只编排既有 Workbench、Plugin Manager、Avatar Job、LiveRoom Composition 和 FFmpeg/MoviePy Wrapper。</p>
            <small>{String(latestPlan.saved_outputs.plan_uri ?? '')}</small>
          </article>
        </>
      )}
    </section>
  );
}
