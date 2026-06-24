from __future__ import annotations

from apps.api.app.domain.compliance.policies import ComplianceResult, check_alcohol_compliance


class ComplianceService:
    def review_alcohol_reply(self, text: str) -> ComplianceResult:
        return check_alcohol_compliance(text)
