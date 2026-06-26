CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS tenants (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL,
  plan text NOT NULL DEFAULT 'starter',
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS users (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  email text NOT NULL,
  display_name text NOT NULL DEFAULT '',
  status text NOT NULL DEFAULT 'active',
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, email)
);

CREATE TABLE IF NOT EXISTS roles (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  name text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, name)
);

CREATE TABLE IF NOT EXISTS permissions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  role_id uuid NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
  permission text NOT NULL,
  UNIQUE (role_id, permission)
);

CREATE TABLE IF NOT EXISTS user_roles (
  user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  role_id uuid NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
  PRIMARY KEY (user_id, role_id)
);

CREATE TABLE IF NOT EXISTS products (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  product_code text NOT NULL,
  product_name text NOT NULL,
  sku text NOT NULL,
  price numeric(12,2) NOT NULL DEFAULT 0,
  original_price numeric(12,2) NOT NULL DEFAULT 0,
  aroma_type text NOT NULL DEFAULT '',
  alcohol_degree text NOT NULL DEFAULT '',
  volume text NOT NULL DEFAULT '',
  selling_points jsonb NOT NULL DEFAULT '[]',
  scenes jsonb NOT NULL DEFAULT '[]',
  status text NOT NULL DEFAULT 'draft',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, sku)
);

CREATE TABLE IF NOT EXISTS product_faqs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  product_id uuid NOT NULL REFERENCES products(id) ON DELETE CASCADE,
  question text NOT NULL,
  answer text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS avatar_profiles (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  name text NOT NULL,
  provider text NOT NULL DEFAULT 'heygen',
  heygen_avatar_id text NOT NULL DEFAULT '',
  heygen_voice_id text NOT NULL DEFAULT '',
  voice_name text NOT NULL DEFAULT '',
  source_material_urls jsonb NOT NULL DEFAULT '[]',
  status text NOT NULL DEFAULT 'draft',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS live_rooms (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  name text NOT NULL,
  avatar_id uuid REFERENCES avatar_profiles(id),
  product_pool jsonb NOT NULL DEFAULT '[]',
  status text NOT NULL DEFAULT 'draft',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS live_sessions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  live_room_id uuid REFERENCES live_rooms(id),
  product_id uuid REFERENCES products(id),
  session_code text NOT NULL,
  status text NOT NULL DEFAULT 'created',
  current_topic text NOT NULL DEFAULT '',
  event_count integer NOT NULL DEFAULT 0,
  reply_count integer NOT NULL DEFAULT 0,
  metadata jsonb NOT NULL DEFAULT '{}',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  stopped_at timestamptz
);

CREATE TABLE IF NOT EXISTS audience_events (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id uuid NOT NULL REFERENCES live_sessions(id) ON DELETE CASCADE,
  external_event_id text NOT NULL DEFAULT '',
  user_id text NOT NULL DEFAULT '',
  user_name text NOT NULL DEFAULT '',
  text text NOT NULL DEFAULT '',
  source text NOT NULL DEFAULT 'manual',
  intent text NOT NULL DEFAULT '',
  raw_payload jsonb NOT NULL DEFAULT '{}',
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (session_id, external_event_id)
);

CREATE TABLE IF NOT EXISTS model_invocations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid REFERENCES tenants(id),
  session_id uuid REFERENCES live_sessions(id),
  provider text NOT NULL,
  model text NOT NULL,
  purpose text NOT NULL,
  streaming boolean NOT NULL DEFAULT false,
  latency_ms integer NOT NULL DEFAULT 0,
  prompt_tokens integer NOT NULL DEFAULT 0,
  completion_tokens integer NOT NULL DEFAULT 0,
  estimated_cost numeric(12,6) NOT NULL DEFAULT 0,
  status text NOT NULL DEFAULT 'succeeded',
  error text NOT NULL DEFAULT '',
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS anchor_replies (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id uuid NOT NULL REFERENCES live_sessions(id) ON DELETE CASCADE,
  audience_event_id uuid REFERENCES audience_events(id),
  model_invocation_id uuid REFERENCES model_invocations(id),
  intent text NOT NULL,
  text text NOT NULL,
  compliance_passed boolean NOT NULL DEFAULT true,
  compliance_notes jsonb NOT NULL DEFAULT '[]',
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS speech_artifacts (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id uuid NOT NULL REFERENCES live_sessions(id) ON DELETE CASCADE,
  reply_id uuid REFERENCES anchor_replies(id) ON DELETE CASCADE,
  provider text NOT NULL,
  object_key text NOT NULL,
  mime_type text NOT NULL DEFAULT 'audio/wav',
  duration_seconds numeric(10,3) NOT NULL DEFAULT 0,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS compliance_reviews (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid REFERENCES tenants(id),
  session_id uuid REFERENCES live_sessions(id),
  target_type text NOT NULL,
  target_id text NOT NULL,
  input_text text NOT NULL,
  output_text text NOT NULL,
  passed boolean NOT NULL DEFAULT true,
  risk_level text NOT NULL DEFAULT 'none',
  notes jsonb NOT NULL DEFAULT '[]',
  policy_version text NOT NULL DEFAULT 'alcohol-v1',
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS script_templates (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  product_id uuid REFERENCES products(id),
  name text NOT NULL,
  category text NOT NULL,
  content text NOT NULL,
  tags jsonb NOT NULL DEFAULT '[]',
  ai_generated boolean NOT NULL DEFAULT false,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS workflow_rules (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  name text NOT NULL,
  event_type text NOT NULL,
  action_type text NOT NULL,
  enabled boolean NOT NULL DEFAULT true,
  delay_seconds integer NOT NULL DEFAULT 0,
  conditions jsonb NOT NULL DEFAULT '{}',
  metadata jsonb NOT NULL DEFAULT '{}',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS knowledge_documents (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  product_id uuid REFERENCES products(id),
  name text NOT NULL,
  source_type text NOT NULL,
  object_key text NOT NULL DEFAULT '',
  status text NOT NULL DEFAULT 'uploaded',
  chunk_count integer NOT NULL DEFAULT 0,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS knowledge_chunks (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id uuid NOT NULL REFERENCES knowledge_documents(id) ON DELETE CASCADE,
  product_id uuid REFERENCES products(id),
  chunk_index integer NOT NULL,
  text text NOT NULL,
  embedding_status text NOT NULL DEFAULT 'pending',
  milvus_collection text NOT NULL DEFAULT 'product_knowledge_chunks',
  milvus_primary_key text NOT NULL DEFAULT '',
  metadata jsonb NOT NULL DEFAULT '{}',
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS model_provider_configs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  name text NOT NULL,
  display_name text NOT NULL,
  base_url text NOT NULL DEFAULT '',
  chat_model text NOT NULL DEFAULT '',
  embedding_model text NOT NULL DEFAULT '',
  streaming_supported boolean NOT NULL DEFAULT true,
  prompt_management_supported boolean NOT NULL DEFAULT true,
  configured boolean NOT NULL DEFAULT false,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS prompt_templates (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  name text NOT NULL,
  purpose text NOT NULL,
  version text NOT NULL DEFAULT 'v1',
  content text NOT NULL,
  variables jsonb NOT NULL DEFAULT '[]',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS avatar_jobs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  avatar_id uuid NOT NULL REFERENCES avatar_profiles(id),
  job_type text NOT NULL,
  input_text text NOT NULL DEFAULT '',
  input_audio_url text NOT NULL DEFAULT '',
  provider_job_id text NOT NULL DEFAULT '',
  status text NOT NULL DEFAULT 'queued',
  output_url text NOT NULL DEFAULT '',
  error text NOT NULL DEFAULT '',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS platform_accounts (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  platform text NOT NULL,
  display_name text NOT NULL,
  status text NOT NULL DEFAULT 'connected',
  credentials_configured boolean NOT NULL DEFAULT false,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS platform_events (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  account_id uuid REFERENCES platform_accounts(id),
  session_id uuid REFERENCES live_sessions(id),
  platform text NOT NULL DEFAULT 'manual',
  event_type text NOT NULL,
  user_name text NOT NULL DEFAULT '',
  text text NOT NULL DEFAULT '',
  order_amount numeric(12,2) NOT NULL DEFAULT 0,
  raw_payload jsonb NOT NULL DEFAULT '{}',
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS platform_metrics (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id uuid REFERENCES live_sessions(id),
  platform text NOT NULL DEFAULT 'manual',
  online_users integer NOT NULL DEFAULT 0,
  gmv numeric(12,2) NOT NULL DEFAULT 0,
  order_count integer NOT NULL DEFAULT 0,
  interaction_rate numeric(8,4) NOT NULL DEFAULT 0,
  conversion_rate numeric(8,4) NOT NULL DEFAULT 0,
  current_product_id uuid REFERENCES products(id),
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS async_tasks (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid REFERENCES tenants(id),
  session_id uuid REFERENCES live_sessions(id),
  task_type text NOT NULL,
  routing_key text NOT NULL,
  status text NOT NULL DEFAULT 'queued',
  payload jsonb NOT NULL DEFAULT '{}',
  result jsonb NOT NULL DEFAULT '{}',
  error text NOT NULL DEFAULT '',
  idempotency_key text NOT NULL DEFAULT '',
  attempts integer NOT NULL DEFAULT 0,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (idempotency_key)
);

CREATE TABLE IF NOT EXISTS audit_logs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid REFERENCES tenants(id),
  user_id uuid REFERENCES users(id),
  action text NOT NULL,
  target_type text NOT NULL,
  target_id text NOT NULL,
  metadata jsonb NOT NULL DEFAULT '{}',
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS projects (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid REFERENCES tenants(id),
  name text NOT NULL,
  brand_name text NOT NULL DEFAULT '',
  industry text NOT NULL DEFAULT '',
  objective text NOT NULL DEFAULT '',
  status text NOT NULL DEFAULT 'active',
  tags jsonb NOT NULL DEFAULT '[]',
  metadata jsonb NOT NULL DEFAULT '{}',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS agent_profiles (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid REFERENCES tenants(id),
  name text NOT NULL,
  role text NOT NULL,
  department text NOT NULL DEFAULT 'LiveOS',
  status text NOT NULL DEFAULT 'idle',
  current_task text NOT NULL DEFAULT '',
  progress numeric(6,4) NOT NULL DEFAULT 0,
  token_count integer NOT NULL DEFAULT 0,
  cost_estimate numeric(12,6) NOT NULL DEFAULT 0,
  elapsed_seconds integer NOT NULL DEFAULT 0,
  logs jsonb NOT NULL DEFAULT '[]',
  output_summary text NOT NULL DEFAULT '',
  tool_names jsonb NOT NULL DEFAULT '[]',
  model_provider text NOT NULL DEFAULT 'openai_compatible',
  metadata jsonb NOT NULL DEFAULT '{}',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS agent_runs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id uuid REFERENCES projects(id),
  agent_id uuid REFERENCES agent_profiles(id),
  workflow_run_id uuid,
  node_run_id uuid,
  task text NOT NULL,
  status text NOT NULL DEFAULT 'queued',
  progress numeric(6,4) NOT NULL DEFAULT 0,
  input_payload jsonb NOT NULL DEFAULT '{}',
  output_payload jsonb NOT NULL DEFAULT '{}',
  logs jsonb NOT NULL DEFAULT '[]',
  token_count integer NOT NULL DEFAULT 0,
  cost_estimate numeric(12,6) NOT NULL DEFAULT 0,
  duration_seconds numeric(12,3) NOT NULL DEFAULT 0,
  error text NOT NULL DEFAULT '',
  started_at timestamptz NOT NULL DEFAULT now(),
  completed_at timestamptz
);

CREATE TABLE IF NOT EXISTS assets (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id uuid REFERENCES projects(id),
  name text NOT NULL,
  asset_type text NOT NULL DEFAULT 'document',
  source_uri text NOT NULL DEFAULT '',
  object_key text NOT NULL DEFAULT '',
  preview_url text NOT NULL DEFAULT '',
  tags jsonb NOT NULL DEFAULT '[]',
  metadata jsonb NOT NULL DEFAULT '{}',
  converted_component_ids jsonb NOT NULL DEFAULT '[]',
  status text NOT NULL DEFAULT 'ready',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS live_components (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id uuid REFERENCES projects(id),
  component_code text NOT NULL,
  name text NOT NULL,
  component_type text NOT NULL,
  current_version text NOT NULL DEFAULT 'v1',
  tags jsonb NOT NULL DEFAULT '[]',
  industries jsonb NOT NULL DEFAULT '[]',
  product_types jsonb NOT NULL DEFAULT '[]',
  usage_count integer NOT NULL DEFAULT 0,
  rating numeric(4,2) NOT NULL DEFAULT 0,
  gmv numeric(12,2) NOT NULL DEFAULT 0,
  ctr numeric(8,4) NOT NULL DEFAULT 0,
  cvr numeric(8,4) NOT NULL DEFAULT 0,
  best_session_count integer NOT NULL DEFAULT 0,
  resource_url text NOT NULL DEFAULT '',
  preview_url text NOT NULL DEFAULT '',
  metadata jsonb NOT NULL DEFAULT '{}',
  status text NOT NULL DEFAULT 'ready',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (project_id, component_code)
);

CREATE TABLE IF NOT EXISTS component_versions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  component_id uuid NOT NULL REFERENCES live_components(id) ON DELETE CASCADE,
  version text NOT NULL DEFAULT 'v1',
  resource_url text NOT NULL DEFAULT '',
  preview_url text NOT NULL DEFAULT '',
  changelog text NOT NULL DEFAULT '',
  metadata jsonb NOT NULL DEFAULT '{}',
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (component_id, version)
);

CREATE TABLE IF NOT EXISTS live_room_templates (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id uuid REFERENCES projects(id),
  name text NOT NULL,
  component_ids jsonb NOT NULL DEFAULT '[]',
  layout jsonb NOT NULL DEFAULT '{}',
  tags jsonb NOT NULL DEFAULT '[]',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS live_room_compositions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id uuid REFERENCES projects(id),
  name text NOT NULL,
  template_id uuid REFERENCES live_room_templates(id),
  components jsonb NOT NULL DEFAULT '[]',
  component_snapshot jsonb NOT NULL DEFAULT '[]',
  status text NOT NULL DEFAULT 'ready',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS prompt_versions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  prompt_id uuid REFERENCES prompt_templates(id),
  name text NOT NULL,
  purpose text NOT NULL,
  version text NOT NULL DEFAULT 'v1',
  content text NOT NULL,
  variables jsonb NOT NULL DEFAULT '[]',
  score numeric(6,2) NOT NULL DEFAULT 0,
  use_count integer NOT NULL DEFAULT 0,
  cost_estimate numeric(12,6) NOT NULL DEFAULT 0,
  gmv numeric(12,2) NOT NULL DEFAULT 0,
  ctr numeric(8,4) NOT NULL DEFAULT 0,
  cvr numeric(8,4) NOT NULL DEFAULT 0,
  status text NOT NULL DEFAULT 'active',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS workflow_definitions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL,
  version text NOT NULL DEFAULT 'v1',
  description text NOT NULL DEFAULT '',
  nodes jsonb NOT NULL DEFAULT '[]',
  edges jsonb NOT NULL DEFAULT '[]',
  status text NOT NULL DEFAULT 'active',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS workflow_runs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id uuid REFERENCES projects(id),
  workflow_definition_id uuid REFERENCES workflow_definitions(id),
  status text NOT NULL DEFAULT 'running',
  progress numeric(6,4) NOT NULL DEFAULT 0,
  current_node_id text NOT NULL DEFAULT '',
  input_payload jsonb NOT NULL DEFAULT '{}',
  output_payload jsonb NOT NULL DEFAULT '{}',
  logs jsonb NOT NULL DEFAULT '[]',
  token_count integer NOT NULL DEFAULT 0,
  cost_estimate numeric(12,6) NOT NULL DEFAULT 0,
  duration_seconds numeric(12,3) NOT NULL DEFAULT 0,
  error text NOT NULL DEFAULT '',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS workflow_node_runs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  workflow_run_id uuid NOT NULL REFERENCES workflow_runs(id) ON DELETE CASCADE,
  node_id text NOT NULL,
  name text NOT NULL,
  agent_id text NOT NULL DEFAULT '',
  status text NOT NULL DEFAULT 'queued',
  input_payload jsonb NOT NULL DEFAULT '{}',
  output_payload jsonb NOT NULL DEFAULT '{}',
  prompt_version_id uuid REFERENCES prompt_versions(id),
  logs jsonb NOT NULL DEFAULT '[]',
  token_count integer NOT NULL DEFAULT 0,
  cost_estimate numeric(12,6) NOT NULL DEFAULT 0,
  duration_seconds numeric(12,3) NOT NULL DEFAULT 0,
  error text NOT NULL DEFAULT '',
  started_at timestamptz NOT NULL DEFAULT now(),
  completed_at timestamptz
);

CREATE TABLE IF NOT EXISTS performance_metrics (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id uuid REFERENCES projects(id),
  session_id uuid REFERENCES live_sessions(id),
  component_ids jsonb NOT NULL DEFAULT '[]',
  gmv numeric(12,2) NOT NULL DEFAULT 0,
  ctr numeric(8,4) NOT NULL DEFAULT 0,
  cvr numeric(8,4) NOT NULL DEFAULT 0,
  watch_seconds integer NOT NULL DEFAULT 0,
  retention_rate numeric(8,4) NOT NULL DEFAULT 0,
  interaction_rate numeric(8,4) NOT NULL DEFAULT 0,
  like_count integer NOT NULL DEFAULT 0,
  comment_count integer NOT NULL DEFAULT 0,
  order_count integer NOT NULL DEFAULT 0,
  refund_rate numeric(8,4) NOT NULL DEFAULT 0,
  product_clicks integer NOT NULL DEFAULT 0,
  add_to_cart_rate numeric(8,4) NOT NULL DEFAULT 0,
  conversion_rate numeric(8,4) NOT NULL DEFAULT 0,
  metadata jsonb NOT NULL DEFAULT '{}',
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS live_session_snapshots (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id uuid REFERENCES projects(id),
  session_id uuid REFERENCES live_sessions(id),
  composition_id uuid REFERENCES live_room_compositions(id),
  component_ids jsonb NOT NULL DEFAULT '[]',
  script_ids jsonb NOT NULL DEFAULT '[]',
  prompt_versions jsonb NOT NULL DEFAULT '[]',
  avatar_id uuid REFERENCES avatar_profiles(id),
  voice_id text NOT NULL DEFAULT '',
  workflow_version text NOT NULL DEFAULT 'v1',
  performance_metric_id uuid REFERENCES performance_metrics(id),
  snapshot jsonb NOT NULL DEFAULT '{}',
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS best_practices (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id uuid REFERENCES projects(id),
  title text NOT NULL,
  query_label text NOT NULL DEFAULT '',
  source_session_id uuid REFERENCES live_sessions(id),
  component_ids jsonb NOT NULL DEFAULT '[]',
  script_ids jsonb NOT NULL DEFAULT '[]',
  prompt_versions jsonb NOT NULL DEFAULT '[]',
  score numeric(8,2) NOT NULL DEFAULT 0,
  reason text NOT NULL DEFAULT '',
  reusable_payload jsonb NOT NULL DEFAULT '{}',
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS plugin_providers (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  category text NOT NULL,
  provider_id text NOT NULL,
  display_name text NOT NULL,
  source_type text NOT NULL DEFAULT 'builtin',
  repo_url text NOT NULL DEFAULT '',
  commit text NOT NULL DEFAULT '',
  license text NOT NULL DEFAULT '',
  capabilities jsonb NOT NULL DEFAULT '[]',
  enabled boolean NOT NULL DEFAULT true,
  health_status text NOT NULL DEFAULT 'unknown',
  config_schema jsonb NOT NULL DEFAULT '{}',
  metadata jsonb NOT NULL DEFAULT '{}',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (category, provider_id)
);

CREATE INDEX IF NOT EXISTS idx_products_tenant ON products(tenant_id);
CREATE INDEX IF NOT EXISTS idx_live_sessions_tenant ON live_sessions(tenant_id);
CREATE INDEX IF NOT EXISTS idx_audience_events_session ON audience_events(session_id, created_at);
CREATE INDEX IF NOT EXISTS idx_anchor_replies_session ON anchor_replies(session_id, created_at);
CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_document ON knowledge_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_platform_events_session ON platform_events(session_id, created_at);
CREATE INDEX IF NOT EXISTS idx_async_tasks_status ON async_tasks(status, routing_key);
