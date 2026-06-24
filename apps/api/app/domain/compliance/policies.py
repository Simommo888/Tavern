from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class ComplianceResult:
    passed: bool
    text: str
    notes: list[str] = field(default_factory=list)


RISK_REWRITES = {
    "未成年": "这类酒水只面向成年人，未成年人不能饮酒，也不建议购买酒类产品。",
    "小孩": "酒类产品只适合成年人理性选择，不面向未成年人。",
    "养生": "酒类产品不能宣传养生或保健功效，我们更多从礼赠、宴请和口感风格角度介绍。",
    "保健": "酒类产品不能宣传保健功效，建议大家理性饮酒、按需选择。",
    "治": "酒类产品不具备医疗功效，我们不做医疗或健康承诺。",
    "开车": "开车不喝酒，喝酒不开车。这个场景不建议饮酒。",
    "多喝": "饮酒要适量理性，不建议过量饮用。",
}


def check_alcohol_compliance(text: str) -> ComplianceResult:
    notes: list[str] = []
    safe_text = text.strip()
    for keyword, rewrite in RISK_REWRITES.items():
        if keyword in safe_text:
            notes.append(f"命中酒类合规风险词：{keyword}")
            safe_text = rewrite
            break
    if not notes:
        if "理性饮酒" not in safe_text and len(safe_text) < 180:
            safe_text = f"{safe_text} 也提醒大家理性饮酒。"
        return ComplianceResult(True, safe_text, [])
    return ComplianceResult(False, safe_text, notes)
