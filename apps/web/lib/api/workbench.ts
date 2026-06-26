import { apiRequest } from '@/lib/api/config';
import type { AgentProfile, AgentRun, AnalyticsOverview, Asset, AvatarProfile, BestPractice, DashboardSummary, KnowledgeChunk, KnowledgeDocument, LiveComponent, LiveRoomComposition, LiveScene, ModelProviderConfig, MvpLivePlan, PlatformEvent, PlatformMetricSnapshot, PluginProvider, ProductRecord, Project, PromptTemplate, PromptVersion, ScriptTemplate, WorkflowDefinition, WorkflowNodeRun, WorkflowRule, WorkflowRun } from '@/types/workbench';

export async function getDashboardSummary(): Promise<DashboardSummary> {
  return apiRequest<DashboardSummary>('/api/v1/dashboard/summary');
}

export async function listProducts(): Promise<ProductRecord[]> {
  const payload = await apiRequest<{ products: ProductRecord[] }>('/api/v1/products');
  return payload.products;
}

export async function createProduct(payload: Partial<ProductRecord>): Promise<ProductRecord> {
  const response = await apiRequest<{ product: ProductRecord }>('/api/v1/products', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  return response.product;
}

export async function publishProduct(productId: string): Promise<ProductRecord> {
  const response = await apiRequest<{ product: ProductRecord }>(`/api/v1/products/${productId}/publish`, { method: 'POST' });
  return response.product;
}

export async function unpublishProduct(productId: string): Promise<ProductRecord> {
  const response = await apiRequest<{ product: ProductRecord }>(`/api/v1/products/${productId}/unpublish`, { method: 'POST' });
  return response.product;
}

export async function listAvatars(): Promise<AvatarProfile[]> {
  const payload = await apiRequest<{ avatars: AvatarProfile[] }>('/api/v1/avatars');
  return payload.avatars;
}

export async function createAvatar(payload: Partial<AvatarProfile>): Promise<AvatarProfile> {
  const response = await apiRequest<{ avatar: AvatarProfile }>('/api/v1/avatars', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  return response.avatar;
}

export async function createAvatarJob(avatarId: string, inputText: string): Promise<{ job_id: string; status: string; output_url: string }> {
  const response = await apiRequest<{ job: { job_id: string; status: string; output_url: string } }>(`/api/v1/avatars/${avatarId}/jobs`, {
    method: 'POST',
    body: JSON.stringify({ input_text: inputText, job_type: 'text_drive' }),
  });
  return response.job;
}

export async function listScriptTemplates(): Promise<ScriptTemplate[]> {
  const payload = await apiRequest<{ templates: ScriptTemplate[] }>('/api/v1/scripts/templates');
  return payload.templates;
}

export async function generateScriptTemplate(category: string, productId = ''): Promise<ScriptTemplate> {
  const payload = await apiRequest<{ template: ScriptTemplate }>('/api/v1/scripts/templates/generate', {
    method: 'POST',
    body: JSON.stringify({ category, product_id: productId }),
  });
  return payload.template;
}

export async function listWorkflowRules(): Promise<WorkflowRule[]> {
  const payload = await apiRequest<{ rules: WorkflowRule[] }>('/api/v1/workflow/rules');
  return payload.rules;
}

export async function createWorkflowRule(payload: Partial<WorkflowRule>): Promise<WorkflowRule> {
  const response = await apiRequest<{ rule: WorkflowRule }>('/api/v1/workflow/rules', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  return response.rule;
}

export async function updateWorkflowRule(ruleId: string, payload: Partial<WorkflowRule>): Promise<WorkflowRule> {
  const response = await apiRequest<{ rule: WorkflowRule }>(`/api/v1/workflow/rules/${ruleId}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  });
  return response.rule;
}

export async function listPlatformMetrics(): Promise<PlatformMetricSnapshot[]> {
  const payload = await apiRequest<{ metrics: PlatformMetricSnapshot[] }>('/api/v1/platform/metrics');
  return payload.metrics;
}

export async function listKnowledgeDocuments(): Promise<KnowledgeDocument[]> {
  const payload = await apiRequest<{ documents: KnowledgeDocument[] }>('/api/v1/knowledge/documents');
  return payload.documents;
}

export async function createKnowledgeDocument(payload: Partial<KnowledgeDocument> & { text?: string }): Promise<KnowledgeDocument> {
  const response = await apiRequest<{ document: KnowledgeDocument }>('/api/v1/knowledge/documents', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  if (payload.text) {
    const indexed = await apiRequest<{ document: KnowledgeDocument }>(`/api/v1/knowledge/documents/${response.document.document_id}/index`, {
      method: 'POST',
      body: JSON.stringify({ text: payload.text }),
    });
    return indexed.document;
  }
  return response.document;
}

export async function searchKnowledge(query: string): Promise<KnowledgeChunk[]> {
  const payload = await apiRequest<{ chunks: KnowledgeChunk[] }>('/api/v1/knowledge/search', {
    method: 'POST',
    body: JSON.stringify({ query }),
  });
  return payload.chunks;
}

export async function listModelProviders(): Promise<ModelProviderConfig[]> {
  const payload = await apiRequest<{ providers: ModelProviderConfig[] }>('/api/v1/model-gateway/providers');
  return payload.providers;
}

export async function listPromptTemplates(): Promise<PromptTemplate[]> {
  const payload = await apiRequest<{ prompts: PromptTemplate[] }>('/api/v1/model-gateway/prompts');
  return payload.prompts;
}

export async function createPromptTemplate(payload: { name: string; system: string; user_instruction: string; max_output_seconds?: number | null }): Promise<PromptTemplate> {
  const response = await apiRequest<{ prompt: PromptTemplate }>('/api/v1/model-gateway/prompts', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  return response.prompt;
}

export async function renderPromptTemplate(promptTemplate: string, promptPayload: Record<string, unknown>): Promise<{ role: string; content: string }[]> {
  const response = await apiRequest<{ messages: { role: string; content: string }[] }>('/api/v1/model-gateway/prompts/render', {
    method: 'POST',
    body: JSON.stringify({ prompt_template: promptTemplate, prompt_payload: promptPayload }),
  });
  return response.messages;
}

export async function listPlatformEvents(): Promise<PlatformEvent[]> {
  const payload = await apiRequest<{ events: PlatformEvent[] }>('/api/v1/platform/events');
  return payload.events;
}

export async function createPlatformEvent(payload: Partial<PlatformEvent>): Promise<PlatformEvent> {
  const response = await apiRequest<{ event: PlatformEvent }>('/api/v1/platform/events', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  return response.event;
}

export async function createPlatformMetric(payload: Partial<PlatformMetricSnapshot>): Promise<PlatformMetricSnapshot> {
  const response = await apiRequest<{ metric: PlatformMetricSnapshot }>('/api/v1/platform/metrics', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  return response.metric;
}

export async function listProjects(): Promise<Project[]> {
  const payload = await apiRequest<{ projects: Project[] }>('/api/v1/projects');
  return payload.projects;
}

export async function listMvpLivePlans(projectId = ''): Promise<MvpLivePlan[]> {
  const query = projectId ? `?project_id=${encodeURIComponent(projectId)}` : '';
  const payload = await apiRequest<{ plans: MvpLivePlan[] }>(`/api/v1/mvp/live-plans${query}`);
  return payload.plans;
}

export async function runMvpLivePlan(payload: { project_id?: string; product_id?: string; product?: Record<string, unknown>; brand_name?: string; script_note?: string; avatar_id?: string }): Promise<MvpLivePlan> {
  const response = await apiRequest<{ plan: MvpLivePlan }>('/api/v1/mvp/live-plans/run', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  return response.plan;
}

export async function createProject(payload: Partial<Project>): Promise<Project> {
  const response = await apiRequest<{ project: Project }>('/api/v1/projects', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  return response.project;
}

export async function listAgents(): Promise<AgentProfile[]> {
  const payload = await apiRequest<{ agents: AgentProfile[] }>('/api/v1/agents');
  return payload.agents;
}

export async function listAgentRuns(projectId?: string): Promise<AgentRun[]> {
  const path = projectId ? `/api/v1/projects/${projectId}/agent-runs` : '/api/v1/agents/runs';
  const payload = await apiRequest<{ runs: AgentRun[] }>(path);
  return payload.runs;
}

export async function listAssets(projectId?: string): Promise<Asset[]> {
  const path = projectId ? `/api/v1/projects/${projectId}/assets` : '/api/v1/assets';
  const payload = await apiRequest<{ assets: Asset[] }>(path);
  return payload.assets;
}

export async function createAsset(projectId: string, payload: Partial<Asset>): Promise<Asset> {
  const response = await apiRequest<{ asset: Asset }>(`/api/v1/projects/${projectId}/assets`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  return response.asset;
}

export async function listComponents(projectId?: string): Promise<LiveComponent[]> {
  const path = projectId ? `/api/v1/projects/${projectId}/components` : '/api/v1/components';
  const payload = await apiRequest<{ components: LiveComponent[] }>(path);
  return payload.components;
}

export async function createComponent(projectId: string, payload: Partial<LiveComponent>): Promise<LiveComponent> {
  const response = await apiRequest<{ component: LiveComponent }>(`/api/v1/projects/${projectId}/components`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  return response.component;
}

export async function listLiveScenes(projectId?: string): Promise<LiveScene[]> {
  const path = projectId ? `/api/v1/projects/${projectId}/scenes` : '/api/v1/scenes';
  const payload = await apiRequest<{ scenes: LiveScene[] }>(path);
  return payload.scenes;
}

export async function listLiveRoomCompositions(projectId?: string): Promise<LiveRoomComposition[]> {
  const path = projectId ? `/api/v1/projects/${projectId}/live-rooms` : '/api/v1/live-room-compositions';
  const payload = await apiRequest<{ compositions: LiveRoomComposition[] }>(path);
  return payload.compositions;
}

export async function listWorkflowDefinitions(): Promise<WorkflowDefinition[]> {
  const payload = await apiRequest<{ definitions: WorkflowDefinition[] }>('/api/v1/workflow/definitions');
  return payload.definitions;
}

export async function listWorkflowRuns(projectId?: string): Promise<WorkflowRun[]> {
  const path = projectId ? `/api/v1/projects/${projectId}/workflow-runs` : '/api/v1/workflow/runs';
  const payload = await apiRequest<{ runs: WorkflowRun[] }>(path);
  return payload.runs;
}

export async function listWorkflowNodeRuns(workflowRunId: string): Promise<WorkflowNodeRun[]> {
  const payload = await apiRequest<{ nodes: WorkflowNodeRun[] }>(`/api/v1/workflow/runs/${workflowRunId}/nodes`);
  return payload.nodes;
}

export async function listBestPractices(projectId?: string): Promise<BestPractice[]> {
  const path = projectId ? `/api/v1/projects/${projectId}/analytics/best-practices` : '/api/v1/analytics/overview';
  if (projectId) {
    const payload = await apiRequest<{ best_practices: BestPractice[] }>(path);
    return payload.best_practices;
  }
  const payload = await apiRequest<AnalyticsOverview>(path);
  return payload.best_practices;
}

export async function getAnalyticsOverview(projectId?: string): Promise<AnalyticsOverview> {
  const path = projectId ? `/api/v1/projects/${projectId}/analytics/overview` : '/api/v1/analytics/overview';
  return apiRequest<AnalyticsOverview>(path);
}

export async function listPromptVersions(): Promise<PromptVersion[]> {
  const payload = await apiRequest<{ prompt_versions: PromptVersion[] }>('/api/v1/prompt-versions');
  return payload.prompt_versions;
}

export async function listPluginProviders(): Promise<PluginProvider[]> {
  const payload = await apiRequest<{ providers: PluginProvider[] }>('/api/v1/plugins/providers');
  return payload.providers;
}
