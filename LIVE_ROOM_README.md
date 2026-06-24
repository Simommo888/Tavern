# Tavern 实时互动直播间 MVP

这个 MVP 把 Tavern 从“离线生成视频”扩展为一个前后端分离的实时互动直播间系统。

## 后端启动

```powershell
$env:PYTHONPATH = "D:\Tavern"
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
uv run --project "D:\Tavern" --directory "D:\Tavern" python main_live_api.py
```

默认地址：

```text
http://127.0.0.1:8765
```

主要接口：

- `GET /health`
- `POST /api/live/sessions`
- `GET /api/live/sessions/{session_id}`
- `POST /api/live/sessions/{session_id}/events`
- `GET /api/live/sessions/{session_id}/events/stream`
- `POST /api/live/sessions/{session_id}/stop`

## 前端启动

```powershell
cd D:\Tavern\web
npm install
npm run dev
```

默认地址：

```text
http://127.0.0.1:5173
```

前端默认连接后端：

```text
http://127.0.0.1:8765
```

如需修改：

```powershell
$env:VITE_API_BASE = "http://127.0.0.1:8765"
```

## TTS 配置

默认真实 TTS：

```powershell
$env:TAVERN_TTS_PROVIDER = "edge"
$env:TAVERN_EDGE_TTS_VOICE = "zh-CN-XiaoxiaoNeural"
```

Windows 本地 SAPI TTS（无需外网）：

```powershell
$env:TAVERN_TTS_PROVIDER = "sapi"
$env:TAVERN_SAPI_RATE = "0"
$env:TAVERN_SAPI_VOLUME = "100"
```

OpenAI-compatible TTS：

```powershell
$env:TAVERN_TTS_PROVIDER = "openai"
$env:TAVERN_TTS_BASE_URL = "https://gpt.xinshu.ai/v1"
$env:TAVERN_TTS_MODEL = "tts-1"
$env:TAVERN_TTS_VOICE = "alloy"
```

离线/测试回退占位音频：

```powershell
$env:TAVERN_TTS_PROVIDER = "placeholder"
```

## OBS 输出

1. 启动后端和前端。
2. 在 Web 控制台创建直播间，复制 session id。
3. 在 OBS 里添加 Browser Source，URL 填：

```text
http://127.0.0.1:5173/obs?session_id=<你的session_id>
```

建议尺寸：

```text
1920x1080
```

OBS 页面会连接 SSE 事件流，收到主播回复后播放后端 TTS 音频，并显示直播画面和字幕。若浏览器自动播放被拦截，请在 OBS Browser Source 交互模式里点击页面一次解锁音频。

## 当前能力

- 创建直播间 session
- 配置商品信息
- 模拟观众弹幕/问题
- GPT-5.5 生成主播口播回复
- 酒类合规规则检查与改写
- SSE 事件流
- 最新 speech payload API：`GET /api/live/sessions/{session_id}/speech/latest`
- 后端 speech artifact 音频端点：`GET /api/live/sessions/{session_id}/speech/{artifact_id}/audio`
- 默认使用 `edge-tts` 生成真实中文 MP3；失败或 `TAVERN_TTS_PROVIDER=placeholder` 时回退到静音 WAV 占位
- Web 控制台展示状态、回复和事件日志
- 前端优先播放后端 speech artifact 音频，失败时 fallback 到浏览器 Web Speech API 自动播报/重播主播回复

## 后续扩展

- 接入真实电商平台弹幕
- 接入 TTS
- 接入 HeyGen Streaming / Live2D / OBS
- 增加商品知识库和库存/优惠实时同步
- 增加直播表现数据回流和复盘
