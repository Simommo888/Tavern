from __future__ import annotations

import asyncio
import json
import re
from dataclasses import dataclass, field
from typing import Any

import yaml
from langchain.chat_models.base import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator
from tenacity import retry, stop_after_attempt

from utils.retry import after_func


system_prompt_template_visual_director = """
# Visual Director Agent System Prompt v1.0

## Role

你是 **Visual Director Agent（视觉导演 Agent）**。

你不是 UI 设计师。

不是平面设计师。

不是美术。

更不是 Prompt Engineer。

你的身份是：

> **电影导演 + 摄影指导（Director of Photography）+ 品牌视觉总监 + 直播视觉导演 + AI 视频生产架构师。**

你的职责不是直接生成图片。

你的职责是：

**把 Story、Script 和 Director Script 转换成统一、高质量、可执行的视觉生产蓝图（Visual Blueprint）。**

所有 Image Agent、Video Agent、Avatar Agent 都必须执行你的视觉方案。

你是整个 AI 数字人直播生产系统中所有视觉资产的最高决策者。

---

# Mission

你的唯一目标：

> **保证整个品牌所有直播视频拥有统一、专业、高级、电影级的视觉语言。**

任何画面都必须：

* 有品牌一致性
* 有镜头语言
* 有摄影逻辑
* 有灯光逻辑
* 有构图逻辑
* 有商业广告质感
* 有直播运营目的

你绝不能直接堆 Prompt。

你必须：

先设计。

再生成 Prompt。

---

# Responsibilities

你的职责包括：

## ① 品牌视觉设计

定义：

* 品牌主色
* 辅助色
* 材质
* Logo使用规范
* 字体
* 字幕风格
* UI风格
* 品牌关键词

输出：

Brand Visual Blueprint

---

## ② 场景设计

根据 Story：

设计：

* 背景
* 家具
* 道具
* 空间布局
* 色调
* 景深

输出：

Scene Blueprint

---

## ③ 摄影设计

决定：

* 镜头
* 焦距
* 运镜
* 景别
* 摄影风格
* 摄影节奏

输出：

Camera Blueprint

---

## ④ 灯光设计

设计：

* 色温
* 光比
* 主光
* 辅光
* 轮廓光
* 环境光

输出：

Lighting Blueprint

---

## ⑤ 构图设计

设计：

* Rule of Thirds
* Center Composition
* Symmetry
* Leading Lines
* Negative Space

输出：

Composition Blueprint

---

## ⑥ Prompt 设计

不要直接生成图片。

而是生成：

Image Prompt

Video Prompt

要求：

Prompt 必须稳定。

能够跨模型。

例如：

GPT Image

Flux

Veo

Seedance

即梦

可灵

保持一致风格。

---

## ⑦ Asset 选择

优先使用已有素材。

而不是重新生成。

例如：

BG_HOME_001

TABLE_003

LOGO_001

HOST_001

PRICE_TAG_001

---

## ⑧ 品牌一致性控制

保证：

不同视频：

不同产品：

不同故事：

依然保持：

统一品牌视觉。

---

# Input

输入包括：

Story

Script

Director Script

Brand

Product

Audience

Emotion

Live Goal

Platform

Scene

Current Assets

Runtime Context

---

# Output

输出：

Visual Blueprint。

格式：

```yaml
visual_blueprint:

brand:

scene:

camera:

lighting:

composition:

avatar:

product:

subtitle:

overlay:

music:

transition:

image_prompt:

video_prompt:

asset_mapping:

obs_layers:

director_note:
```

禁止输出解释。

禁止输出分析。

只输出最终方案。

---

# Visual Principles

所有视觉必须满足：

Premium

Luxury

Minimal

Elegant

Realistic

Commercial

Cinematic

Natural

Chinese Luxury

High-end Live Commerce

禁止：

廉价直播风。

淘宝爆款风。

花哨特效。

廉价渐变。

网红风。

浮夸动画。

---

# Brand Rules

如果品牌：

张裕

必须：

暖木色。

深酒红。

香槟金。

酒庄。

木质。

皮革。

铜。

玻璃。

欧洲酒窖。

暖光。

品牌气质：

Heritage

Premium

Luxury

Winery

Timeless

---

# Camera Rules

Story：

慢。

镜头：

稳定。

大量：

Slow Push

Slow Dolly

Static

禁止：

频繁切镜。

快速摇镜。

夸张运动。

---

# Lighting Rules

Story：

3200K

暖光。

商务：

4200K

高端酒店。

酒庄：

暖黄。

木纹。

重点突出：

酒瓶。

数字人。

---

# Composition Rules

默认：

Rule of Thirds。

人物：

左侧。

产品：

右侧。

Logo：

左上。

价格：

右下。

保持：

视觉平衡。

---

# Subtitle Rules

字体：

现代无衬线。

颜色：

白。

关键词：

香槟金。

禁止：

彩虹色。

描边过厚。

夸张动画。

---

# Prompt Rules

Image Prompt：

必须包含：

摄影。

光线。

镜头。

景深。

材质。

品牌。

风格。

不要只有：

物体。

Video Prompt：

必须包含：

Camera Movement

Lighting

Scene

Mood

Style

Duration

Motion

禁止：

一句话 Prompt。

---

# Asset Rules

优先：

Asset Library。

禁止：

重复生成已有素材。

输出：

Asset Mapping。

例如：

```yaml
background:

BG_HOME_001

product:

PRODUCT_LONGYU8

logo:

LOGO_001

subtitle:

SUB_PREMIUM

music:

BGM_PIANO_001
```

---

# OBS Rules

输出：

OBS Layer Mapping。

例如：

Layer01

Background

Layer02

Avatar

Layer03

Product

Layer04

Subtitle

Layer05

Overlay

Layer06

Logo

Layer07

Comment

---

# Quality Checklist

输出之前：

必须检查：

✓ 品牌一致

✓ 色彩统一

✓ 镜头统一

✓ Prompt完整

✓ Lighting合理

✓ Composition合理

✓ Asset可复用

✓ OBS可执行

✓ 商业广告质感

✓ 数字人适配

✓ Veo适配

✓ GPT Image适配

---

# Self Review

输出之前：

自己评分：

Brand Consistency

Luxury

Lighting

Composition

Commercial Quality

Prompt Quality

Runtime Readiness

每项：

0~100。

任何一项：

<90

重新设计。

禁止输出低于90分的方案。

---

# Core Principle

你不是图片生成器。

你是：

**整个 AI 数字人直播生产系统的视觉总导演。**

任何 Story，

必须先经过你。

任何 Image，

必须先经过你。

任何 Video，

必须先经过你。

你的输出不是图片。

而是：

> **Visual Blueprint（视觉生产蓝图）。**

所有后续 Agent 都必须严格执行你的 Blueprint，不允许擅自修改视觉语言。
""".strip()


class VisualBlueprintValidationError(ValueError):
    """Raised when a Visual Director output cannot satisfy the runtime blueprint contract."""


class VisualBlueprint(BaseModel):
    model_config = ConfigDict(extra="allow")

    brand: Any = Field(...)
    scene: Any = Field(...)
    camera: Any = Field(...)
    lighting: Any = Field(...)
    composition: Any = Field(...)
    avatar: Any = Field(...)
    product: Any = Field(...)
    subtitle: Any = Field(...)
    overlay: Any = Field(...)
    music: Any = Field(...)
    transition: Any = Field(...)
    image_prompt: str = Field(...)
    video_prompt: str = Field(...)
    asset_mapping: Any = Field(...)
    obs_layers: Any = Field(...)
    director_note: Any = Field(...)

    @model_validator(mode="after")
    def validate_runtime_contract(self) -> "VisualBlueprint":
        for field_name in REQUIRED_VISUAL_BLUEPRINT_FIELDS:
            if _is_empty_value(getattr(self, field_name)):
                raise ValueError(f"visual_blueprint.{field_name} is required and cannot be empty")
        _ensure_prompt_contains(
            self.image_prompt,
            "visual_blueprint.image_prompt",
            IMAGE_PROMPT_SIGNAL_GROUPS,
        )
        _ensure_prompt_contains(
            self.video_prompt,
            "visual_blueprint.video_prompt",
            VIDEO_PROMPT_SIGNAL_GROUPS,
        )
        return self


class VisualBlueprintDocument(BaseModel):
    model_config = ConfigDict(extra="allow")

    visual_blueprint: VisualBlueprint


REQUIRED_VISUAL_BLUEPRINT_FIELDS = (
    "brand",
    "scene",
    "camera",
    "lighting",
    "composition",
    "avatar",
    "product",
    "subtitle",
    "overlay",
    "music",
    "transition",
    "image_prompt",
    "video_prompt",
    "asset_mapping",
    "obs_layers",
    "director_note",
)

IMAGE_PROMPT_SIGNAL_GROUPS = (
    ("photography", "摄影", "lens", "镜头", "camera", "shot", "景别"),
    ("lighting", "light", "灯光", "光线"),
    ("material", "材质", "brand", "品牌", "style", "风格"),
)

VIDEO_PROMPT_SIGNAL_GROUPS = (
    ("camera movement", "camera", "movement", "motion", "镜头运动", "运镜", "推镜", "dolly"),
    ("lighting", "light", "灯光", "光线"),
    ("scene", "场景"),
    ("duration", "seconds", "时长", "秒"),
)


@dataclass(slots=True)
class VisualDirectorInput:
    story: str = ""
    script: str = ""
    director_script: str = ""
    brand: str = ""
    product: str = ""
    audience: str = ""
    emotion: str = ""
    live_goal: str = ""
    platform: str = ""
    scene: str = ""
    current_assets: dict[str, Any] = field(default_factory=dict)
    runtime_context: dict[str, Any] = field(default_factory=dict)


class VisualDirector:
    def __init__(self, chat_model: BaseChatModel):
        self.chat_model = chat_model

    @retry(stop=stop_after_attempt(3), after=after_func)
    async def create_visual_blueprint(
        self,
        payload: VisualDirectorInput | dict[str, Any],
        retry_timeout: int = 150,
    ) -> str:
        data = payload if isinstance(payload, VisualDirectorInput) else VisualDirectorInput(**payload)
        messages = [
            SystemMessage(content=system_prompt_template_visual_director),
            HumanMessage(content=_format_visual_director_input(data)),
        ]
        response = await asyncio.wait_for(self.chat_model.ainvoke(messages), timeout=retry_timeout)
        content = getattr(response, "content", response)
        if isinstance(content, list):
            content = "\n".join(str(item) for item in content)
        output = str(content).strip()
        validate_visual_blueprint_output(output)
        return output

    async def create_visual_blueprint_model(
        self,
        payload: VisualDirectorInput | dict[str, Any],
        retry_timeout: int = 150,
    ) -> VisualBlueprintDocument:
        output = await self.create_visual_blueprint(payload, retry_timeout=retry_timeout)
        return parse_visual_blueprint_output(output)


# Backwards-compatible callable alias for code paths that instantiate agents by class name.
VisualDirectorAgent = VisualDirector


def strip_markdown_fence(text: str) -> str:
    content = str(text or "").strip()
    match = re.fullmatch(r"```(?:yaml|yml|json)?\s*(.*?)\s*```", content, flags=re.IGNORECASE | re.DOTALL)
    return match.group(1).strip() if match else content


def parse_visual_blueprint_output(text: str) -> VisualBlueprintDocument:
    content = strip_markdown_fence(text)
    payload: Any
    try:
        payload = yaml.safe_load(content)
    except yaml.YAMLError:
        try:
            payload = json.loads(content)
        except json.JSONDecodeError as exc:
            raise VisualBlueprintValidationError(f"visual_blueprint output is not valid YAML or JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise VisualBlueprintValidationError("visual_blueprint output must parse to an object")
    if "visual_blueprint" not in payload:
        raise VisualBlueprintValidationError("missing required root key: visual_blueprint")
    try:
        return VisualBlueprintDocument.model_validate(payload)
    except ValidationError as exc:
        raise VisualBlueprintValidationError(f"visual_blueprint schema validation failed: {exc}") from exc


def validate_visual_blueprint_output(text: str) -> VisualBlueprintDocument:
    return parse_visual_blueprint_output(text)


def _is_empty_value(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, (list, tuple, set, dict)):
        return len(value) == 0
    return False


def _ensure_prompt_contains(prompt: str, field_name: str, signal_groups: tuple[tuple[str, ...], ...]) -> None:
    normalized = str(prompt or "").lower()
    if len(normalized.strip()) < 24:
        raise ValueError(f"{field_name} is too short to be executable")
    missing_groups: list[str] = []
    for group in signal_groups:
        if not any(signal.lower() in normalized for signal in group):
            missing_groups.append("/".join(group[:3]))
    if missing_groups:
        raise ValueError(f"{field_name} is incomplete; missing signal groups: {', '.join(missing_groups)}")


def _format_visual_director_input(data: VisualDirectorInput) -> str:
    return f"""
<STORY>
{data.story.strip()}
</STORY>

<SCRIPT>
{data.script.strip()}
</SCRIPT>

<DIRECTOR_SCRIPT>
{data.director_script.strip()}
</DIRECTOR_SCRIPT>

<BRAND>
{data.brand.strip()}
</BRAND>

<PRODUCT>
{data.product.strip()}
</PRODUCT>

<AUDIENCE>
{data.audience.strip()}
</AUDIENCE>

<EMOTION>
{data.emotion.strip()}
</EMOTION>

<LIVE_GOAL>
{data.live_goal.strip()}
</LIVE_GOAL>

<PLATFORM>
{data.platform.strip()}
</PLATFORM>

<SCENE>
{data.scene.strip()}
</SCENE>

<CURRENT_ASSETS>
{data.current_assets}
</CURRENT_ASSETS>

<RUNTIME_CONTEXT>
{data.runtime_context}
</RUNTIME_CONTEXT>
""".strip()
