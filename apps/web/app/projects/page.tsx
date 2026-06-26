import Link from 'next/link';
import WorkbenchShell from '@/components/live/WorkbenchShell';
import PageHero from '@/components/ui/PageHero';
import StatusBadge from '@/components/ui/StatusBadge';
import { listAssets, listComponents, listLiveRoomCompositions, listProjects, listWorkflowRuns } from '@/lib/api/workbench';

export default async function ProjectsPage() {
  const [projects, assets, components, rooms, runs] = await Promise.all([
    listProjects(),
    listAssets(),
    listComponents(),
    listLiveRoomCompositions(),
    listWorkflowRuns(),
  ]);
  return (
    <WorkbenchShell>
      <div className="page">
        <PageHero
          eyebrow="Project Center"
          title="所有直播资产都归属于 Project"
          description="品牌、商品、素材、组件、剧本、直播间、视频和历史效果统一沉淀到项目中，避免传统后台式分散管理。"
          action={<button>新建 Project</button>}
        />
        <section className="grid">
          {projects.map((project) => {
            const projectAssets = assets.filter((asset) => asset.project_id === project.project_id);
            const projectComponents = components.filter((component) => component.project_id === project.project_id);
            const projectRooms = rooms.filter((room) => room.project_id === project.project_id);
            const projectRuns = runs.filter((run) => run.project_id === project.project_id);
            return (
              <article key={project.project_id} className="card wide">
                <div className="card-row">
                  <div>
                    <p className="eyebrow">{project.brand_name || project.industry}</p>
                    <h2>{project.name}</h2>
                    <p>{project.objective}</p>
                  </div>
                  <StatusBadge status={project.status} />
                </div>
                <div className="metrics">
                  <article className="card metric"><span>Assets</span><strong>{projectAssets.length}</strong></article>
                  <article className="card metric"><span>Components</span><strong>{projectComponents.length}</strong></article>
                  <article className="card metric"><span>Live Rooms</span><strong>{projectRooms.length}</strong></article>
                  <article className="card metric"><span>Workflow Runs</span><strong>{projectRuns.length}</strong></article>
                </div>
                <div className="tag-list">{project.tags.map((tag) => <span key={tag} className="tag">{tag}</span>)}</div>
                <div className="quick">
                  <Link href="/studio"><button>进入 Studio</button></Link>
                  <Link href="/workflow"><button className="ghost-button">查看 Workflow</button></Link>
                  <Link href="/analytics"><button className="ghost-button">复盘经验</button></Link>
                </div>
              </article>
            );
          })}
        </section>
      </div>
    </WorkbenchShell>
  );
}
