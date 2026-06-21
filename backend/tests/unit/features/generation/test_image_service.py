"""Unit tests for ImageService — all OpenAI calls are mocked."""

import base64
from unittest.mock import MagicMock, patch

import pytest
from app.features.generation.image import ImageService

FAKE_PROMPT = "A bright dental clinic celebrating World Oral Health Day"
FAKE_IMAGE_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
FAKE_B64 = base64.b64encode(FAKE_IMAGE_BYTES).decode()


def _make_openai_response(b64: str = FAKE_B64) -> MagicMock:
    return MagicMock(data=[MagicMock(b64_json=b64)])


@pytest.fixture(autouse=True)
def disable_fallback_image():
    """Always test the real API path regardless of .env settings."""
    with patch("app.features.generation.image.settings") as mock_settings:
        mock_settings.use_fallback_image = False
        mock_settings.openai_api_key = "test-key"
        mock_settings.openai_image_model = "gpt-image-2"
        mock_settings.openai_image_size = "1024x1024"
        mock_settings.openai_image_quality = "medium"
        yield mock_settings


@pytest.fixture
def mock_openai():
    with patch("app.features.generation.image.OpenAI") as MockCls:
        client = MagicMock()
        MockCls.return_value = client
        client.images.generate.return_value = _make_openai_response()
        yield client


# ---------------------------------------------------------------------------
# Happy-path tests
# ---------------------------------------------------------------------------


class TestImageServiceSuccess:
    def test_generate_returns_output_path(self, mock_openai, tmp_path):
        svc = ImageService()
        out = tmp_path / "img.png"
        result = svc.generate(FAKE_PROMPT, out)
        assert result == out

    def test_generate_writes_image_bytes(self, mock_openai, tmp_path):
        svc = ImageService()
        out = tmp_path / "img.png"
        svc.generate(FAKE_PROMPT, out)
        assert out.exists()
        assert out.read_bytes() == FAKE_IMAGE_BYTES

    def test_generate_creates_parent_dirs(self, mock_openai, tmp_path):
        svc = ImageService()
        out = tmp_path / "nested" / "deep" / "img.png"
        svc.generate(FAKE_PROMPT, out)
        assert out.exists()

    def test_generate_calls_api_once(self, mock_openai, tmp_path):
        svc = ImageService()
        svc.generate(FAKE_PROMPT, tmp_path / "img.png")
        mock_openai.images.generate.assert_called_once()

    def test_generate_decodes_b64_from_response(self, mock_openai, tmp_path):
        custom_bytes = b"custom image data"
        custom_b64 = base64.b64encode(custom_bytes).decode()
        mock_openai.images.generate.return_value = _make_openai_response(custom_b64)
        svc = ImageService()
        out = tmp_path / "img.png"
        svc.generate(FAKE_PROMPT, out)
        assert out.read_bytes() == custom_bytes

    def test_generate_passes_prompt_to_api(self, mock_openai, tmp_path):
        svc = ImageService()
        svc.generate(FAKE_PROMPT, tmp_path / "img.png")
        kwargs = mock_openai.images.generate.call_args.kwargs
        assert kwargs["prompt"] == FAKE_PROMPT

    def test_generate_requests_1024x1024(self, mock_openai, tmp_path):
        svc = ImageService()
        svc.generate(FAKE_PROMPT, tmp_path / "img.png")
        kwargs = mock_openai.images.generate.call_args.kwargs
        assert kwargs["size"] == "1024x1024"
        assert kwargs["quality"] == "medium"
        assert "response_format" not in kwargs

    def test_generate_requests_n_equals_1(self, mock_openai, tmp_path):
        svc = ImageService()
        svc.generate(FAKE_PROMPT, tmp_path / "img.png")
        kwargs = mock_openai.images.generate.call_args.kwargs
        assert kwargs["n"] == 1

    def test_generate_specifies_model(self, mock_openai, tmp_path):
        svc = ImageService()
        svc.generate(FAKE_PROMPT, tmp_path / "img.png")
        kwargs = mock_openai.images.generate.call_args.kwargs
        assert kwargs["model"] == "gpt-image-2"


# ---------------------------------------------------------------------------
# Retry / error-handling tests
# ---------------------------------------------------------------------------


class TestImageServiceRetry:
    def test_raises_on_persistent_api_error(self, mock_openai, tmp_path):
        mock_openai.images.generate.side_effect = Exception("quota exceeded")
        svc = ImageService()
        with pytest.raises(Exception, match="quota exceeded"):
            svc.generate(FAKE_PROMPT, tmp_path / "img.png")

    def test_exhausts_all_three_attempts_on_api_error(self, mock_openai, tmp_path):
        mock_openai.images.generate.side_effect = Exception("API error")
        svc = ImageService()
        with pytest.raises(Exception):
            svc.generate(FAKE_PROMPT, tmp_path / "img.png")
        assert mock_openai.images.generate.call_count == 3

    def test_succeeds_on_second_attempt(self, mock_openai, tmp_path):
        mock_openai.images.generate.side_effect = [
            Exception("Transient error"),
            _make_openai_response(),
        ]
        svc = ImageService()
        result = svc.generate(FAKE_PROMPT, tmp_path / "img.png")
        assert result == tmp_path / "img.png"
        assert mock_openai.images.generate.call_count == 2

    def test_raises_when_b64_json_is_none(self, mock_openai, tmp_path):
        mock_openai.images.generate.return_value = MagicMock(
            data=[MagicMock(b64_json=None)]
        )
        svc = ImageService()
        with pytest.raises(Exception):
            svc.generate(FAKE_PROMPT, tmp_path / "img.png")

    def test_does_not_write_file_on_api_error(self, mock_openai, tmp_path):
        mock_openai.images.generate.side_effect = Exception("All retries failed")
        svc = ImageService()
        out = tmp_path / "img.png"
        with pytest.raises(Exception):
            svc.generate(FAKE_PROMPT, out)
        assert not out.exists()
