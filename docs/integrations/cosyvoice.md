# CosyVoice TTS 集成

Tavern 通过 `cosyvoice_tts` plugin 接入 CosyVoice。CosyVoice 模型仓库、权重和 GPU 运行时不放入 Tavern 业务代码；Tavern 只调用外部 HTTP 服务并保存返回的音频 artifact。

## 上游资源

- Official repo: https://github.com/FunAudioLLM/CosyVoice
- FastAPI server: https://github.com/FunAudioLLM/CosyVoice/blob/main/runtime/python/fastapi/server.py
- FastAPI client: https://github.com/FunAudioLLM/CosyVoice/blob/main/runtime/python/fastapi/client.py
- CosyVoice2 examples: https://github.com/FunAudioLLM/CosyVoice/blob/main/example.py
- CosyVoice2-0.5B model card: https://huggingface.co/FunAudioLLM/CosyVoice2-0.5B

## Tavern 配置

本地 Docker 默认会优先尝试 CosyVoice，并在未配置或不可用时回退到 `edge_tts` / 占位 URI：

```env
TAVERN_MVP_TTS_PROVIDER=cosyvoice_tts
TAVERN_TTS_FALLBACK_PROVIDER=edge_tts
TAVERN_COSYVOICE_BASE_URL=http://host.docker.internal:50000
TAVERN_COSYVOICE_HEALTH_PATH=
TAVERN_COSYVOICE_SPEECH_PATH=/v1/audio/speech
TAVERN_COSYVOICE_MODEL=CosyVoice2-0.5B
TAVERN_COSYVOICE_VOICE=中文女声
TAVERN_COSYVOICE_FORMAT=wav
TAVERN_COSYVOICE_TIMEOUT_SECONDS=120
TAVERN_TTS_OUTPUT_DIR=.working_dir/artifacts/tts
```

如果使用 CosyVoice 官方 FastAPI runtime，可以把 `TAVERN_COSYVOICE_SPEECH_PATH` 设置为官方 endpoint，例如：

```env
TAVERN_COSYVOICE_SPEECH_PATH=/inference_sft
```

官方 FastAPI endpoint 返回 raw PCM 时，Tavern 会按 `TAVERN_COSYVOICE_SAMPLE_RATE`，默认 `24000`，封装为 WAV 文件。

## 验证

查看 provider：

```powershell
curl http://127.0.0.1:8770/api/v1/plugins/providers?category=tts
```

查看健康状态：

```powershell
curl http://127.0.0.1:8770/api/v1/plugins/providers/cosyvoice_tts/health
```

直接提交 TTS job：

```powershell
curl -X POST http://127.0.0.1:8770/api/v1/plugins/providers/cosyvoice_tts/jobs `
  -H "Content-Type: application/json" `
  -d "{\"text\":\"欢迎来到直播间\",\"plan_id\":\"manual\"}"
```

跑 MVP：

```powershell
curl -X POST http://127.0.0.1:8770/api/v1/mvp/live-plans/run `
  -H "Content-Type: application/json" `
  -d "{}"
```

CosyVoice 成功时，返回的 `plan.speech_artifact_uri` 会指向 `.working_dir/artifacts/tts/...` 下的音频文件；不可用时，MVP 会继续回退并保存直播方案。

## 注意

CosyVoice 代码和模型权重的商用许可需要在真实商用前单独确认。Tavern 的 `third_party/manifest.json` 只记录外部集成候选，不表示已完成授权审查。
