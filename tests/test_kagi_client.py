import json
import unittest
from unittest import mock


class FakeHTTPResponse:
    def __init__(self, body: str, code: int = 200):
        self._body = body.encode("utf-8")
        self.code = code

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class TestKagiClient(unittest.TestCase):
    def setUp(self):
        # Import inside tests so env mocking is easy.
        import importlib

        self.kagi_client = importlib.import_module("scripts.kagi_client")

    def test_missing_token_raises(self):
        with mock.patch.dict("os.environ", {}, clear=True):
            with self.assertRaises(self.kagi_client.KagiError):
                self.kagi_client.search("test")

    def test_search_builds_url_and_header(self):
        with mock.patch.dict("os.environ", {"KAGI_API_TOKEN": "tok"}, clear=True):
            with mock.patch("urllib.request.urlopen") as urlopen:
                urlopen.return_value = FakeHTTPResponse(json.dumps({"meta": {}, "data": []}))
                self.kagi_client.search("steve jobs")

                req = urlopen.call_args[0][0]
                self.assertIn("https://kagi.com/api/v0/search?", req.full_url)
                self.assertIn("q=steve+jobs", req.full_url)
                self.assertEqual(req.headers.get("Authorization"), "Bot tok")

    def test_fastgpt_posts_json(self):
        with mock.patch.dict("os.environ", {"KAGI_API_TOKEN": "tok"}, clear=True):
            with mock.patch("urllib.request.urlopen") as urlopen:
                urlopen.return_value = FakeHTTPResponse(json.dumps({"meta": {}, "data": {"output": "ok"}}))
                self.kagi_client.fastgpt("hello", cache=False)

                req = urlopen.call_args[0][0]
                self.assertEqual(req.method, "POST")
                self.assertIn("/fastgpt", req.full_url)
                # urllib lowercases/normalizes header keys internally
                self.assertIn(req.get_header("Content-type"), ("application/json", "application/json; charset=utf-8"))

    def test_non_json_response_raises(self):
        with mock.patch.dict("os.environ", {"KAGI_API_TOKEN": "tok"}, clear=True):
            with mock.patch("urllib.request.urlopen") as urlopen:
                urlopen.return_value = FakeHTTPResponse("<html>nope</html>")
                with self.assertRaises(self.kagi_client.KagiError):
                    self.kagi_client.search("x")


if __name__ == "__main__":
    unittest.main()
