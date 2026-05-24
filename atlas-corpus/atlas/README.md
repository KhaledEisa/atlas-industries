# Atlas Industries — Corpus & Evaluation Bundle

This bundle is the dataset for the **Atlas Industries Enterprise Assistant** AI/ML graduation project (agentic RAG capstone). It contains the full document corpus and the gold evaluation cases.

## Contents

```
data/docs/
├── hr/        10 documents — vacation, sick leave, onboarding, remote work, etc.
├── it/        10 documents — VPN, password reset, MFA, incident response, etc.
└── finance/   10 documents — travel reimbursement, per diem, client dining, etc.

tests/
└── eval_cases.jsonl   10 gold test questions for DeepEval
```

## Corpus Profile

**30 total documents**, designed to stress every component of an agentic RAG pipeline.

### Language distribution

- **English (60%)** — 18 documents
- **Arabic (30%)** — 9 documents
- **Bilingual EN+AR (10%)** — 3 documents

### Format distribution

- **Markdown (.md)** — 12 documents
- **PDF (.pdf)** — 9 documents
- **DOCX (.docx)** — 9 documents

### Why this mix is hard

Students must build an ingestion pipeline that:
1. Loads three different formats (MD, PDF, DOCX), each with different text-extraction quirks.
2. Handles Arabic text correctly — including right-to-left rendering, Unicode normalization, and tokenization for embeddings.
3. Picks embeddings that work cross-lingually so an Arabic question can retrieve an Arabic document and an English question can retrieve an English document — and bilingual documents can match either.
4. Preserves source filenames as metadata for citation, including filenames that contain Arabic characters.

## Cross-references in the Corpus

Documents reference each other by policy ID (e.g. HR-VAC-001 → HR-001-vacation-policy.md). Some test questions intentionally require synthesis across two or three documents — this is part of the difficulty.

## Eval Cases Schema

Each line in `tests/eval_cases.jsonl` is a JSON object with:

| Field | Type | Description |
|---|---|---|
| `id` | string | Stable case ID (EVAL-001 to EVAL-010) |
| `input` | string | The question, as a user would phrase it |
| `expected_domain` | string | `hr`, `it`, or `finance` — used for routing accuracy |
| `expected_output` | string | A reference answer (factually correct, paraphrased) |
| `expected_sources` | array | Filenames whose content supports the answer |
| `language` | string | `en` or `ar` |

Questions span all three domains and both languages. Several require **multi-document retrieval** (different filenames in `expected_sources`).

## Locked Facts

These facts are explicitly stated in the corpus and are non-negotiable for grading:

- New-hire vacation: 15 days/year, accrual 1.25 days/month after probation.
- Probation period: 90 days.
- Sick leave: 14 paid days/year, medical certificate required for 3+ days.
- Remote work: max 3 days/week, not available during probation.
- VPN: Cisco AnyConnect, server `vpn.atlas-industries.com`, port 443.
- Password reset: `portal.atlas-industries.com/reset`, 24h cooldown.
- MFA: Microsoft Authenticator only.
- Software request SLA (< $500): 3 to 5 business days.
- Domestic hotel cap: 1,500 EGP/night.
- International hotel cap: 200 USD/night.
- Airport taxi: 800 EGP per leg.
- Client dinner: 2,000 EGP per person.
- Per diem: 500 EGP domestic / 75 USD international.
- Expense submission window: 30 days, hard deadline 60 days.

If a student's system invents different numbers, that is a hallucination by the **Faithfulness** and **Hallucination** DeepEval metrics.

## Folder Layout (Required)

Place documents at exactly the paths shown above. Filenames must not be renamed — the eval cases reference them by filename for the citation check.

---

Atlas Industries is a fictional company. Any resemblance to real companies, policies, or systems is coincidental.
