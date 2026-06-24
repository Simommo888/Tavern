'use client';

import { useState } from 'react';
import { createWorkflowRule, updateWorkflowRule } from '@/lib/api/workbench';
import type { WorkflowRule } from '@/types/workbench';

export default function WorkflowCenter({ initialRules }: { initialRules: WorkflowRule[] }) {
  const [rules, setRules] = useState(initialRules);
  const [form, setForm] = useState({ name: '用户关注后促单', event_type: 'user_follow', action_type: 'sales_push', delay_seconds: '5' });

  async function handleCreate() {
    const rule = await createWorkflowRule({ ...form, delay_seconds: Number(form.delay_seconds), enabled: true });
    setRules((items) => [rule, ...items]);
  }

  async function toggle(rule: WorkflowRule) {
    const next = await updateWorkflowRule(rule.rule_id, { enabled: !rule.enabled });
    setRules((items) => items.map((item) => item.rule_id === next.rule_id ? next : item));
  }

  return (
    <section className="grid">
      <article className="card wide">
        <h2>新增事件规则</h2>
        <div className="grid">
          <label>规则名称<input value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} /></label>
          <label>事件类型<input value={form.event_type} onChange={(event) => setForm({ ...form, event_type: event.target.value })} /></label>
          <label>动作类型<input value={form.action_type} onChange={(event) => setForm({ ...form, action_type: event.target.value })} /></label>
          <label>延迟秒数<input value={form.delay_seconds} onChange={(event) => setForm({ ...form, delay_seconds: event.target.value })} /></label>
        </div>
        <button onClick={handleCreate}>保存规则</button>
      </article>
      {rules.map((rule) => (
        <article key={rule.rule_id} className="card">
          <h2>{rule.name}</h2>
          <dl>
            <dt>事件</dt><dd>{rule.event_type}</dd>
            <dt>动作</dt><dd>{rule.action_type}</dd>
            <dt>延迟</dt><dd>{rule.delay_seconds} 秒</dd>
            <dt>状态</dt><dd>{rule.enabled ? '启用' : '停用'}</dd>
          </dl>
          <button onClick={() => toggle(rule)}>{rule.enabled ? '停用' : '启用'}</button>
        </article>
      ))}
    </section>
  );
}
