from __future__ import annotations

from apps.api.app.domain.live.entities import AnchorReply, SpeechArtifact
from apps.api.app.infrastructure.repositories.file_live import FileLiveRoomRepository
from agent_runtime.speech_tts import synthesize_speech


class SpeechService:
    def __init__(self, repository: FileLiveRoomRepository) -> None:
        self.repository = repository

    async def create_speech_artifact(self, reply: AnchorReply) -> SpeechArtifact:
        speech = SpeechArtifact(session_id=reply.session_id, reply_id=reply.reply_id, text=reply.text)
        output_dir = self.repository.speech_output_dir(reply.session_id)
        path, mime_type, provider = await synthesize_speech(reply.text, output_dir, speech.artifact_id)
        speech.audio_path = self.repository.relative_speech_path(reply.session_id, path)
        speech.mime_type = mime_type
        speech.provider = provider
        self.repository.save_speech_artifact(speech)
        return speech
