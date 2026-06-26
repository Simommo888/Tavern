# Tavern third_party

Tavern LiveOS 优先复用成熟开源项目，但第三方项目必须通过插件边界接入，不能把业务逻辑写进第三方目录。

## Rules

- 每个项目放在 `third_party/<project-name>/`。
- 每次拉取后在 `manifest.json` 记录 repo URL、commit、license、用途和接入状态。
- 后端只通过 `apps/api/app/plugins/**` 适配器调用第三方能力。
- 第一阶段只拉 MVP 主链路需要的项目，避免无目的引入大模型仓库。

## Current candidates

- Fish Speech：TTS / 声音克隆。
- LiveTalking：实时数字人 / 音频驱动口型。
- MuseTalk：音频驱动口型同步。
- SadTalker：Talking head 视频生成。
- FFmpeg / MoviePy：视频合成与转码，当前优先使用已有依赖封装。
