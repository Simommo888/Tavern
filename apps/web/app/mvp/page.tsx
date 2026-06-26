import WorkbenchShell from '@/components/live/WorkbenchShell';
import MvpLivePlanRunner from '@/components/live/MvpLivePlanRunner';
import PageHero from '@/components/ui/PageHero';
import { listAvatars, listMvpLivePlans, listProducts, listProjects } from '@/lib/api/workbench';

export default async function MvpPage() {
  const [projects, products, avatars, plans] = await Promise.all([
    listProjects(),
    listProducts(),
    listAvatars(),
    listMvpLivePlans(),
  ]);

  return (
    <WorkbenchShell>
      <div className="page">
        <PageHero
          eyebrow="Phase 9 / MVP"
          title="上传商品到保存直播方案的最小闭环"
          description="本阶段只打通 MVP：上传商品→品牌分析→剧本→数字人口播→数字人→直播视频→保存方案。数字人、TTS、视频合成都通过现有 Plugin / Wrapper / Job 能力编排，不重复造轮子。"
          action={<button>Product → Saved Live Plan</button>}
        />
        <MvpLivePlanRunner projects={projects} products={products} avatars={avatars} initialPlans={plans} />
      </div>
    </WorkbenchShell>
  );
}
