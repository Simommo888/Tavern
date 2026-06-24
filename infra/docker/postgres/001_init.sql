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

CREATE INDEX IF NOT EXISTS idx_products_tenant ON products(tenant_id);
CREATE INDEX IF NOT EXISTS idx_live_sessions_tenant ON live_sessions(tenant_id);
CREATE INDEX IF NOT EXISTS idx_audience_events_session ON audience_events(session_id, created_at);
CREATE INDEX IF NOT EXISTS idx_anchor_replies_session ON anchor_replies(session_id, created_at);
CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_document ON knowledge_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_platform_events_session ON platform_events(session_id, created_at);
CREATE INDEX IF NOT EXISTS idx_async_tasks_status ON async_tasks(status, routing_key);
