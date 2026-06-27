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
    "学生": "酒类产品只面向成年人，不面向学生或未成年人群体。",
    "养生": "酒类产品不能宣传养生或保健功效，我们更多从礼赠、宴请和口感风格角度介绍。",
    "保健": "酒类产品不能宣传保健功效，建议大家理性饮酒、按需选择。",
    "治疗": "酒类产品不具备医疗或治疗功效，我们不做医疗、康复或健康承诺。",
    "医疗": "酒类产品不具备医疗功效，我们不做医疗或健康承诺。",
    "功效": "酒类产品不能宣传健康功效，请从口感、产区、礼赠和宴请场景角度介绍。",
    "治": "酒类产品不具备医疗功效，我们不做医疗或健康承诺。",
    "开车": "开车不喝酒，喝酒不开车。这个场景不建议饮酒。",
    "酒驾": "开车不喝酒，喝酒不开车，不能把饮酒和驾驶场景绑定宣传。",
    "多喝": "饮酒要适量理性，不建议过量饮用。",
    "过量饮酒": "饮酒要适量理性，不能鼓励过量饮酒或拼酒。",
    "最低价": "价格权益以直播间页面为准，避免使用无法证明的绝对化价格表述。",
    "全网最低": "价格权益以直播间页面为准，不使用全网最低等绝对化承诺。",
    "最后一瓶": "库存信息以直播间页面为准，不制造不实紧迫感。",
    "国家级奖项": "奖项、年份和荣誉需以可核验证据为准，避免夸大或不可证实表达。",
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
