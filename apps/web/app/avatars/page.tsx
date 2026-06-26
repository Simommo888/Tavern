import WorkbenchShell from '@/components/live/WorkbenchShell';
import AvatarCenter from '@/components/live/AvatarCenter';
import PageHero from '@/components/ui/PageHero';
import { listAvatars } from '@/lib/api/workbench';

export default async function AvatarsPage() {
  const avatars = await listAvatars();
  return (
    <WorkbenchShell>
      <div className="page">
        <PageHero
          eyebrow="Avatar Department"
          title="数字人员工与声音配置"
          description="数字人是可替换 Provider 能力：HeyGen、LiveTalking、MuseTalk、SadTalker 都通过统一 Avatar Provider 接入。"
          action={<button>创建数字人</button>}
        />
        <AvatarCenter initialAvatars={avatars} />
      </div>
    </WorkbenchShell>
  );
}
