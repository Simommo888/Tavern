from __future__ import annotations

from pathlib import Path

from apps.api.app.agents.state import LiveAnchorState
from apps.api.app.application.workbench_service import WorkbenchService
from apps.api.app.domain.compliance.policies import check_alcohol_compliance
from apps.api.app.domain.live.entities import ProductProfile
from apps.api.app.domain.live.services import classify_intent, fallback_reply


class LiveAnchorGraph:
    def __init__(self, workbench: WorkbenchService | None = None, workspace_root: str | Path = ".") -> None:
        self.workbench = workbench or WorkbenchService(workspace_root)

    def run(self, state: LiveAnchorState) -> LiveAnchorState:
        state = self.normalize_audience_event(state)
        state = self.classify_comment_intent(state)
        state = self.retrieve_product_knowledge(state)
        state = self.pre_compliance_check(state)
        state = self.plan_reply_strategy(state)
        state = self.generate_anchor_reply(state)
        state = self.post_compliance_check(state)
        state = self.publish_live_event(state)
        return state

    def normalize_audience_event(self, state: LiveAnchorState) -> LiveAnchorState:
        state.setdefault("event_text", "")
        state.setdefault("errors", [])
        state["event_text"] = state["event_text"].strip()
        return state

    def classify_comment_intent(self, state: LiveAnchorState) -> LiveAnchorState:
        state["intent"] = classify_intent(state.get("event_text", ""))
        return state

    def retrieve_product_knowledge(self, state: LiveAnchorState) -> LiveAnchorState:
        product_id = str(state.get("product_context", {}).get("product_id") or "")
        results = self.workbench.search_knowledge_with_scores(state.get("event_text", ""), product_id=product_id, limit=5)
        state["retrieved_chunks"] = [
            {
                "chunk_id": item["chunk"].chunk_id,
                "document_id": item["chunk"].document_id,
                "product_id": item["chunk"].product_id,
                "text": item["chunk"].text,
                "score": item["score"],
                "matched_terms": item["matched_terms"],
            }
            for item in results
        ]
        return state

    def pre_compliance_check(self, state: LiveAnchorState) -> LiveAnchorState:
        if state.get("intent") == "compliance_risk":
            result = check_alcohol_compliance(state.get("event_text", ""))
            state["compliance_notes"] = result.notes
        else:
            state.setdefault("compliance_notes", [])
        return state

    def plan_reply_strategy(self, state: LiveAnchorState) -> LiveAnchorState:
        product_name = state.get("product_context", {}).get("product_name", "这款酒")
        state["draft_reply"] = f"围绕{product_name}回答观众问题，保持酒类合规和15秒以内口播。"
        return state

    def generate_anchor_reply(self, state: LiveAnchorState) -> LiveAnchorState:
        product_context = dict(state.get("product_context") or {})
        if "price" in product_context:
            product_context["price"] = str(product_context["price"])
        product = ProductProfile.model_validate(product_context)
        state["final_reply"] = fallback_reply(product, state.get("event_text", ""), state.get("intent", "smalltalk"))
        return state

    def post_compliance_check(self, state: LiveAnchorState) -> LiveAnchorState:
        result = check_alcohol_compliance(state.get("final_reply", ""))
        state["final_reply"] = result.text
        state["compliance_notes"] = [*state.get("compliance_notes", []), *result.notes]
        return state

    def publish_live_event(self, state: LiveAnchorState) -> LiveAnchorState:
        state.setdefault("model_invocation_ids", [])
        return state
