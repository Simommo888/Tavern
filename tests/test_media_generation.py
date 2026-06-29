import unittest
from unittest.mock import Mock, patch

from apps.api.app.infrastructure.media_generation import JimengVideoClient


class MediaGenerationTests(unittest.TestCase):
    def test_jimeng_client_supports_bearer_submit_and_poll(self):
        submit_response = Mock()
        submit_response.status_code = 200
        submit_response.json.return_value = {"data": {"task_id": "task-123"}}
        result_response = Mock()
        result_response.status_code = 200
        result_response.json.return_value = {"data": {"status": "done", "video_url": "https://example.com/out.mp4"}}

        with patch("apps.api.app.infrastructure.media_generation.requests.post", side_effect=[submit_response, result_response]) as post:
            client = JimengVideoClient(
                api_key="bearer-key",
                base_url="https://visual.volcengineapi.com",
                req_key="jimeng_t2v_v30",
                submit_action="CVSync2AsyncSubmitTask",
                result_action="CVSync2AsyncGetResult",
                api_version="2022-08-31",
                timeout_seconds=30,
                poll_interval_seconds=0,
                max_poll_attempts=1,
            )
            task_id = client.submit_task(prompt="测试视频", aspect_ratio="9:16", duration_seconds=5, fps=24)
            video_url, payload = client.poll_result(task_id)

        self.assertEqual(task_id, "task-123")
        self.assertEqual(video_url, "https://example.com/out.mp4")
        self.assertEqual(payload["data"]["status"], "done")
        self.assertIn("Action=CVSync2AsyncSubmitTask", post.call_args_list[0].args[0])
        self.assertEqual(post.call_args_list[0].kwargs["headers"]["Authorization"], "Bearer bearer-key")
        self.assertEqual(post.call_args_list[0].kwargs["headers"]["Content-Type"], "application/json")

    def test_jimeng_client_supports_volcengine_hmac_headers(self):
        response = Mock()
        response.status_code = 200
        response.json.return_value = {"Result": {"task_id": "task-hmac"}}

        with patch("apps.api.app.infrastructure.media_generation.requests.post", return_value=response) as post:
            client = JimengVideoClient(
                api_key="",
                base_url="https://visual.volcengineapi.com",
                req_key="jimeng_t2v_v30",
                submit_action="CVSync2AsyncSubmitTask",
                result_action="CVSync2AsyncGetResult",
                api_version="2022-08-31",
                timeout_seconds=30,
                poll_interval_seconds=0,
                max_poll_attempts=1,
                access_key="ak-test",
                secret_key="sk-test",
            )
            task_id = client.submit_task(prompt="测试视频", aspect_ratio="16:9", duration_seconds=5, fps=24)

        headers = post.call_args.kwargs["headers"]
        self.assertEqual(task_id, "task-hmac")
        self.assertTrue(headers["Authorization"].startswith("HMAC-SHA256 Credential=ak-test/"))
        self.assertIn("SignedHeaders=content-type;host;x-content-sha256;x-date", headers["Authorization"])
        self.assertIn("X-Content-Sha256", headers)
        self.assertIn("X-Date", headers)


if __name__ == "__main__":
    unittest.main()
