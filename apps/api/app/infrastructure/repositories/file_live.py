from __future__ import annotations

from pathlib import Path
from typing import Any

from apps.api.app.domain.live.entities import LiveRoomEventRecord, LiveRoomSession, SpeechArtifact


class FileLiveRoomRepository:
    def __init__(self, workspace_root: str | Path = ".") -> None:
        self.workspace_root = Path(workspace_root).resolve()
        self.store_dir = self.workspace_root / ".working_dir" / "live_rooms"
        self.store_dir.mkdir(parents=True, exist_ok=True)

    def save_session(self, session: LiveRoomSession) -> None:
        path = self._session_path(session.session_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(session.model_dump_json(indent=2), encoding="utf-8")

    def get_session(self, session_id: str) -> LiveRoomSession:
        path = self._session_path(session_id)
        if not path.exists():
            raise KeyError(f"Unknown live room session: {session_id}")
        return LiveRoomSession.model_validate_json(path.read_text(encoding="utf-8"))

    def append_event(self, session_id: str, event_type: str, payload: dict[str, Any]) -> LiveRoomEventRecord:
        record = LiveRoomEventRecord(type=event_type, session_id=session_id, payload=payload)
        path = self._events_path(session_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(record.model_dump_json() + "\n")
        return record

    def events(self, session_id: str) -> list[LiveRoomEventRecord]:
        path = self._events_path(session_id)
        if not path.exists():
            return []
        rows = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rows.append(LiveRoomEventRecord.model_validate_json(line))
        return rows

    def save_speech_artifact(self, speech: SpeechArtifact) -> None:
        path = self._speech_meta_path(speech.session_id, speech.artifact_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(speech.model_dump_json(indent=2), encoding="utf-8")

    def get_speech_artifact(self, session_id: str, artifact_id: str) -> SpeechArtifact:
        path = self._speech_meta_path(session_id, artifact_id)
        if not path.exists():
            raise KeyError(f"Unknown speech artifact: {artifact_id}")
        return SpeechArtifact.model_validate_json(path.read_text(encoding="utf-8"))

    def speech_audio_path(self, session_id: str, artifact_id: str) -> Path:
        speech = self.get_speech_artifact(session_id, artifact_id)
        path = (self.store_dir / session_id / speech.audio_path).resolve()
        if self.store_dir.resolve() not in path.parents:
            raise ValueError("Speech audio path escapes live room store")
        return path

    def speech_output_dir(self, session_id: str) -> Path:
        return self.store_dir / session_id / "speech"

    def relative_speech_path(self, session_id: str, path: Path) -> str:
        return str(path.relative_to(self.store_dir / session_id)).replace("\\", "/")

    def _session_path(self, session_id: str) -> Path:
        return self.store_dir / session_id / "session.json"

    def _events_path(self, session_id: str) -> Path:
        return self.store_dir / session_id / "events.jsonl"

    def _speech_meta_path(self, session_id: str, artifact_id: str) -> Path:
        return self.store_dir / session_id / "speech" / f"{artifact_id}.json"
