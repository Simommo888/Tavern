import type { AnalyticsOverview } from '@/types/workbench';

function percent(value: number) {
  return `${(value * 100).toFixed(1)}%`;
}

function money(value: number) {
  return `¥${value.toLocaleString('zh-CN')}`;
}

export default function AnalyticsCenter({ overview }: { overview: AnalyticsOverview }) {
  return (
    <section className="grid">
      <article className="card wide">
        <div className="card-row">
          <div>
            <p className="eyebrow">Top Ranking</p>
            <h2>直播场次综合排行</h2>
          </div>
          <small>按 GMV + CTR + CVR 排序</small>
        </div>
        <div className="ranking-table">
          {overview.top_ranking.map((item) => (
            <article key={item.metric_id} className="ranking-row">
              <strong>#{item.rank}</strong>
              <div>
                <p>{item.session_id}</p>
                <small>{item.component_ids.length} components · {item.prompt_versions.length} prompts · avatar {item.avatar_id || '-'}</small>
              </div>
              <span>{money(item.gmv)}</span>
              <span>CTR {percent(item.ctr)}</span>
              <span>CVR {percent(item.cvr)}</span>
              <span>Score {item.score}</span>
            </article>
          ))}
        </div>
      </article>

      <article className="card">
        <div className="card-row">
          <div>
            <p className="eyebrow">Component Ranking</p>
            <h2>组件表现排行</h2>
          </div>
        </div>
        <div className="timeline">
          {overview.component_ranking.map((component) => (
            <article key={component.component_id} className="reply">
              <span>#{component.rank} · {component.component_code} · {component.component_type}</span>
              <p>{component.name}</p>
              <small>{money(component.gmv)} · CTR {percent(component.ctr)} · CVR {percent(component.cvr)} · Used {component.usage_count}</small>
            </article>
          ))}
        </div>
      </article>

      <article className="card">
        <div className="card-row">
          <div>
            <p className="eyebrow">Prompt Ranking</p>
            <h2>Prompt 表现排行</h2>
          </div>
        </div>
        <div className="timeline">
          {overview.prompt_ranking.map((prompt) => (
            <article key={prompt.prompt_version_id} className="reply">
              <span>#{prompt.rank} · {prompt.purpose} · {prompt.version}</span>
              <p>{prompt.name}</p>
              <small>{money(prompt.gmv)} · CTR {percent(prompt.ctr)} · CVR {percent(prompt.cvr)} · Use {prompt.use_count} · Cost ${prompt.cost_estimate.toFixed(1)}</small>
            </article>
          ))}
        </div>
      </article>

      <article className="card">
        <div className="card-row">
          <div>
            <p className="eyebrow">Avatar Ranking</p>
            <h2>数字人表现排行</h2>
          </div>
        </div>
        <div className="timeline">
          {overview.avatar_ranking.map((avatar) => (
            <article key={avatar.avatar_id} className="reply">
              <span>#{avatar.rank} · {avatar.provider} · {avatar.status}</span>
              <p>{avatar.name}</p>
              <small>{money(avatar.gmv)} · CTR {percent(avatar.ctr)} · CVR {percent(avatar.cvr)} · Sessions {avatar.session_count} · Voice {avatar.voice_name || '-'}</small>
            </article>
          ))}
        </div>
      </article>

      <article className="card">
        <div className="card-row">
          <div>
            <p className="eyebrow">Best Practice</p>
            <h2>最佳实践沉淀</h2>
          </div>
        </div>
        <div className="timeline">
          {overview.best_practice_ranking.map((practice) => (
            <article key={practice.best_practice_id} className="reply">
              <span>#{practice.rank} · {practice.query_label} · Score {practice.score}</span>
              <p>{practice.title}</p>
              <small>{practice.reason}</small>
            </article>
          ))}
        </div>
      </article>
    </section>
  );
}
