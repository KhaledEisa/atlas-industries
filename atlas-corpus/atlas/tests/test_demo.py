from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path

# ── Fix path ──────────────────────────────────────────────────────
# test_demo.py is at: atlas-corpus/atlas/tests/test_demo.py
# src/ is at:         src/
# So we need to go up 3 levels from tests/ to reach project root

_ROOT = Path(__file__).resolve().parent.parent.parent.parent
print(f"Project root: {_ROOT}")   # ← add this so you can see what path it finds
sys.path.insert(0, str(_ROOT))

from src.orchestrator import run

# ── Give each session a fixed ID for testing ──────────────────────
SESSION_ID = "demo-session-001"

# ─────────────────────────────────────────────────────────────────
# Turn 1 — English Finance question
# Expected: Router picks finance, retrieves FIN-001 + FIN-002
# ─────────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("TURN 1 — English Finance")
print("="*60)

result1 = run(
    question   = "I traveled to a client meeting last week. How do I submit the reimbursement, and how many days do I have?",
    session_id = SESSION_ID
)

print(f"Domain     : {result1['domain']}")
print(f"Sources    : {result1['sources']}")
print(f"Tool calls : {result1['tool_calls']}")
print(f"Answer     :\n{result1['answer']}")

# ─────────────────────────────────────────────────────────────────
# Turn 2 — Follow-up, no domain hint
# Expected: Memory carries finance context, retrieves hotel cap
# ─────────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("TURN 2 — Follow-up with memory")
print("="*60)

result2 = run(
    question   = "And what's the cap on the hotel for a domestic trip?",
    session_id = SESSION_ID    # same session → memory carries over
)

print(f"Domain     : {result2['domain']}")
print(f"Sources    : {result2['sources']}")
print(f"Answer     :\n{result2['answer']}")

# ─────────────────────────────────────────────────────────────────
# Turn 3 — Arabic Finance question
# Expected: Router picks finance, answer in Arabic, RTL
# ─────────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("TURN 3 — Arabic Finance question")
print("="*60)

result3 = run(
    question   = "ما هو الحد الأقصى لعشاء العملاء لكل شخص؟",
    session_id = SESSION_ID
)

print(f"Domain     : {result3['domain']}")
print(f"Sources    : {result3['sources']}")
print(f"Answer     :\n{result3['answer']}")