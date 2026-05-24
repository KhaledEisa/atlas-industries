"""Cross-platform reset: wipes the FAISS vector store and triggers a fresh ingest."""
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
store = ROOT / "data" / "vector_store"

if store.exists():
    shutil.rmtree(store)
    print(f"[reset] Removed {store}")
else:
    print(f"[reset] No existing store at {store}")

print("[reset] Rebuilding index...")
result = subprocess.run(
    [sys.executable, str(ROOT / "src" / "ingest.py")],
    cwd=str(ROOT),
)
sys.exit(result.returncode)
