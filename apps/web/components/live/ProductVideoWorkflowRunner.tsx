'use client';

import { useMemo, useState } from 'react';
import { createProductVideoWorkflowRun, runProductVideoWorkflowNode, runProductVideoWorkflow } from '@/lib/api/workbench';
import type { ProductRecord, ProductVideoWorkflowSnapshot, Project, WorkflowNodeRun } from '@/types/workbench';
import ProgressBar from '@/components/ui/ProgressBar';
import StatusBadge from '@/components/ui/StatusBadge';

const defaultNodeOrder = ['product_brand_input', 'planner', 'story', 'script', 'director', 'visual_director', 'asset', 'image', 'video', 'editor'];

function outputText(node?: WorkflowNodeRun): string {
  if (!node) return '等待执行';
  const payload = node.output_payload?.data ?? {};
  return JSON.stringify(payload, null, 2).slice(0, 1200);
}

function artifactUri(node?: WorkflowNodeRun): string {
  return String(node?.output_payload?.artifact_uri ?? '');
}

export default function ProductVideoWorkflowRunner({ projects, products, initialSnapshot, n8nImportPath, n8nUrl }: { projects: Project[]; products: ProductRecord[]; initialSnapshot?: ProductVideoWorkflowSnapshot | null; n8nImportPath: string; n8nUrl: string }) {
  const [snapshot, setSnapshot] = useState<ProductVideoWorkflowSnapshot | null>(initialSnapshot ?? null);
  const [busyNode, setBusyNode] = useState('');
  const [form, setForm] = useState({
    project_id: projects[0]?.project_id ?? '',
    product_id: products[0]?.product_id ?? '',
    brand_name: projects[0]?.brand_name || '龙八',
    duration_seconds: 45,
    bgm_style: 'premium light corporate',
  });

  const nodeOrder = useMemo(() => snapshot?.definition.nodes.map((node) => node.id) ?? defaultNodeOrder, [snapshot]);
  const completedCount = snapshot?.nodes.filter((node) => node.status === 'succeeded').length ?? 0;
  const nextNode = snapshot?.nodes.find((node) => node.status !== 'succeeded');
  const finalVideoUri = String(snapshot?.final_video?.uri ?? snapshot?.run.output_payload?.final_video ?? '');

  async function startRun() {
    setBusyNode('start');
    try {
      const result = await createProductVideoWorkflowRun({
        project_id: form.project_id || undefined,
        product_id: form.product_id || undefined,
        brand_name: form.brand_name,
        duration_seconds: form.duration_seconds,
        bgm_style: form.bgm_style,
      });
      setSnapshot(result);
    } finally {
      setBusyNode('');
    }
  }

  async function runNode(nodeId: string) {
    if (!snapshot) return;
    setBusyNode(nodeId);
    try {
      const result = await runProductVideoWorkflowNode(snapshot.run.workflow_run_id, nodeId);
      setSnapshot(result);
    } finally {
      setBusyNode('');
    }
  }

  async function runRemaining() {
    if (!snapshot) {
      setBusyNode('all');
      try {
        const result = await runProductVideoWorkflow({
          project_id: form.project_id || undefined,
          product_id: form.product_id || undefined,
          brand_name: form.brand_name,
          duration_seconds: form.duration_seconds,
          bgm_style: form.bgm_style,
        });
        setSnapshot(result);
      } finally {
        setBusyNode('');
      }
      return;
    }
    setBusyNode('all');
    try {
      let current = snapshot;
      for (const nodeId of nodeOrder) {
        const node = current.nodes.find((item) => item.node_id === nodeId);
        if (node?.status === 'succeeded') continue;
        current = await runProductVideoWorkflowNode(current.run.workflow_run_id, nodeId);
        setSnapshot(current);
      }
    } finally {
      setBusyNode('');
    }
  }

  return (
    <section className="grid">
      <article className="card wide">
        <div className="card-row">
          <div>
            <h2>创建完整视频工作流 Run</h2>
            <p>先创建 WorkflowRun，再逐节点执行；n8n 画布也按同一套 API 调用每个 Agent。</p>
          </div>
          <div className="speech-controls">
            <button onClick={startRun} disabled={!!busyNode}>{busyNode === 'start' ? '创建中...' : '创建 Run'}</button>
            <button className="ghost-button" onClick={runRemaining} disabled={!!busyNode}>{busyNode === 'all' ? '执行中...' : '执行剩余节点'}</button>
          </div>
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
          <label>品牌名称<input value={form.brand_name} onChange={(event) => setForm({ ...form, brand_name: event.target.value })} /></label>
        </div>
        <div className="grid">
          <label>目标时长（秒）<input type="number" min={20} max={180} value={form.duration_seconds} onChange={(event) => setForm({ ...form, duration_seconds: Number(event.target.value) || 45 })} /></label>
          <label>BGM 风格<input value={form.bgm_style} onChange={(event) => setForm({ ...form, bgm_style: event.target.value })} /></label>
        </div>
      </article>

      {snapshot && (
        <article className="card wide">
          <div className="card-row">
            <div>
              <h2>{snapshot.definition.name}</h2>
              <p>{snapshot.definition.description}</p>
            </div>
            <StatusBadge status={snapshot.run.status} />
          </div>
          <ProgressBar value={snapshot.run.progress} />
          <dl className="plain workflow-run-meta">
            <div><dt>Run</dt><dd>{snapshot.run.workflow_run_id}</dd></div>
            <div><dt>当前节点</dt><dd>{snapshot.run.current_node_id}</dd></div>
            <div><dt>已完成</dt><dd>{completedCount}/{snapshot.definition.nodes.length}</dd></div>
            <div><dt>Token</dt><dd>{snapshot.run.token_count.toLocaleString('zh-CN')}</dd></div>
            <div><dt>完整视频</dt><dd>{finalVideoUri || '等待 Editor Agent'}</dd></div>
          </dl>
        </article>
      )}

      <section className="card wide">
        <div className="card-row">
          <div>
            <h2>n8n 导入入口</h2>
            <p>n8n 文件已升级为逐节点 HTTP 调用：创建 run 后，每个 Agent 节点单独执行并返回产物。</p>
          </div>
          <a href={n8nUrl} target="_blank" rel="noreferrer"><button>打开 n8n</button></a>
        </div>
        <dl>
          <div><dt>导入文件</dt><dd>{n8nImportPath}</dd></div>
          <div><dt>n8n 地址</dt><dd>{n8nUrl}</dd></div>
          <div><dt>执行模式</dt><dd>one_http_node_per_agent</dd></div>
        </dl>
      </section>

      {snapshot ? (
        <section className="workflow-board visual-workflow-board wide">
          {snapshot.definition.nodes.map((node, index) => {
            const nodeRun = snapshot.nodes.find((item) => item.node_id === node.id);
            const isNext = nextNode?.node_id === node.id;
            return (
              <article key={node.id} className={`card workflow-node workflow-node-${nodeRun?.status ?? 'queued'}`}>
                <p className="eyebrow">{String(node.stage ?? node.id).toUpperCase()}</p>
                <div className="workflow-node-index">{index}</div>
                <h2>{node.label}</h2>
                <StatusBadge status={nodeRun?.status ?? 'queued'} />
                <p>{node.description}</p>
                <dl>
                  <div><dt>Agent</dt><dd>{node.agent}</dd></div>
                  <div><dt>产物</dt><dd>{node.artifact}</dd></div>
                  <div><dt>Provider</dt><dd>{String((nodeRun?.input_payload?.provider_config as Record<string, unknown> | undefined)?.provider ?? '等待执行')}</dd></div>
                  <div><dt>URI</dt><dd>{artifactUri(nodeRun) || '等待产物'}</dd></div>
                </dl>
                <button onClick={() => runNode(node.id)} disabled={!!busyNode || nodeRun?.status === 'succeeded'}>{busyNode === node.id ? '执行中...' : isNext ? '执行当前节点' : '执行节点'}</button>
                <pre>{outputText(nodeRun)}</pre>
              </article>
            );
          })}
        </section>
      ) : (
        <article className="card wide">
          <h2>等待创建工作流</h2>
          <p>点击“创建 Run”后，这里会展示每个节点的状态、Provider 配置、产物 URI 和输出 JSON。</p>
        </article>
      )}
    </section>
  );
}
