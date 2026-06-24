import type { AvatarProfile, DashboardSummary, KnowledgeChunk, KnowledgeDocument, ModelProviderConfig, PlatformEvent, PlatformMetricSnapshot, ProductRecord, PromptTemplate, ScriptTemplate, WorkflowRule } from '@/types/workbench';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? 'http://127.0.0.1:8770';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) },
    cache: 'no-store',
    ...init,
  });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json() as Promise<T>;
}

export async function getDashboardSummary(): Promise<DashboardSummary> {
  return request('/api/v1/dashboard/summary');
}

export async function listProducts(): Promise<ProductRecord[]> {
  const payload = await request<{ products: ProductRecord[] }>('/api/v1/products');
  return payload.products;
}

export async function createProduct(payload: Partial<ProductRecord>): Promise<ProductRecord> {
  const response = await request<{ product: ProductRecord }>('/api/v1/products', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  return response.product;
}

export async function publishProduct(productId: string): Promise<ProductRecord> {
  const response = await request<{ product: ProductRecord }>(`/api/v1/products/${productId}/publish`, { method: 'POST' });
  return response.product;
}

export async function unpublishProduct(productId: string): Promise<ProductRecord> {
  const response = await request<{ product: ProductRecord }>(`/api/v1/products/${productId}/unpublish`, { method: 'POST' });
  return response.product;
}

export async function listAvatars(): Promise<AvatarProfile[]> {
  const payload = await request<{ avatars: AvatarProfile[] }>('/api/v1/avatars');
  return payload.avatars;
}

export async function createAvatar(payload: Partial<AvatarProfile>): Promise<AvatarProfile> {
  const response = await request<{ avatar: AvatarProfile }>('/api/v1/avatars', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  return response.avatar;
}

export async function createAvatarJob(avatarId: string, inputText: string): Promise<{ job_id: string; status: string; output_url: string }> {
  const response = await request<{ job: { job_id: string; status: string; output_url: string } }>(`/api/v1/avatars/${avatarId}/jobs`, {
    method: 'POST',
    body: JSON.stringify({ input_text: inputText, job_type: 'text_drive' }),
  });
  return response.job;
}

export async function listScriptTemplates(): Promise<ScriptTemplate[]> {
  const payload = await request<{ templates: ScriptTemplate[] }>('/api/v1/scripts/templates');
  return payload.templates;
}

export async function generateScriptTemplate(category: string, productId = ''): Promise<ScriptTemplate> {
  const payload = await request<{ template: ScriptTemplate }>('/api/v1/scripts/templates/generate', {
    method: 'POST',
    body: JSON.stringify({ category, product_id: productId }),
  });
  return payload.template;
}

export async function listWorkflowRules(): Promise<WorkflowRule[]> {
  const payload = await request<{ rules: WorkflowRule[] }>('/api/v1/workflow/rules');
  return payload.rules;
}

export async function createWorkflowRule(payload: Partial<WorkflowRule>): Promise<WorkflowRule> {
  const response = await request<{ rule: WorkflowRule }>('/api/v1/workflow/rules', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  return response.rule;
}

export async function updateWorkflowRule(ruleId: string, payload: Partial<WorkflowRule>): Promise<WorkflowRule> {
  const response = await request<{ rule: WorkflowRule }>(`/api/v1/workflow/rules/${ruleId}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  });
  return response.rule;
}

export async function listPlatformMetrics(): Promise<PlatformMetricSnapshot[]> {
  const payload = await request<{ metrics: PlatformMetricSnapshot[] }>('/api/v1/platform/metrics');
  return payload.metrics;
}

export async function listKnowledgeDocuments(): Promise<KnowledgeDocument[]> {
  const payload = await request<{ documents: KnowledgeDocument[] }>('/api/v1/knowledge/documents');
  return payload.documents;
}

export async function createKnowledgeDocument(payload: Partial<KnowledgeDocument> & { text?: string }): Promise<KnowledgeDocument> {
  const response = await request<{ document: KnowledgeDocument }>('/api/v1/knowledge/documents', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  if (payload.text) {
    const indexed = await request<{ document: KnowledgeDocument }>(`/api/v1/knowledge/documents/${response.document.document_id}/index`, {
      method: 'POST',
      body: JSON.stringify({ text: payload.text }),
    });
    return indexed.document;
  }
  return response.document;
}

export async function searchKnowledge(query: string): Promise<KnowledgeChunk[]> {
  const payload = await request<{ chunks: KnowledgeChunk[] }>('/api/v1/knowledge/search', {
    method: 'POST',
    body: JSON.stringify({ query }),
  });
  return payload.chunks;
}

export async function listModelProviders(): Promise<ModelProviderConfig[]> {
  const payload = await request<{ providers: ModelProviderConfig[] }>('/api/v1/model-gateway/providers');
  return payload.providers;
}

export async function listPromptTemplates(): Promise<PromptTemplate[]> {
  const payload = await request<{ prompts: PromptTemplate[] }>('/api/v1/model-gateway/prompts');
  return payload.prompts;
}

export async function listPlatformEvents(): Promise<PlatformEvent[]> {
  const payload = await request<{ events: PlatformEvent[] }>('/api/v1/platform/events');
  return payload.events;
}

export async function createPlatformEvent(payload: Partial<PlatformEvent>): Promise<PlatformEvent> {
  const response = await request<{ event: PlatformEvent }>('/api/v1/platform/events', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  return response.event;
}

export async function createPlatformMetric(payload: Partial<PlatformMetricSnapshot>): Promise<PlatformMetricSnapshot> {
  const response = await request<{ metric: PlatformMetricSnapshot }>('/api/v1/platform/metrics', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  return response.metric;
}
