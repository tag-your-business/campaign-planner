"""Unit tests for OpenAIProvider."""

from unittest.mock import MagicMock, patch

import pytest
from app.common.ai_providers import Message, TextGenerationRequest
from app.common.ai_providers.providers import OpenAIProvider


class TestOpenAIProvider:
    """Tests for OpenAI provider — Responses API path (primary: gpt-5.4-mini)."""

    def test_initialization(self):
        """Test provider initialization."""
        provider = OpenAIProvider(api_key="sk-test123", model="gpt-5.4-mini")

        assert provider.api_key == "sk-test123"
        assert provider.model == "gpt-5.4-mini"
        assert provider.client is not None

    @patch("app.common.ai_providers.providers.openai_provider.OpenAI")
    def test_generate_success(self, mock_openai_class):
        """Test successful text generation via Responses API (gpt-5.4-mini)."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.output_text = "Generated caption"
        mock_response.usage.input_tokens = 50
        mock_response.usage.output_tokens = 20

        mock_client.responses.create.return_value = mock_response

        provider = OpenAIProvider(api_key="sk-test123", model="gpt-5.4-mini")
        request = TextGenerationRequest(
            messages=[
                Message(role="system", content="You are helpful."),
                Message(role="user", content="Hello!"),
            ],
            temperature=0.7,
            max_tokens=100,
        )

        response = provider.generate(request)

        assert response.text == "Generated caption"
        assert response.provider == "openai"
        assert response.model == "gpt-5.4-mini"
        assert response.usage["prompt_tokens"] == 50
        assert response.usage["completion_tokens"] == 20
        assert response.usage["total_tokens"] == 70

        mock_client.responses.create.assert_called_once()
        call_kwargs = mock_client.responses.create.call_args[1]
        assert call_kwargs["model"] == "gpt-5.4-mini"
        assert call_kwargs["max_output_tokens"] == 100
        assert "messages" not in call_kwargs

    @patch("app.common.ai_providers.providers.openai_provider.OpenAI")
    def test_generate_with_model_override(self, mock_openai_class):
        """Test generation with model override — override stays on Responses API."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.output_text = "Response"
        mock_response.usage = None

        mock_client.responses.create.return_value = mock_response

        provider = OpenAIProvider(api_key="sk-test123", model="gpt-5.4-mini")
        request = TextGenerationRequest(
            messages=[Message(role="user", content="Test")],
            model="gpt-5.5",
        )

        response = provider.generate(request)

        assert response.model == "gpt-5.5"
        call_kwargs = mock_client.responses.create.call_args[1]
        assert call_kwargs["model"] == "gpt-5.5"

    @patch("app.common.ai_providers.providers.openai_provider.OpenAI")
    def test_generate_with_extra_params(self, mock_openai_class):
        """Test generation with extra parameters passed to Responses API."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.output_text = "Response"
        mock_response.usage = None

        mock_client.responses.create.return_value = mock_response

        provider = OpenAIProvider(api_key="sk-test123", model="gpt-5.4-mini")
        request = TextGenerationRequest(
            messages=[Message(role="user", content="Test")],
            extra_params={"reasoning": {"effort": "high"}},
        )

        provider.generate(request)

        call_kwargs = mock_client.responses.create.call_args[1]
        assert call_kwargs["reasoning"] == {"effort": "high"}

    @patch("app.common.ai_providers.providers.openai_provider.OpenAI")
    def test_generate_api_error(self, mock_openai_class):
        """Test handling of API errors from Responses API."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.responses.create.side_effect = Exception("API Error")

        provider = OpenAIProvider(api_key="sk-test123", model="gpt-5.4-mini")
        request = TextGenerationRequest(messages=[Message(role="user", content="Test")])

        with pytest.raises(Exception, match="API Error"):
            provider.generate(request)

    @patch("app.common.ai_providers.providers.openai_provider.OpenAI")
    def test_message_format_conversion(self, mock_openai_class):
        """Test system message → instructions, non-system messages → input."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.output_text = "Response"
        mock_response.usage = None

        mock_client.responses.create.return_value = mock_response

        provider = OpenAIProvider(api_key="sk-test123", model="gpt-5.4-mini")
        request = TextGenerationRequest(
            messages=[
                Message(role="system", content="System prompt"),
                Message(role="user", content="User message"),
                Message(role="user", content="Follow-up"),
            ]
        )

        provider.generate(request)

        call_kwargs = mock_client.responses.create.call_args[1]
        assert call_kwargs["instructions"] == "System prompt"
        assert "User message" in call_kwargs["input"]
        assert "Follow-up" in call_kwargs["input"]
        assert "messages" not in call_kwargs

    @patch("app.common.ai_providers.providers.openai_provider.OpenAI")
    def test_responses_api_routing(self, mock_openai_class):
        """Test that GPT-5 / o3 / o4 models route to Responses API, not Chat Completions."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.output_text = "ok"
        mock_response.usage = None
        mock_client.responses.create.return_value = mock_response

        for model in ("gpt-5.4-mini", "gpt-5.4", "gpt-5.5", "o3", "o4-mini"):
            provider = OpenAIProvider(api_key="sk-test123", model=model)
            request = TextGenerationRequest(
                messages=[Message(role="user", content="Hi")]
            )
            provider.generate(request)

        mock_client.chat.completions.create.assert_not_called()


class TestOpenAIProviderChatCompletions:
    """Tests for OpenAI provider — Chat Completions API path (legacy: gpt-4o)."""

    @patch("app.common.ai_providers.providers.openai_provider.OpenAI")
    def test_chat_completions_success(self, mock_openai_class):
        """Test successful text generation via Chat Completions API (gpt-4o)."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Generated caption"
        mock_response.usage.prompt_tokens = 50
        mock_response.usage.completion_tokens = 20
        mock_response.usage.total_tokens = 70

        mock_client.chat.completions.create.return_value = mock_response

        provider = OpenAIProvider(api_key="sk-test123", model="gpt-4o")
        request = TextGenerationRequest(
            messages=[
                Message(role="system", content="You are helpful."),
                Message(role="user", content="Hello!"),
            ],
            temperature=0.7,
            max_tokens=100,
        )

        response = provider.generate(request)

        assert response.text == "Generated caption"
        assert response.provider == "openai"
        assert response.model == "gpt-4o"
        assert response.usage["prompt_tokens"] == 50
        assert response.usage["completion_tokens"] == 20
        assert response.usage["total_tokens"] == 70

        mock_client.chat.completions.create.assert_called_once()
        call_kwargs = mock_client.chat.completions.create.call_args[1]
        assert call_kwargs["model"] == "gpt-4o"
        assert call_kwargs["temperature"] == 0.7
        assert call_kwargs["max_completion_tokens"] == 100
        assert len(call_kwargs["messages"]) == 2

    @patch("app.common.ai_providers.providers.openai_provider.OpenAI")
    def test_chat_completions_model_override(self, mock_openai_class):
        """Test model override stays on Chat Completions path."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Response"
        mock_response.usage = None

        mock_client.chat.completions.create.return_value = mock_response

        provider = OpenAIProvider(api_key="sk-test123", model="gpt-4o")
        request = TextGenerationRequest(
            messages=[Message(role="user", content="Test")],
            model="gpt-4-turbo",
        )

        response = provider.generate(request)

        assert response.model == "gpt-4-turbo"
        call_kwargs = mock_client.chat.completions.create.call_args[1]
        assert call_kwargs["model"] == "gpt-4-turbo"

    @patch("app.common.ai_providers.providers.openai_provider.OpenAI")
    def test_chat_completions_extra_params(self, mock_openai_class):
        """Test extra parameters passed through to Chat Completions API."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Response"
        mock_response.usage = None

        mock_client.chat.completions.create.return_value = mock_response

        provider = OpenAIProvider(api_key="sk-test123", model="gpt-4o")
        request = TextGenerationRequest(
            messages=[Message(role="user", content="Test")],
            extra_params={"top_p": 0.9, "presence_penalty": 0.5},
        )

        provider.generate(request)

        call_kwargs = mock_client.chat.completions.create.call_args[1]
        assert call_kwargs["top_p"] == 0.9
        assert call_kwargs["presence_penalty"] == 0.5

    @patch("app.common.ai_providers.providers.openai_provider.OpenAI")
    def test_chat_completions_api_error(self, mock_openai_class):
        """Test handling of API errors from Chat Completions."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("API Error")

        provider = OpenAIProvider(api_key="sk-test123", model="gpt-4o")
        request = TextGenerationRequest(messages=[Message(role="user", content="Test")])

        with pytest.raises(Exception, match="API Error"):
            provider.generate(request)

    @patch("app.common.ai_providers.providers.openai_provider.OpenAI")
    def test_chat_completions_message_format(self, mock_openai_class):
        """Test all message roles converted to dicts and passed as messages list."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Response"
        mock_response.usage = None

        mock_client.chat.completions.create.return_value = mock_response

        provider = OpenAIProvider(api_key="sk-test123", model="gpt-4o")
        request = TextGenerationRequest(
            messages=[
                Message(role="system", content="System prompt"),
                Message(role="user", content="User message"),
                Message(role="assistant", content="Assistant message"),
                Message(role="user", content="Follow-up"),
            ]
        )

        provider.generate(request)

        call_kwargs = mock_client.chat.completions.create.call_args[1]
        messages = call_kwargs["messages"]

        assert len(messages) == 4
        assert messages[0] == {"role": "system", "content": "System prompt"}
        assert messages[1] == {"role": "user", "content": "User message"}
        assert messages[2] == {"role": "assistant", "content": "Assistant message"}
        assert messages[3] == {"role": "user", "content": "Follow-up"}
