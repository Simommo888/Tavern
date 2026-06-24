from __future__ import annotations

from apps.api.app.domain.live.entities import AudienceIntent, ProductProfile


def classify_intent(text: str) -> AudienceIntent:
    lowered = text.lower()
    if any(token in text for token in ["多少钱", "价格", "几块", "贵不贵"]):
        return "price_question"
    if any(token in text for token in ["送人", "送礼", "领导", "长辈", "端午"]):
        return "gift_question"
    if any(token in text for token in ["优惠", "福利", "券", "活动"]):
        return "promotion_question"
    if any(token in text for token in ["养生", "保健", "治", "未成年", "小孩", "开车", "多喝"]):
        return "compliance_risk"
    if any(token in text for token in ["度数", "规格", "产地", "香型", "口感"]):
        return "product_question"
    if "price" in lowered:
        return "price_question"
    return "smalltalk"


def fallback_reply(product: ProductProfile, text: str, intent: AudienceIntent) -> str:
    name = product.product_name or "这款产品"
    if intent == "price_question":
        return f"{name}的价格和权益以直播间当前活动为准，我建议大家按自己的送礼或宴请需求理性选择。"
    if intent == "gift_question":
        return f"{name}更适合成年人节日送礼、宴请拜访这类正式场景，礼盒包装会更体面一些。"
    if intent == "promotion_question":
        return f"今天主要看直播间实时权益和组合活动，我会把规格、适用场景和注意事项讲清楚。"
    if intent == "product_question":
        points = "、".join(product.selling_points[:3]) or "礼盒包装、宴请送礼"
        return f"{name}主打{points}，具体规格建议以下单页和客服确认为准。"
    if intent == "compliance_risk":
        return "酒类产品只面向成年人，不能宣传养生或医疗功效，也提醒大家适量理性饮酒。"
    return f"欢迎来到直播间，今天主要给大家介绍{name}，有价格、送礼和规格问题都可以直接问。"
