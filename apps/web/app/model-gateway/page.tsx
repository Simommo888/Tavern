import WorkbenchShell from '@/components/live/WorkbenchShell';
import PageHero from '@/components/ui/PageHero';
import StatusBadge from '@/components/ui/StatusBadge';
import { listModelProviders, listPluginProviders, listPromptTemplates } from '@/lib/api/workbench';

export default async function ModelGatewayPage() {
  const [providers, prompts, plugins] = await Promise.all([listModelProviders(), listPromptTemplates(), listPluginProviders()]);
  return (
    <WorkbenchShell>
      <div className="page">
        <PageHero
          eyebrow="Model & Plugin Manager"
          title="统一模型网关与插件 Provider"
          description="LLM、TTS、数字人、视频合成、推流和工作流全部通过 Provider Adapter 接入，今天用 Fish Speech，明天换 ElevenLabs，不改业务链路。"
          action={<button>添加 Provider</button>}
        />
        <section className="grid three">
          {providers.map((provider) => (
            <article key={provider.provider_id} className="card">
              <div className="card-row">
                <h2>{provider.display_name}</h2>
                <StatusBadge status={provider.configured ? 'ready' : 'queued'} />
              </div>
              <dl>
                <div><dt>Provider</dt><dd>{provider.name}</dd></div>
                <div><dt>Chat</dt><dd>{provider.chat_model || '-'}</dd></div>
                <div><dt>Embedding</dt><dd>{provider.embedding_model || '-'}</dd></div>
                <div><dt>Streaming</dt><dd>{provider.streaming_supported ? '支持' : '不支持'}</dd></div>
              </dl>
            </article>
          ))}
        </section>
        <section className="grid" style={{ marginTop: 20 }}>
          <article className="card">
            <h2>插件 Provider Registry</h2>
            <div className="timeline">
              {plugins.map((plugin) => (
                <article key={plugin.plugin_id} className="reply">
                  <span>{plugin.category} · {plugin.source_type}</span>
                  <p>{plugin.display_name}</p>
                  <small>{plugin.provider_id} · {plugin.health_status} · {plugin.capabilities.join(' / ')}</small>
                </article>
              ))}
            </div>
          </article>
          <article className="card">
            <h2>Prompt 管理</h2>
            <div className="timeline">
              {prompts.map((prompt) => (
                <article key={prompt.prompt_id} className="reply">
                  <span>{prompt.purpose} · {prompt.version}</span>
                  <p>{prompt.name}</p>
                  <small>{prompt.content}</small>
                </article>
              ))}
            </div>
          </article>
        </section>
      </div>
    </WorkbenchShell>
  );
}
