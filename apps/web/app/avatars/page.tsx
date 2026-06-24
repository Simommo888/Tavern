import WorkbenchShell from '@/components/live/WorkbenchShell';
import AvatarCenter from '@/components/live/AvatarCenter';
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
        <AvatarCenter initialAvatars={avatars} />
      </div>
    </WorkbenchShell>
  );
}
