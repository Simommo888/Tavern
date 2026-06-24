import WorkbenchShell from '@/components/live/WorkbenchShell';
import { listModelProviders, listPromptTemplates } from '@/lib/api/workbench';

export default async function ModelGatewayPage() {
  const providers = await listModelProviders();
  const prompts = await listPromptTemplates();
  return (
    <WorkbenchShell>
      <div className="page">
        <header className="hero">
          <div>
            <p className="eyebrow">Model Gateway</p>
            <h1>统一模型网关</h1>
            <p>统一管理 Gemini、Claude、GPT 与 OpenAI-compatible 模型，支持模型切换、流式输出和 Prompt 版本管理。</p>
          </div>
        </header>
        <section className="grid">
          {providers.map((provider) => (
            <article key={provider.provider_id} className="card">
              <h2>{provider.display_name}</h2>
              <dl>
                <dt>Provider</dt><dd>{provider.name}</dd>
                <dt>Chat</dt><dd>{provider.chat_model || '-'}</dd>
                <dt>Embedding</dt><dd>{provider.embedding_model || '-'}</dd>
                <dt>Streaming</dt><dd>{provider.streaming_supported ? '支持' : '不支持'}</dd>
                <dt>配置</dt><dd>{provider.configured ? '已配置' : '待配置'}</dd>
              </dl>
            </article>
          ))}
          <article className="card wide">
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
