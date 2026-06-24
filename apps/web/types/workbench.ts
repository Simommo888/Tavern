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
};
