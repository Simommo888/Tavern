import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from utils import ffmpeg_cli


class FfmpegCliTests(unittest.TestCase):
    def test_concat_clips_builds_argv_without_shell(self):
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "clip one.mp4"
            input_path.write_bytes(b"clip")
            output_path = Path(tmp) / "out.mp4"

            class Completed:
                returncode = 0
                stdout = ""
                stderr = ""

            with patch("utils.ffmpeg_cli.shutil.which", return_value="C:/ffmpeg/bin/ffmpeg.exe"), patch("utils.ffmpeg_cli.subprocess.run", return_value=Completed()) as run:
                result = ffmpeg_cli.concat_clips([input_path], output_path)
            self.assertIn("-f", result.argv)
            self.assertFalse(run.call_args.kwargs["shell"])
            self.assertTrue(output_path.with_suffix(".concat.txt").exists())

    def test_missing_binary_has_clear_error(self):
        with patch("utils.ffmpeg_cli.shutil.which", return_value=None):
            with self.assertRaises(FileNotFoundError):
                ffmpeg_cli.resolve_ffmpeg()


if __name__ == "__main__":
    unittest.main()
