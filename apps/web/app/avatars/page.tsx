import WorkbenchShell from '@/components/live/WorkbenchShell';
import { listAvatars } from '@/lib/api/workbench';

export default async function AvatarsPage() {
  const avatars = await listAvatars();
  return (
    <WorkbenchShell>
      <div className="page">
        <header className="hero">
          <div>
            <p className="eyebrow">Avatar Service</p>
            <h1>数字人管理</h1>
            <p>创建数字人、维护真人素材、绑定 HeyGen Avatar 和配置声音。</p>
          </div>
          <button>创建数字人</button>
        </header>
        <section className="grid">
          {avatars.map((avatar) => (
            <article key={avatar.avatar_id} className="card">
              <h2>{avatar.name}</h2>
              <dl>
                <dt>Provider</dt><dd>{avatar.provider}</dd>
                <dt>HeyGen Avatar</dt><dd>{avatar.heygen_avatar_id || '未绑定'}</dd>
                <dt>HeyGen Voice</dt><dd>{avatar.heygen_voice_id || '未绑定'}</dd>
                <dt>声音</dt><dd>{avatar.voice_name || '未配置'}</dd>
                <dt>状态</dt><dd>{avatar.status}</dd>
              </dl>
              <p>素材数量：{avatar.source_material_urls.length}</p>
            </article>
          ))}
        </section>
      </div>
    </WorkbenchShell>
  );
}
