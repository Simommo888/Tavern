'use client';

import { useState } from 'react';
import { createAvatar, createAvatarJob } from '@/lib/api/workbench';
import type { AvatarProfile } from '@/types/workbench';

export default function AvatarCenter({ initialAvatars }: { initialAvatars: AvatarProfile[] }) {
  const [avatars, setAvatars] = useState(initialAvatars);
  const [form, setForm] = useState({ name: '张裕品牌数字人主播', heygen_avatar_id: '', heygen_voice_id: '', voice_name: '中文女声' });
  const [jobStatus, setJobStatus] = useState('');

  async function handleCreate() {
    const avatar = await createAvatar({ ...form, provider: 'heygen', status: 'ready', source_material_urls: [] });
    setAvatars((items) => [avatar, ...items]);
  }

  async function handleJob(avatar: AvatarProfile) {
    const job = await createAvatarJob(avatar.avatar_id, '欢迎来到酒类数字人直播间，今天给大家介绍适合成年人送礼和宴请的产品。');
    setJobStatus(`${avatar.name}: ${job.status} ${job.output_url}`);
  }

  return (
    <section className="grid">
      <article className="card wide">
        <h2>创建数字人</h2>
        <div className="grid">
          <label>名称<input value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} /></label>
          <label>HeyGen Avatar ID<input value={form.heygen_avatar_id} onChange={(event) => setForm({ ...form, heygen_avatar_id: event.target.value })} /></label>
          <label>HeyGen Voice ID<input value={form.heygen_voice_id} onChange={(event) => setForm({ ...form, heygen_voice_id: event.target.value })} /></label>
          <label>声音名称<input value={form.voice_name} onChange={(event) => setForm({ ...form, voice_name: event.target.value })} /></label>
        </div>
        <button onClick={handleCreate}>保存数字人</button>
        {jobStatus && <p>{jobStatus}</p>}
      </article>
      {avatars.map((avatar) => (
        <article key={avatar.avatar_id} className="card">
          <h2>{avatar.name}</h2>
          <dl>
            <dt>Provider</dt><dd>{avatar.provider}</dd>
            <dt>Avatar</dt><dd>{avatar.heygen_avatar_id || '未绑定'}</dd>
            <dt>Voice</dt><dd>{avatar.heygen_voice_id || '未绑定'}</dd>
            <dt>声音</dt><dd>{avatar.voice_name || '未配置'}</dd>
            <dt>状态</dt><dd>{avatar.status}</dd>
          </dl>
          <button onClick={() => handleJob(avatar)}>发起文本驱动任务</button>
        </article>
      ))}
    </section>
  );
}
