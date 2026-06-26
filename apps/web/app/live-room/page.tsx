import Link from 'next/link';
import WorkbenchShell from '@/components/live/WorkbenchShell';
import MetricGrid from '@/components/ui/MetricGrid';
import PageHero from '@/components/ui/PageHero';
import StatusBadge from '@/components/ui/StatusBadge';
import { listAssets, listComponents, listLiveRoomCompositions, listLiveScenes } from '@/lib/api/workbench';

const componentTypes = ['Background', 'Desk', 'Avatar', 'Logo', 'Product', 'Subtitle', 'Sticker', 'POP', 'Camera', 'Transition'];

export default async function LiveRoomBuilderPage() {
  const [assets, components, scenes, compositions] = await Promise.all([listAssets(), listComponents(), listLiveScenes(), listLiveRoomCompositions()]);
  const active = compositions[0];
  const activeScenes = active?.scene_snapshot.length ? active.scene_snapshot : scenes;
  return (
    <WorkbenchShell>
      <div className="page">
        <PageHero
          eyebrow="Live Room Builder"
          title="Asset → Component → Scene → LiveRoom"
          description="Phase 6 将直播间拆成可追踪层级：素材入库，生成组件；组件组合成场景；一个或多个场景组成直播间。所有层级都有 UUID、Version、Metadata、Tags。"
          action={<Link href="/live-rooms/demo"><button>进入实时总控</button></Link>}
        />
        <MetricGrid metrics={[
          { label: 'Asset', value: assets.length, hint: '原始素材' },
          { label: 'Component', value: components.length, hint: '可复用积木' },
          { label: 'Scene', value: scenes.length, hint: '组件组合' },
          { label: 'LiveRoom', value: compositions.length, hint: '直播间方案' },
        ]} />
        <section className="component-chain card wide">
          {['Asset', 'Component', 'Scene', 'LiveRoom'].map((item) => <span key={item}>{item}</span>)}
        </section>
        <section className="grid" style={{ gridTemplateColumns: '0.75fr 1.35fr 0.9fr' }}>
          <article className="card">
            <h2>组件类型</h2>
            <div className="timeline">
              {componentTypes.map((type) => (
                <article key={type} className="reply">
                  <span>{components.filter((component) => component.component_type === type).length} components</span>
                  <p>{type}</p>
                </article>
              ))}
            </div>
          </article>

          <article className="canvas-preview">
            <div className="pop">限时权益 POP</div>
            <div className="avatar">酒</div>
            <div className="subtitle">{active?.name ?? 'AI 数字人直播间组合预览'}</div>
          </article>

          <article className="card">
            <div className="card-row">
              <div>
                <p className="eyebrow">{active?.version ?? 'v1'}</p>
                <h2>当前 LiveRoom</h2>
              </div>
              {active && <StatusBadge status={active.status} />}
            </div>
            <dl>
              <div><dt>UUID</dt><dd>{active?.uuid ?? '-'}</dd></div>
              <div><dt>ID</dt><dd>{active?.composition_id ?? '-'}</dd></div>
              <div><dt>Scene</dt><dd>{active?.scene_ids.length ?? 0}</dd></div>
              <div><dt>Component</dt><dd>{active?.component_snapshot.length ?? 0}</dd></div>
              <div><dt>Metadata</dt><dd>{active ? Object.keys(active.metadata).join('、') : '-'}</dd></div>
            </dl>
            <div className="tag-list">{(active?.tags ?? []).map((tag) => <span key={tag} className="tag">{tag}</span>)}</div>
          </article>
        </section>

        <section className="grid">
          {activeScenes.map((scene) => (
            <article key={scene.scene_id} className="card wide">
              <div className="card-row">
                <div>
                  <p className="eyebrow">Scene · {scene.version}</p>
                  <h2>{scene.name}</h2>
                </div>
                <StatusBadge status={scene.status} />
              </div>
              <dl className="plain workflow-run-meta">
                <div><dt>UUID</dt><dd>{scene.uuid}</dd></div>
                <div><dt>类型</dt><dd>{scene.scene_type}</dd></div>
                <div><dt>组件</dt><dd>{scene.component_ids.length}</dd></div>
                <div><dt>布局</dt><dd>{String(scene.layout.canvas ?? '-')}</dd></div>
                <div><dt>Metadata</dt><dd>{Object.keys(scene.metadata).join('、') || '-'}</dd></div>
              </dl>
              <div className="grid four">
                {scene.component_snapshot.map((component) => (
                  <article key={component.component_id} className="reply">
                    <span>{component.component_code} · {component.current_version}</span>
                    <p>{component.name}</p>
                    <small>{component.component_type} · source assets {component.source_asset_ids.length} · CVR {(component.cvr * 100).toFixed(1)}%</small>
                  </article>
                ))}
              </div>
            </article>
          ))}
        </section>
      </div>
    </WorkbenchShell>
  );
}
