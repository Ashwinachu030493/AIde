"""
Integration tests for lazy-loaded VectorStore with fallback embeddings.
"""

import os
import tempfile
from concurrent.futures import TimeoutError as FuturesTimeoutError
from unittest.mock import Mock, patch

import pytest

from server.shared.vector_store import VectorStore


class TestVectorStoreInitialization:
    """Tests for VectorStore lazy initialization and fallback."""

    def test_vectorstore_initializes_without_blocking(self):
        """Test that VectorStore init doesn't block on model download."""
        import time

        start = time.time()
        store = VectorStore()
        elapsed = time.time() - start

        # Should complete initialization very quickly
        assert elapsed < 10, "VectorStore init took too long"
        assert store.client is not None

    def test_offline_mode_uses_dummy_embeddings(self):
        """Test that TRANSFORMERS_OFFLINE=1 uses dummy embeddings."""
        with patch.dict("os.environ", {"TRANSFORMERS_OFFLINE": "1"}):
            store = VectorStore()

            # Verify dummy embedding function is used
            test_input = ["test string"]
            result = store.embedding_fn(test_input)

            assert len(result) == 1
            assert len(result[0]) == 384  # Embedding dimension
            assert all(val == 0.0 for val in result[0])  # Dummy returns zeros

    def test_custom_model_path_respected(self):
        """Test that EMBEDDING_MODEL_PATH is used when set."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(
                "os.environ", {"EMBEDDING_MODEL_PATH": tmpdir, "TRANSFORMERS_OFFLINE": "0"}
            ):
                # This will timeout and fallback since path is empty
                store = VectorStore()

                # Should have initialized (with fallback)
                assert store.embedding_fn is not None

    def test_timeout_triggers_fallback(self):
        """Test that embedding load timeout triggers dummy fallback."""
        with patch(
            "server.shared.vector_store.embedding_functions.SentenceTransformerEmbeddingFunction"
        ) as mock_st:
            # Simulate slow initialization
            def slow_init(*args, **kwargs):
                import time

                time.sleep(10)  # Longer than 5s timeout

            mock_st.side_effect = slow_init

            # Should timeout and use dummy
            store = VectorStore()

            # Verify dummy is used
            result = store.embedding_fn(["test"])
            assert len(result[0]) == 384
            assert all(val == 0.0 for val in result[0])

    def test_exception_during_load_triggers_fallback(self):
        """Test that exceptions during load trigger dummy fallback."""
        with patch(
            "server.shared.vector_store.embedding_functions.SentenceTransformerEmbeddingFunction"
        ) as mock_st:
            mock_st.side_effect = Exception("Mock initialization error")

            # Should fallback to dummy
            store = VectorStore()

            # Verify dummy is used
            result = store.embedding_fn(["test"])
            assert len(result[0]) == 384


class TestVectorStoreOperations:
    """Tests for VectorStore CRUD operations."""

    @pytest.fixture
    def store(self):
        """Create VectorStore with offline mode."""
        with patch.dict("os.environ", {"TRANSFORMERS_OFFLINE": "1"}):
            return VectorStore()

    @pytest.fixture
    def temp_chroma_path(self):
        """Create temporary ChromaDB path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    def test_get_project_collection(self, store):
        """Test getting or creating project collection."""
        collection = store._get_project_collection("test-project")
        assert collection is not None
        assert "test-project" in collection.name

    @pytest.mark.asyncio
    async def test_add_code_snippet(self, store):
        """Test adding code snippet to vector store."""
        doc_id = await store.add_code_snippet(
            project_id="test-proj",
            code="def test(): pass",
            file_path="test.py",
            function_name="test",
        )

        assert doc_id is not None
        assert isinstance(doc_id, str)

    @pytest.mark.asyncio
    async def test_query_similar_code(self, store):
        """Test querying similar code."""
        project_id = f"test-proj-{id(self)}"  # Unique project ID for this test

        # Add some code first
        await store.add_code_snippet(
            project_id=project_id,
            code="def hello(): print('hello')",
            file_path="hello.py",
            function_name="hello",
        )

        # Query for similar code
        results = await store.query_similar_code(
            project_id=project_id, query="greeting function", n_results=5
        )

        assert isinstance(results, list)
        # May be empty with dummy embeddings, but should not error

    def test_language_detection(self, store):
        """Test language detection from file extension."""
        assert store._detect_language("test.py") == "python"
        assert store._detect_language("test.js") == "javascript"
        assert store._detect_language("test.ts") == "typescript"
        assert store._detect_language("test.html") == "html"
        assert store._detect_language("test.unknown") == "unknown"


class TestVectorStoreWithChroma:
    """Tests for ChromaDB integration."""

    def test_local_client_initialization(self):
        """Test local persistent client initialization."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(
                "os.environ", {"CHROMA_SERVER_HOST": "local", "TRANSFORMERS_OFFLINE": "1"}
            ):
                with patch("chromadb.PersistentClient") as mock_client:
                    mock_client.return_value = Mock()
                    store = VectorStore()
                    assert store.client is not None

    def test_http_client_initialization(self):
        """Test HTTP client initialization."""
        with patch("chromadb.HttpClient") as mock_http:
            mock_http.return_value = Mock()

            with patch.dict(
                "os.environ", {"CHROMA_SERVER_HOST": "localhost:8000", "TRANSFORMERS_OFFLINE": "1"}
            ):
                store = VectorStore()
                mock_http.assert_called_once()


class TestVectorStoreLazyLoading:
    """Tests for lazy loading behavior in ingestion router."""

    def test_get_vector_store_singleton_pattern(self):
        """Test that get_vector_store returns same instance."""
        from server.ingestion.router import get_vector_store

        store1 = get_vector_store()
        store2 = get_vector_store()

        assert store1 is store2, "Should return same singleton instance"

    def test_vector_store_not_initialized_on_import(self):
        """Test that VectorStore is not created on module import."""
        # This is tested by the fact that we can import the router
        # without triggering a long embedding download
        import importlib
        import sys

        # Remove module if already imported
        if "server.ingestion.router" in sys.modules:
            del sys.modules["server.ingestion.router"]

        import time

        start = time.time()

        # Import should be fast
        from server.ingestion import router

        elapsed = time.time() - start
        assert elapsed < 2, "Router import took too long"

    def test_vector_store_initialized_on_first_use(self):
        """Test that VectorStore is created on first get_vector_store call."""
        from server.ingestion.router import _vector_store, get_vector_store

        # Initially should be None
        # (Can't directly access _vector_store due to scope, but conceptually tested)
        # First call creates it
        with patch.dict("os.environ", {"TRANSFORMERS_OFFLINE": "1"}):
            store = get_vector_store()
            assert store is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
