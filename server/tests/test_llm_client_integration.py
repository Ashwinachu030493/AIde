"""
Integration tests for unified LLM client.
Tests provider routing, fallbacks, and user configuration.
"""

import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest
from sqlalchemy.orm import Session

from server.llm.client import LLMClient, UserLLMConfig


class TestLLMClientIntegration:
    """Integration tests for consolidated LLM client."""

    def test_client_initialization(self):
        """Test client initializes with default config."""
        client = LLMClient()
        assert client.user_config is not None
        assert client.usage_stats["total_tokens"] == 0
        assert isinstance(client.usage_stats["requests_by_provider"], dict)

    def test_client_with_user_config(self):
        """Test client initializes with user-provided config."""
        config = UserLLMConfig(
            openai_api_key="test-key", default_model="gpt-4", preferred_providers=["openai"]
        )
        client = LLMClient(user_config=config)
        assert client.user_config.openai_api_key == "test-key"
        assert client.user_config.default_model == "gpt-4"

    def test_get_available_providers_with_keys(self):
        """Test provider detection with configured keys."""
        config = UserLLMConfig(
            openai_api_key="test-openai-key", anthropic_api_key="test-anthropic-key"
        )
        client = LLMClient(user_config=config)
        providers = client.get_available_providers()

        assert "openai" in providers
        assert "anthropic" in providers
        assert "groq" not in providers

    def test_get_available_providers_fallback_to_env(self):
        """Test provider detection falls back to environment variables."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "env-key"}):
            client = LLMClient(user_config=UserLLMConfig())
            providers = client.get_available_providers()
            assert "openai" in providers

    def test_model_provider_detection(self):
        """Test correct provider detection from model names."""
        client = LLMClient()

        assert client._get_model_provider("gpt-4") == "openai"
        assert client._get_model_provider("gpt-3.5-turbo") == "openai"
        assert client._get_model_provider("claude-3-opus") == "anthropic"
        assert client._get_model_provider("claude-3-sonnet") == "anthropic"
        assert client._get_model_provider("llama3-70b") == "groq"
        assert client._get_model_provider("huggingface/model") == "huggingface"

    def test_api_key_retrieval_from_config(self):
        """Test API key retrieval prioritizes user config over env."""
        config = UserLLMConfig(openai_api_key="config-key")
        client = LLMClient(user_config=config)

        key = client._get_api_key_for_provider("openai")
        assert key == "config-key"

    def test_api_key_retrieval_fallback_to_env(self):
        """Test API key falls back to environment when not in config."""
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "env-anthropic-key"}):
            client = LLMClient(user_config=UserLLMConfig())
            key = client._get_api_key_for_provider("anthropic")
            assert key == "env-anthropic-key"

    def test_model_resolution_with_task_type(self):
        """Test model resolution based on task type and user tier."""
        client = LLMClient()

        # Free tier should get budget model
        model, fallback = client._resolve_model(None, "code_generation", "free")
        assert model == "gpt-3.5-turbo"

        # Premium tier should get primary model
        model, fallback = client._resolve_model(None, "code_generation", "premium")
        assert model == "gpt-4-turbo-preview"

    def test_token_estimation(self):
        """Test token estimation logic."""
        client = LLMClient()

        prompt = "Test prompt with some words"
        system_prompt = "System instructions"

        tokens = client._estimate_tokens(prompt, system_prompt)
        assert tokens > 0
        assert tokens == (len(prompt) // 4) + (len(system_prompt) // 4)

    def test_stats_update(self):
        """Test usage statistics update."""
        client = LLMClient()

        client._update_stats("openai", "Generated response content")

        assert client.usage_stats["total_tokens"] > 0
        assert client.usage_stats["requests_by_provider"]["openai"] == 1

    @pytest.mark.asyncio
    async def test_completion_without_api_key_raises_error(self):
        """Test that requesting completion without API key raises ValueError."""
        client = LLMClient(user_config=UserLLMConfig())

        with pytest.raises(ValueError, match="No API key"):
            await client.get_completion(prompt="Test prompt", model="gpt-4")

    @pytest.mark.asyncio
    async def test_completion_with_mock_db_logging(self):
        """Test completion with database logging."""
        mock_db = Mock(spec=Session)
        mock_db.add = Mock()
        mock_db.commit = Mock()

        config = UserLLMConfig(openai_api_key="test-key")
        client = LLMClient(user_config=config, db_session=mock_db)

        with patch("server.llm.client.acompletion", new_callable=AsyncMock) as mock_acompletion:
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = "Test response"
            mock_acompletion.return_value = mock_response

            result = await client.get_completion(
                prompt="Test", streaming=False, project_id="test-project"
            )

            assert result == "Test response"
            assert mock_db.add.called
            assert mock_db.commit.called

    def test_model_routing_table_completeness(self):
        """Test that all task types have proper routing configuration."""
        required_keys = ["primary", "fallback", "budget_model"]

        for task_type, config in LLMClient.MODEL_ROUTING.items():
            for key in required_keys:
                assert key in config, f"Missing {key} in {task_type} routing"


class TestLLMClientWithDatabase:
    """Tests requiring database interaction."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return Mock(spec=Session)

    def test_client_with_db_session(self, mock_db):
        """Test client accepts database session."""
        client = LLMClient(db_session=mock_db)
        assert client.db == mock_db

    @pytest.mark.asyncio
    async def test_usage_logging_structure(self, mock_db):
        """Test that usage logging creates proper log structure."""
        config = UserLLMConfig(openai_api_key="test-key")
        client = LLMClient(user_config=config, db_session=mock_db)

        with patch("server.llm.client.acompletion", new_callable=AsyncMock) as mock_completion:
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = "Response"
            mock_completion.return_value = mock_response

            await client.get_completion(
                prompt="Test", streaming=False, project_id="test-proj", operation="test_op"
            )

            # Verify db.add was called
            assert mock_db.add.called
            log_entry = mock_db.add.call_args[0][0]

            # Check log entry attributes
            assert hasattr(log_entry, "provider")
            assert hasattr(log_entry, "model")
            assert hasattr(log_entry, "operation")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
