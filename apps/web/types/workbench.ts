export type ProductFaq = {
  question: string;
  answer: string;
};

export type ProductRecord = {
  product_id: string;
  product_name: string;
  sku: string;
  price: number;
  original_price: number;
  aroma_type: string;
  alcohol_degree: string;
  volume: string;
  selling_points: string[];
  scenes: string[];
  faqs: ProductFaq[];
  status: string;
};

export type AvatarProfile = {
  avatar_id: string;
  name: string;
  provider: string;
  heygen_avatar_id: string;
  heygen_voice_id: string;
  voice_name: string;
  source_material_urls: string[];
  status: string;
};

export type ScriptTemplate = {
  template_id: string;
  name: string;
  category: string;
  content: string;
  product_id: string;
  tags: string[];
  ai_generated: boolean;
};

export type WorkflowRule = {
  rule_id: string;
  name: string;
  event_type: string;
  action_type: string;
  enabled: boolean;
  delay_seconds: number;
};

export type PlatformMetricSnapshot = {
  snapshot_id: string;
  session_id: string;
  platform: string;
  online_users: number;
  gmv: number;
  order_count: number;
  interaction_rate: number;
  conversion_rate: number;
  current_product_id: string;
};

export type KnowledgeDocument = {
  document_id: string;
  name: string;
  source_type: string;
  product_id: string;
  status: string;
  chunk_count: number;
};

export type KnowledgeChunk = {
  chunk_id: string;
  document_id: string;
  product_id: string;
  chunk_index: number;
  text: string;
  embedding_status: string;
};

export type ModelProviderConfig = {
  provider_id: string;
  name: string;
  display_name: string;
  chat_model: string;
  embedding_model: string;
  streaming_supported: boolean;
  prompt_management_supported: boolean;
  configured: boolean;
};

export type PromptTemplate = {
  prompt_id: string;
  name: string;
  purpose: string;
  version: string;
  content: string;
  variables: string[];
  system?: string;
  user_instruction?: string;
  max_output_seconds?: number | null;
};

export type PlatformEvent = {
  event_id: string;
  session_id: string;
  platform: string;
  event_type: string;
  user_name: string;
  text: string;
  order_amount: number;
};

export type DashboardSummary = {
  online_users: number;
  current_gmv: number;
  today_revenue: number;
  order_count: number;
  interaction_rate: number;
  conversion_rate: number;
  current_product: ProductRecord | null;
  avatar_status: string;
  live_status: string;
  project_count: number;
  active_agent_count: number;
  component_count: number;
  workflow_run_count: number;
};

export type Project = {
  project_id: string;
  name: string;
  brand_name: string;
  industry: string;
  objective: string;
  status: string;
  tags: string[];
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type AgentProfile = {
  agent_id: string;
  name: string;
  role: string;
  department: string;
  status: string;
  current_task: string;
  progress: number;
  token_count: number;
  cost_estimate: number;
  elapsed_seconds: number;
  logs: string[];
  output_summary: string;
  tool_names: string[];
  model_provider: string;
};

export type AgentRun = {
  run_id: string;
  project_id: string;
  agent_id: string;
  workflow_run_id: string;
  node_run_id: string;
  task: string;
  status: string;
  progress: number;
  input_payload: Record<string, unknown>;
  output_payload: Record<string, unknown>;
  logs: string[];
  token_count: number;
  cost_estimate: number;
  duration_seconds: number;
  error: string;
  started_at: string;
  completed_at: string;
};

export type Asset = {
  asset_id: string;
  uuid: string;
  version: string;
  project_id: string;
  name: string;
  asset_type: string;
  source_uri: string;
  object_key: string;
  preview_url: string;
  tags: string[];
  metadata: Record<string, unknown>;
  converted_component_ids: string[];
  status: string;
};

export type LiveComponent = {
  component_id: string;
  uuid: string;
  component_code: string;
  name: string;
  component_type: string;
  current_version: string;
  project_id: string;
  source_asset_ids: string[];
  tags: string[];
  industries: string[];
  product_types: string[];
  usage_count: number;
  rating: number;
  gmv: number;
  ctr: number;
  cvr: number;
  best_session_count: number;
  resource_url: string;
  preview_url: string;
  metadata: Record<string, unknown>;
  status: string;
};

export type LiveScene = {
  scene_id: string;
  uuid: string;
  version: string;
  project_id: string;
  name: string;
  scene_type: string;
  component_ids: string[];
  component_slots: Record<string, unknown>[];
  component_snapshot: LiveComponent[];
  layout: Record<string, unknown>;
  tags: string[];
  metadata: Record<string, unknown>;
  status: string;
};

export type LiveRoomComposition = {
  composition_id: string;
  uuid: string;
  version: string;
  project_id: string;
  name: string;
  template_id: string;
  scene_ids: string[];
  scene_snapshot: LiveScene[];
  components: Record<string, unknown>[];
  component_snapshot: LiveComponent[];
  tags: string[];
  metadata: Record<string, unknown>;
  status: string;
};

export type BestPractice = {
  best_practice_id: string;
  project_id: string;
  title: string;
  query_label: string;
  source_session_id: string;
  component_ids: string[];
  script_ids: string[];
  prompt_versions: string[];
  score: number;
  reason: string;
  reusable_payload: Record<string, unknown>;
};

export type PromptVersion = {
  prompt_version_id: string;
  prompt_id: string;
  name: string;
  purpose: string;
  version: string;
  content: string;
  variables: string[];
  score: number;
  use_count: number;
  cost_estimate: number;
  gmv: number;
  ctr: number;
  cvr: number;
  status: string;
};

export type WorkflowNodeDefinition = {
  id: string;
  label: string;
  agent: string;
  stage?: string;
  artifact?: string;
  description?: string;
  reusable?: boolean;
};

export type WorkflowDefinition = {
  workflow_definition_id: string;
  name: string;
  version: string;
  description: string;
  nodes: WorkflowNodeDefinition[];
  edges: { source: string; target: string; type?: string }[];
  status: string;
};

export type MvpLivePlan = {
  plan_id: string;
  project_id: string;
  product_id: string;
  workflow_run_id: string;
  script_template_id: string;
  avatar_id: string;
  avatar_job_id: string;
  live_room_composition_id: string;
  status: string;
  steps: Record<string, unknown>[];
  product_snapshot: Record<string, unknown>;
  brand_analysis: Record<string, unknown>;
  script_snapshot: Record<string, unknown>;
  speech_artifact_uri: string;
  avatar_video_uri: string;
  live_video_uri: string;
  saved_outputs: Record<string, unknown>;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type WorkflowRun = {
  workflow_run_id: string;
  project_id: string;
  workflow_definition_id: string;
  status: string;
  progress: number;
  current_node_id: string;
  input_payload: Record<string, unknown>;
  output_payload: Record<string, unknown>;
  logs: string[];
  token_count: number;
  cost_estimate: number;
  duration_seconds: number;
  error: string;
  created_at: string;
  updated_at: string;
};

export type ProductVideoWorkflowSnapshot = {
  definition: WorkflowDefinition;
  run: WorkflowRun;
  nodes: WorkflowNodeRun[];
  project: Project;
  product: ProductRecord;
  final_video: Record<string, unknown>;
  artifacts: Record<string, string>;
};

export type WorkflowStartPayload = {
  brand_name?: string;
  duration_seconds?: number;
  aspect_ratio?: string;
  bgm_style?: string;
  product_id?: string;
  project_id?: string;
  product?: Record<string, unknown>;
  brand_profile?: Record<string, unknown>;
};

export type WorkflowNodeRun = {
  node_run_id: string;
  workflow_run_id: string;
  node_id: string;
  name: string;
  agent_id: string;
  status: string;
  input_payload: Record<string, unknown>;
  output_payload: Record<string, unknown>;
  prompt_version_id: string;
  logs: string[];
  token_count: number;
  cost_estimate: number;
  duration_seconds: number;
  error: string;
  started_at: string;
  completed_at: string;
};

export type PluginProvider = {
  plugin_id: string;
  category: string;
  provider_id: string;
  display_name: string;
  source_type: string;
  repo_url: string;
  commit: string;
  license: string;
  capabilities: string[];
  enabled: boolean;
  health_status: string;
};

export type AnalyticsSummary = {
  gmv: number;
  ctr: number;
  cvr: number;
  order_count: number;
  session_count: number;
  component_count: number;
  prompt_count: number;
  avatar_count: number;
  snapshot_count: number;
};

export type TopSessionRankingItem = {
  rank: number;
  session_id: string;
  metric_id: string;
  gmv: number;
  ctr: number;
  cvr: number;
  order_count: number;
  component_ids: string[];
  prompt_versions: string[];
  avatar_id: string;
  composition_id: string;
  score: number;
};

export type ComponentRankingItem = {
  rank: number;
  component_id: string;
  component_code: string;
  name: string;
  component_type: string;
  gmv: number;
  ctr: number;
  cvr: number;
  usage_count: number;
  best_session_count: number;
  score: number;
};

export type PromptRankingItem = {
  rank: number;
  prompt_version_id: string;
  prompt_id: string;
  name: string;
  purpose: string;
  version: string;
  gmv: number;
  ctr: number;
  cvr: number;
  use_count: number;
  cost_estimate: number;
  session_count: number;
  score: number;
};

export type AvatarRankingItem = {
  rank: number;
  avatar_id: string;
  name: string;
  provider: string;
  voice_name: string;
  status: string;
  session_count: number;
  gmv: number;
  ctr: number;
  cvr: number;
  score: number;
};

export type BestPracticeRankingItem = {
  rank: number;
  best_practice_id: string;
  title: string;
  query_label: string;
  score: number;
  reason: string;
  component_ids: string[];
  prompt_versions: string[];
  source_session_id: string;
};

export type AnalyticsOverview = {
  summary: AnalyticsSummary;
  top_session: Record<string, unknown> | null;
  top_ranking: TopSessionRankingItem[];
  top_components: LiveComponent[];
  component_ranking: ComponentRankingItem[];
  prompt_ranking: PromptRankingItem[];
  avatar_ranking: AvatarRankingItem[];
  best_practices: BestPractice[];
  best_practice_ranking: BestPracticeRankingItem[];
  snapshot_count: number;
};
