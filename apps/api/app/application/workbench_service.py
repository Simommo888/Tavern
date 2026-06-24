from __future__ import annotations

from pathlib import Path
from typing import Any

from interfaces.production import utc_now_iso
from apps.api.app.domain.workbench.entities import AvatarJob, AvatarProfile, KnowledgeChunk, KnowledgeDocument, ModelProviderConfig, PlatformAccount, PlatformEvent, PlatformMetricSnapshot, ProductRecord, PromptTemplate, ScriptTemplate, WorkflowRule
from apps.api.app.infrastructure.repositories.file_workbench import JsonCollectionRepository


class WorkbenchService:
    def __init__(self, workspace_root: str | Path = ".") -> None:
        self.workspace_root = Path(workspace_root).resolve()
        self.products = JsonCollectionRepository(self.workspace_root, "products", ProductRecord, "product_id")
        self.avatars = JsonCollectionRepository(self.workspace_root, "avatars", AvatarProfile, "avatar_id")
        self.scripts = JsonCollectionRepository(self.workspace_root, "scripts", ScriptTemplate, "template_id")
        self.workflow_rules = JsonCollectionRepository(self.workspace_root, "workflow_rules", WorkflowRule, "rule_id")
        self.platform_accounts = JsonCollectionRepository(self.workspace_root, "platform_accounts", PlatformAccount, "account_id")
        self.metrics = JsonCollectionRepository(self.workspace_root, "platform_metrics", PlatformMetricSnapshot, "snapshot_id")
        self.knowledge_documents = JsonCollectionRepository(self.workspace_root, "knowledge_documents", KnowledgeDocument, "document_id")
        self.knowledge_chunks = JsonCollectionRepository(self.workspace_root, "knowledge_chunks", KnowledgeChunk, "chunk_id")
        self.model_providers = JsonCollectionRepository(self.workspace_root, "model_providers", ModelProviderConfig, "provider_id")
        self.prompt_templates = JsonCollectionRepository(self.workspace_root, "prompt_templates", PromptTemplate, "prompt_id")
        self.avatar_jobs = JsonCollectionRepository(self.workspace_root, "avatar_jobs", AvatarJob, "job_id")
        self.platform_events = JsonCollectionRepository(self.workspace_root, "platform_events", PlatformEvent, "event_id")
        self._ensure_seed_data()

    def dashboard_summary(self) -> dict[str, Any]:
        latest_metric = self.metrics.list()[-1] if self.metrics.list() else PlatformMetricSnapshot(
            online_users=1286,
            gmv=68420,
            order_count=329,
            interaction_rate=0.186,
            conversion_rate=0.042,
            current_product_id=self.products.list()[0].product_id if self.products.list() else "",
        )
        current_product = None
        if latest_metric.current_product_id:
            try:
                current_product = self.products.get(latest_metric.current_product_id)
            except KeyError:
                current_product = None
        return {
            "online_users": latest_metric.online_users,
            "current_gmv": latest_metric.gmv,
            "today_revenue": latest_metric.gmv,
            "order_count": latest_metric.order_count,
            "interaction_rate": latest_metric.interaction_rate,
            "conversion_rate": latest_metric.conversion_rate,
            "current_product": current_product.model_dump() if current_product else None,
            "avatar_status": "ready" if self.avatars.list() else "not_configured",
            "live_status": "running",
        }

    def create_product(self, payload: dict[str, Any]) -> ProductRecord:
        return self.products.upsert(ProductRecord.model_validate(payload))

    def update_product(self, product_id: str, payload: dict[str, Any]) -> ProductRecord:
        product = self.products.get(product_id)
        updated = product.model_copy(update={**payload, "updated_at": utc_now_iso()})
        return self.products.upsert(updated)

    def publish_product(self, product_id: str) -> ProductRecord:
        return self.update_product(product_id, {"status": "published"})

    def unpublish_product(self, product_id: str) -> ProductRecord:
        return self.update_product(product_id, {"status": "draft"})

    def create_avatar(self, payload: dict[str, Any]) -> AvatarProfile:
        return self.avatars.upsert(AvatarProfile.model_validate(payload))

    def update_avatar(self, avatar_id: str, payload: dict[str, Any]) -> AvatarProfile:
        avatar = self.avatars.get(avatar_id)
        updated = avatar.model_copy(update={**payload, "updated_at": utc_now_iso()})
        return self.avatars.upsert(updated)

    def create_script(self, payload: dict[str, Any]) -> ScriptTemplate:
        return self.scripts.upsert(ScriptTemplate.model_validate(payload))

    def update_script(self, template_id: str, payload: dict[str, Any]) -> ScriptTemplate:
        template = self.scripts.get(template_id)
        updated = template.model_copy(update={**payload, "updated_at": utc_now_iso()})
        return self.scripts.upsert(updated)

    def generate_script(self, category: str, product_id: str = "") -> ScriptTemplate:
        product_name = "这款酒"
        if product_id:
            try:
                product_name = self.products.get(product_id).product_name
            except KeyError:
                pass
        templates = {
            "opening": f"欢迎来到直播间，今天给大家重点介绍{product_name}，适合成年人节日送礼和商务宴请场景，大家按需理性选择。",
            "product": f"{product_name}主打礼盒包装、宴请送礼和成熟消费者聚会场景，具体规格和权益以直播间页面为准。",
            "sales": f"如果你正在考虑成年人节日拜访或商务宴请，可以关注{product_name}当前组合权益，理性下单、按需选择。",
            "interaction": f"大家有价格、香型、规格、送礼场景的问题都可以打在公屏，我会逐个说明{product_name}的适用场景。",
            "thanks": f"感谢支持{product_name}，也提醒大家酒类产品只面向成年人，请适量饮酒、理性消费。",
        }
        return self.create_script({
            "name": f"AI生成-{category}",
            "category": category,
            "content": templates.get(category, templates["interaction"]),
            "product_id": product_id,
            "ai_generated": True,
            "tags": ["酒类合规", "AI生成"],
        })

    def create_knowledge_document(self, payload: dict[str, Any]) -> KnowledgeDocument:
        return self.knowledge_documents.upsert(KnowledgeDocument.model_validate(payload))

    def index_knowledge_document(self, document_id: str, text: str = "") -> KnowledgeDocument:
        document = self.knowledge_documents.get(document_id)
        source_text = text.strip() or f"{document.name} 商品资料：适合成年人商务宴请、节日送礼和聚会场景。酒类产品不宣传医疗保健功效。"
        chunks = [part.strip() for part in source_text.replace("\r", "").split("\n") if part.strip()]
        if not chunks:
            chunks = [source_text]
        existing = [chunk for chunk in self.knowledge_chunks.list() if chunk.document_id != document_id]
        for index, chunk_text in enumerate(chunks):
            existing.append(KnowledgeChunk(document_id=document_id, product_id=document.product_id, chunk_index=index, text=chunk_text, embedding_status="embedded", metadata={"source_type": document.source_type}))
        self.knowledge_chunks._write(existing)
        updated = document.model_copy(update={"status": "indexed", "chunk_count": len(chunks), "updated_at": utc_now_iso()})
        return self.knowledge_documents.upsert(updated)

    def search_knowledge(self, query: str, product_id: str = "") -> list[KnowledgeChunk]:
        tokens = [token for token in query.replace("？", "").replace("，", " ").split() if token]
        chunks = self.knowledge_chunks.list()
        if product_id:
            chunks = [chunk for chunk in chunks if chunk.product_id in {"", product_id}]
        scored = []
        for chunk in chunks:
            score = sum(1 for token in tokens if token in chunk.text)
            if score or not tokens:
                scored.append((score, chunk))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [chunk for _, chunk in scored[:5]]

    def create_avatar_job(self, payload: dict[str, Any]) -> AvatarJob:
        job = AvatarJob.model_validate(payload)
        if not job.provider_job_id:
            job = job.model_copy(update={"provider_job_id": "heygen-dry-run", "status": "succeeded", "output_url": f"minio://avatar-jobs/{job.job_id}.mp4", "updated_at": utc_now_iso()})
        return self.avatar_jobs.upsert(job)

    def ingest_platform_event(self, payload: dict[str, Any]) -> PlatformEvent:
        event = PlatformEvent.model_validate(payload)
        self.platform_events.upsert(event)
        return event

    def _ensure_seed_data(self) -> None:
        if not self.products.list():
            product = self.create_product({
                "product_name": "可雅白兰地礼盒",
                "sku": "KOYA-500-GB",
                "price": 399,
                "original_price": 599,
                "aroma_type": "白兰地",
                "alcohol_degree": "40%vol",
                "volume": "500ml",
                "selling_points": ["节日送礼", "礼盒包装", "商务宴请"],
                "scenes": ["商务宴请", "送礼", "聚会"],
                "faqs": [{"question": "适合送领导吗？", "answer": "适合成年人正式拜访和商务宴请场景，建议按预算理性选择。"}],
                "status": "published",
            })
        else:
            product = self.products.list()[0]
        if not self.avatars.list():
            self.create_avatar({
                "name": "酒类品牌数字人主播",
                "provider": "heygen",
                "heygen_avatar_id": "",
                "heygen_voice_id": "",
                "voice_name": "中文女声",
                "status": "ready",
            })
        if not self.workflow_rules.list():
            for rule in [
                {"name": "用户进入欢迎", "event_type": "user_enter", "action_type": "welcome", "delay_seconds": 0},
                {"name": "下单感谢", "event_type": "order_created", "action_type": "thank_order", "delay_seconds": 0},
                {"name": "冷场 60 秒互动", "event_type": "cold_start", "action_type": "run_script", "delay_seconds": 60},
            ]:
                self.workflow_rules.upsert(WorkflowRule.model_validate(rule))
        if not self.platform_accounts.list():
            self.platform_accounts.upsert(PlatformAccount(display_name="手动模拟直播间", platform="manual", credentials_configured=True))
        if not self.metrics.list():
            self.metrics.upsert(PlatformMetricSnapshot(current_product_id=product.product_id, online_users=1286, gmv=68420, order_count=329, interaction_rate=0.186, conversion_rate=0.042))
        if not self.model_providers.list():
            for provider in [
                {"name": "gpt", "display_name": "GPT 主力回复模型", "chat_model": "gpt-4.1", "embedding_model": "text-embedding-3-large", "configured": False},
                {"name": "claude", "display_name": "Claude 高质量策划模型", "chat_model": "claude-sonnet-4-6", "configured": False},
                {"name": "gemini", "display_name": "Gemini 多模态模型", "chat_model": "gemini-2.5-pro", "configured": False},
            ]:
                self.model_providers.upsert(ModelProviderConfig.model_validate(provider))
        if not self.prompt_templates.list():
            self.prompt_templates.upsert(PromptTemplate(
                name="酒类主播回复 Prompt",
                purpose="live_reply",
                content="你是酒类电商数字人主播，回复必须自然口语化、15秒以内，并遵守酒类合规。",
                variables=["product", "audience_event", "retrieved_knowledge"],
            ))
        if not self.knowledge_documents.list():
            document = self.create_knowledge_document({"name": "可雅白兰地直播 FAQ", "source_type": "text", "product_id": product.product_id, "status": "uploaded"})
            self.index_knowledge_document(document.document_id, "适合送领导吗？适合成年人正式拜访和商务宴请场景。\n有什么卖点？礼盒包装、节日送礼、成熟消费者聚会场景。\n合规提醒：酒类不宣传养生、保健或医疗功效，不面向未成年人。")
