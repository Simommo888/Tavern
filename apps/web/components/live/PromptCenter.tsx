'use client';

import { useMemo, useState } from 'react';
import { createPromptTemplate, renderPromptTemplate } from '@/lib/api/workbench';
import type { PromptTemplate, PromptVersion } from '@/types/workbench';

export default function PromptCenter({ initialPrompts, initialVersions }: { initialPrompts: PromptTemplate[]; initialVersions: PromptVersion[] }) {
  const [prompts, setPrompts] = useState(initialPrompts);
  const [versions] = useState(initialVersions);
  const [selectedName, setSelectedName] = useState(initialPrompts[0]?.name ?? '');
  const [messages, setMessages] = useState<{ role: string; content: string }[]>([]);
  const [form, setForm] = useState({
    name: 'storyboard_generate',
    system: '你是直播电商分镜导演，负责把脚本转成可执行镜头语言。',
    user_instruction: '基于 {product} 和 {script} 输出 5 个直播分镜，每个分镜包含画面、字幕、数字人动作和组件。',
    max_output_seconds: '30',
  });
  const [payloadText, setPayloadText] = useState('{"product":"可雅白兰地礼盒","script":"开场讲品并引导理性下单"}');
  const [busy, setBusy] = useState('');

  const selectedPrompt = useMemo(() => prompts.find((prompt) => prompt.name === selectedName) ?? prompts[0], [prompts, selectedName]);
  const selectedVersion = selectedPrompt ? versions.find((version) => version.prompt_id === selectedPrompt.prompt_id || version.name === selectedPrompt.name) : undefined;

  async function handleCreate() {
    setBusy('create');
    try {
      const prompt = await createPromptTemplate({
        name: form.name,
        system: form.system,
        user_instruction: form.user_instruction,
        max_output_seconds: Number(form.max_output_seconds) || null,
      });
      setPrompts((items) => [prompt, ...items.filter((item) => item.name !== prompt.name)]);
      setSelectedName(prompt.name);
    } finally {
      setBusy('');
    }
  }

  async function handleRender() {
    if (!selectedPrompt) return;
    setBusy('render');
    try {
      const payload = JSON.parse(payloadText || '{}') as Record<string, unknown>;
      setMessages(await renderPromptTemplate(selectedPrompt.name, payload));
    } finally {
      setBusy('');
    }
  }

  return (
    <section className="grid">
      <article className="card wide">
        <h2>新建 Prompt 模板</h2>
        <div className="grid">
          <label>模板名称<input value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} /></label>
          <label>口播秒数<input value={form.max_output_seconds} onChange={(event) => setForm({ ...form, max_output_seconds: event.target.value })} /></label>
        </div>
        <label>System<textarea value={form.system} onChange={(event) => setForm({ ...form, system: event.target.value })} /></label>
        <label>User Instruction<textarea value={form.user_instruction} onChange={(event) => setForm({ ...form, user_instruction: event.target.value })} /></label>
        <button onClick={handleCreate} disabled={busy === 'create'}>{busy === 'create' ? '保存中...' : '保存 Prompt'}</button>
      </article>

      <article className="card">
        <h2>模板列表</h2>
        <div className="timeline">
          {prompts.map((prompt) => (
            <article key={`${prompt.prompt_id}-${prompt.name}`} className="reply" onClick={() => setSelectedName(prompt.name)}>
              <span>{prompt.purpose} · {prompt.version}</span>
              <p>{prompt.name}</p>
              <small>{prompt.variables.length ? `Variables: ${prompt.variables.join('、')}` : 'No variables'}</small>
            </article>
          ))}
        </div>
      </article>

      <article className="card">
        <h2>渲染检查</h2>
        <label>选择模板
          <select value={selectedPrompt?.name ?? ''} onChange={(event) => setSelectedName(event.target.value)}>
            {prompts.map((prompt) => <option key={prompt.name} value={prompt.name}>{prompt.name}</option>)}
          </select>
        </label>
        <label>Prompt Payload<textarea value={payloadText} onChange={(event) => setPayloadText(event.target.value)} /></label>
        <button onClick={handleRender} disabled={!selectedPrompt || busy === 'render'}>{busy === 'render' ? '渲染中...' : '渲染 Prompt'}</button>
        {selectedVersion && <small>历史表现：Score {selectedVersion.score} · Use {selectedVersion.use_count} · GMV ¥{selectedVersion.gmv.toLocaleString('zh-CN')}</small>}
      </article>

      {messages.length > 0 && (
        <article className="card wide">
          <h2>Rendered Messages</h2>
          <pre>{JSON.stringify(messages, null, 2)}</pre>
        </article>
      )}
    </section>
  );
}
