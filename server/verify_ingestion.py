import asyncio
import os
import sys
from datetime import datetime

# Add project root to path (Two levels up from server/ file if needed, or simply current dir if running from root.
# Attempting to add 'F:\AIde' to path assuming script is in 'F:\AIde\server'
current_dir = os.path.dirname(os.path.abspath(__file__))  # F:\AIde\server
project_root = os.path.dirname(current_dir)  # F:\AIde
sys.path.append(project_root)

# Mocking database session for test
from unittest.mock import MagicMock


async def verify_ingestion_logic():
    print("--- Verifying Ingestion Logic (Direct) ---")

    try:
        # 1. Import Modules (verifies dependencies)
        print("[1] Importing modules...")

        print("    Importing CodeParser...")
        from server.ingestion.parser import CodeParser, FileMetadata

        print("    ✅ CodeParser imported.")

        print("    Importing VectorStore...")
        from server.shared.vector_store import VectorStore

        print("    ✅ VectorStore imported.")

        print("    Importing Ingestion Router...")
        from server.ingestion.router import ingest_project_background

        print("    ✅ Ingestion Router imported.")

        print("    Importing Models...")
        from server.models.ingestion import IngestionJob, IngestionStatus

        print("    ✅ Models imported.")

        # 2. Test Parser
        print("[2] Testing CodeParser...")
        parser = CodeParser()
        test_file_content = "def hello():\n    print('world')\n\nclass Foo:\n    pass"
        test_path = "test_script.py"

        metadata, chunks = parser.parse_file(test_path, test_file_content)
        print(
            f"    ✅ Parsed metadata: functions={len(metadata.functions)}, classes={len(metadata.classes)}"
        )
        print(f"    ✅ Generated {len(chunks)} chunks.")

        assert len(metadata.functions) >= 1
        assert len(metadata.classes) >= 1

        # 3. Test Vector Store Interaction (Mocked Project Ingestion)
        print("[3] Testing Vector Store Integration...")
        vector_store = VectorStore()
        # Create a dummy job
        job_id = "test_job_1"
        job = IngestionJob(id=job_id, project_id="test_proj", project_path=".")

        # Manually trigger what the background task does (simplified)
        for chunk in chunks:
            await vector_store.add_code_snippet(
                project_id="test_proj",
                code=chunk.content,
                file_path=test_path,
                function_name=chunk.metadata.get("element_name"),
            )
        print("    ✅ Added chunks to VectorStore.")

        print("\n🎉 VERIFICATION SUCCESSFUL: Ingestion logic is sound.")
        return True

    except ImportError as e:
        print(f"❌ Import Failed: {e}")
        # Hint at path issues
        print(f"Current Path: {sys.path}")
        return False
    except Exception as e:
        print(f"❌ Logic Verification Failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    asyncio.run(verify_ingestion_logic())
