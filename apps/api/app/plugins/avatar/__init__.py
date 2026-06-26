from __future__ import annotations

from apps.api.app.plugins.base import NotInstalledPlugin


class LiveTalkingAvatarProvider(NotInstalledPlugin):
    def __init__(self, repo_url: str = "https://github.com/lipku/LiveTalking", commit: str = "", license: str = "check_before_commercial_use", adapter: str = "apps/api/app/plugins/avatar") -> None:
        super().__init__(
            "livetalking",
            "avatar",
            repo_url,
            ("realtime_avatar", "audio_drive"),
            display_name="LiveTalking Adapter",
            commit=commit,
            license=license,
            adapter=adapter,
            metadata={"integration": "wrapper_candidate"},
        )


class MuseTalkAvatarProvider(NotInstalledPlugin):
    def __init__(self, repo_url: str = "https://github.com/TMElyralab/MuseTalk", commit: str = "", license: str = "check_before_commercial_use", adapter: str = "apps/api/app/plugins/avatar") -> None:
        super().__init__(
            "musetalk",
            "avatar",
            repo_url,
            ("audio_drive", "lip_sync"),
            display_name="MuseTalk Adapter",
            commit=commit,
            license=license,
            adapter=adapter,
            metadata={"integration": "wrapper_candidate"},
        )


class SadTalkerAvatarProvider(NotInstalledPlugin):
    def __init__(self, repo_url: str = "https://github.com/OpenTalker/SadTalker", commit: str = "", license: str = "check_before_commercial_use", adapter: str = "apps/api/app/plugins/avatar") -> None:
        super().__init__(
            "sadtalker",
            "avatar",
            repo_url,
            ("talking_head",),
            display_name="SadTalker Adapter",
            commit=commit,
            license=license,
            adapter=adapter,
            metadata={"integration": "wrapper_candidate"},
        )
