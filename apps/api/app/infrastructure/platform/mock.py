from __future__ import annotations

from apps.api.app.domain.workbench.entities import PlatformEvent, PlatformMetricSnapshot


class MockLivePlatformAdapter:
    def start_stream(self, session_id: str) -> dict:
        return {"session_id": session_id, "status": "started", "platform": "mock"}

    def stop_stream(self, session_id: str) -> dict:
        return {"session_id": session_id, "status": "stopped", "platform": "mock"}

    def send_comment(self, session_id: str, text: str) -> dict:
        return {"session_id": session_id, "sent": True, "text": text}

    def get_comment(self, session_id: str) -> list[PlatformEvent]:
        return [PlatformEvent(session_id=session_id, platform="mock", event_type="comment", user_name="模拟观众", text="这个适合送礼吗？")]

    def get_order(self, session_id: str) -> list[PlatformEvent]:
        return [PlatformEvent(session_id=session_id, platform="mock", event_type="order_created", user_name="模拟买家", order_amount=399)]

    def get_metrics(self, session_id: str) -> PlatformMetricSnapshot:
        return PlatformMetricSnapshot(session_id=session_id, platform="mock", online_users=1286, gmv=68420, order_count=329, interaction_rate=0.186, conversion_rate=0.042)
