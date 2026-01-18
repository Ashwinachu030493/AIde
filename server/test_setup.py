import os
import sys

from sqlalchemy import text

# Add project root to path (one level up)
sys.path.append(os.path.dirname(os.getcwd()))

from server.shared.database import engine, init_db
from server.shared.vector_store import VectorStore


def test_db():
    print("Testing SQLite Database...")
    try:
        init_db()
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1")).scalar()
            assert result == 1
        print("✅ Database initialized and connected.")
    except Exception as e:
        print(f"❌ Database error: {e}")
        raise


def test_vector_store():
    print("Testing Local ChromaDB...")
    try:
        vs = VectorStore()
        # Add a dummy doc
        vs._add_code_snippet_sync("test_proj", "print('hello')", "test.py")
        results = vs._query_similar_code_sync("test_proj", "hello")
        assert len(results) > 0
        print("✅ Vector Store working.")
    except Exception as e:
        print(f"❌ Vector Store error: {e}")
        raise


if __name__ == "__main__":
    test_db()
    test_vector_store()
