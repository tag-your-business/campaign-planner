"""Unit tests for ImageService — all OpenAI and httpx calls are mocked."""

from unittest.mock import MagicMock, patch

import pytest
from app.features.generation.image import ImageService

FAKE_PROMPT = "A bright dental clinic celebrating World Oral Health Day"
FAKE_IMAGE_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100  # minimal fake PNG bytes
FAKE_URL = "https://oaidalleapi.blob.core.windows.net/generated/img001.png"


def _make_openai_response(url: str = FAKE_URL) -> MagicMock:
    return MagicMock(data=[MagicMock(url=url)])


@pytest.fixture
def mock_openai():
    with patch("app.features.generation.image.OpenAI") as MockCls:
        client = MagicMock()
        MockCls.return_value = client
        client.images.generate.return_value = _make_openai_response()
        yield client


@pytest.fixture
def mock_httpx_get():
    with patch("app.features.generation.image.httpx.get") as mock_get:
        mock_get.return_value = MagicMock(content=FAKE_IMAGE_BYTES)
        yield mock_get


# ---------------------------------------------------------------------------
# Happy-path tests
# ---------------------------------------------------------------------------


class TestImageServiceSuccess:
    def test_generate_returns_output_path(self, mock_openai, mock_httpx_get, tmp_path):
        svc = ImageService()
        out = tmp_path / "img.png"
        result = svc.generate(FAKE_PROMPT, out)
        assert result == out

    def test_generate_writes_image_bytes(self, mock_openai, mock_httpx_get, tmp_path):
        svc = ImageService()
        out = tmp_path / "img.png"
        svc.generate(FAKE_PROMPT, out)
        assert out.exists()
        assert out.read_bytes() == FAKE_IMAGE_BYTES

    def test_generate_creates_parent_dirs(self, mock_openai, mock_httpx_get, tmp_path):
        svc = ImageService()
        out = tmp_path / "nested" / "deep" / "img.png"
        svc.generate(FAKE_PROMPT, out)
        assert out.exists()

    def test_generate_calls_dalle_once(self, mock_openai, mock_httpx_get, tmp_path):
        svc = ImageService()
        svc.generate(FAKE_PROMPT, tmp_path / "img.png")
        mock_openai.images.generate.assert_called_once()

    def test_generate_downloads_from_correct_url(
        self, mock_openai, mock_httpx_get, tmp_path
    ):
        svc = ImageService()
        svc.generate(FAKE_PROMPT, tmp_path / "img.png")
        mock_httpx_get.assert_called_once_with(FAKE_URL)

    def test_generate_passes_prompt_to_dalle(
        self, mock_openai, mock_httpx_get, tmp_path
    ):
        svc = ImageService()
        svc.generate(FAKE_PROMPT, tmp_path / "img.png")
        kwargs = mock_openai.images.generate.call_args.kwargs
        assert kwargs["prompt"] == FAKE_PROMPT

    def test_generate_requests_1024x1024(self, mock_openai, mock_httpx_get, tmp_path):
        svc = ImageService()
        svc.generate(FAKE_PROMPT, tmp_path / "img.png")
        kwargs = mock_openai.images.generate.call_args.kwargs
        assert kwargs["size"] == "1024x1024"

    def test_generate_requests_n_equals_1(self, mock_openai, mock_httpx_get, tmp_path):
        svc = ImageService()
        svc.generate(FAKE_PROMPT, tmp_path / "img.png")
        kwargs = mock_openai.images.generate.call_args.kwargs
        assert kwargs["n"] == 1

    def test_generate_specifies_model(self, mock_openai, mock_httpx_get, tmp_path):
        svc = ImageService()
        svc.generate(FAKE_PROMPT, tmp_path / "img.png")
        kwargs = mock_openai.images.generate.call_args.kwargs
        assert "model" in kwargs
        assert len(kwargs["model"]) > 0


# ---------------------------------------------------------------------------
# Retry / error-handling tests
# ---------------------------------------------------------------------------


class TestImageServiceRetry:
    def test_raises_on_persistent_dalle_error(
        self, mock_openai, mock_httpx_get, tmp_path
    ):
        mock_openai.images.generate.side_effect = Exception("DALL-E quota exceeded")
        svc = ImageService()
        with pytest.raises(Exception, match="DALL-E quota exceeded"):
            svc.generate(FAKE_PROMPT, tmp_path / "img.png")

    def test_exhausts_all_three_attempts_on_dalle_error(
        self, mock_openai, mock_httpx_get, tmp_path
    ):
        mock_openai.images.generate.side_effect = Exception("API error")
        svc = ImageService()
        with pytest.raises(Exception):
            svc.generate(FAKE_PROMPT, tmp_path / "img.png")
        assert mock_openai.images.generate.call_count == 3

    def test_succeeds_on_second_attempt(self, mock_openai, mock_httpx_get, tmp_path):
        mock_openai.images.generate.side_effect = [
            Exception("Transient error"),
            _make_openai_response(),
        ]
        svc = ImageService()
        result = svc.generate(FAKE_PROMPT, tmp_path / "img.png")
        assert result == tmp_path / "img.png"
        assert mock_openai.images.generate.call_count == 2

    def test_raises_on_persistent_httpx_error(
        self, mock_openai, mock_httpx_get, tmp_path
    ):
        mock_httpx_get.side_effect = Exception("Network error")
        svc = ImageService()
        with pytest.raises(Exception, match="Network error"):
            svc.generate(FAKE_PROMPT, tmp_path / "img.png")

    def test_exhausts_all_three_attempts_on_httpx_error(
        self, mock_openai, mock_httpx_get, tmp_path
    ):
        mock_httpx_get.side_effect = Exception("Download failed")
        svc = ImageService()
        with pytest.raises(Exception):
            svc.generate(FAKE_PROMPT, tmp_path / "img.png")
        assert mock_httpx_get.call_count == 3

    def test_succeeds_on_second_attempt_after_download_error(
        self, mock_openai, mock_httpx_get, tmp_path
    ):
        mock_httpx_get.side_effect = [
            Exception("Timeout"),
            MagicMock(content=FAKE_IMAGE_BYTES),
        ]
        svc = ImageService()
        svc.generate(FAKE_PROMPT, tmp_path / "img.png")
        assert (tmp_path / "img.png").read_bytes() == FAKE_IMAGE_BYTES

    def test_does_not_write_file_when_download_fails(
        self, mock_openai, mock_httpx_get, tmp_path
    ):
        mock_httpx_get.side_effect = Exception("All retries failed")
        svc = ImageService()
        out = tmp_path / "img.png"
        with pytest.raises(Exception):
            svc.generate(FAKE_PROMPT, out)
        assert not out.exists()
