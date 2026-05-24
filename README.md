# Atlas Industries — Enterprise Knowledge Assistant

An internal knowledge chatbot for Atlas Industries, a fictional mid-sized company (~500 employees). Employees ask plain-language questions and receive clear, cited answers drawn exclusively from official company documents across HR, IT Support, and Finance.

---

## Overview

The system provides a single conversational interface over 30 internal policy documents. It routes each question to the correct department, retrieves the relevant passages, and returns a grounded answer with source citations — in both English and Arabic.

Key capabilities:
- Multi-format document ingestion (Markdown, PDF, DOCX)
- Multilingual support — English and Arabic, including RTL rendering
- Domain routing — HR, IT Support, Finance & Reimbursement
- Session memory — follow-up questions resolve against prior turns
- Source citations on every answer
- Structured logging per run
- Automated evaluation with DeepEval

---

## Tech Stack

| Layer | Technology |
|---|---|
| Orchestration | LangGraph |
| LLM | Google Gemini / Groq (free tier) |
| Embeddings | `BAAI/bge-m3` or `intfloat/multilingual-e5-large` |
| Vector Store | FAISS / Chroma / Qdrant |
| UI | Chainlit / Streamlit / Gradio |
| Evaluation | DeepEval |
| Logging | structlog / loguru |
| Validation | Pydantic |
| Language | Python 3.10+ |

---

## Document Corpus

30 documents across three domains:

| Domain | Count | Formats |
|---|---|---|
| HR | 10 | `.md`, `.pdf`, `.docx` |
| IT Support | 10 | `.md`, `.pdf`, `.docx` |
| Finance & Reimbursement | 10 | `.md`, `.pdf`, `.docx` |

~60% English, ~30% Arabic, ~10% bilingual.

---

## Project Structure

```
atlas-industries/
├── src/
│   ├── ingest.py           # Document loading, chunking, embedding, vector store
│   ├── orchestrator.py     # LangGraph workflow — router, retriever, agent, memory
│   ├── tools.py            # Typed agent tools (Pydantic schemas)
│   ├── observability.py    # Structured JSON logging
│   └── settings.py         # Shared configuration
├── app.py                  # Chat UI entry point
├── config/
│   └── RAI_Config.yaml     # Responsible AI rules
├── data/
│   └── docs/
│       ├── hr/
│       ├── it/
│       └── finance/
├── tests/
│   ├── evaluate.py         # DeepEval evaluation script
│   └── eval_cases.jsonl    # 10 gold test cases
├── scripts/
│   └── reset.sh            # Wipe and rebuild the vector index
├── notebooks/
│   └── 02_retrieval.ipynb  # Retrieval quality exploration
├── outputs/
│   ├── eval_report.json
│   ├── final_report.md
│   └── run_logs.jsonl
├── docs/
│   ├── architecture.png
│   └── demo.gif
├── .env.example
├── requirements.txt
└── README.md
```

---

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/KhaledEisa/atlas-industries.git
cd atlas-industries

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy and fill in environment variables
cp .env.example .env

# 4. Ingest documents and build the vector index
python src/ingest.py

# 5. Launch the chat UI
python app.py
```

---

## Evaluation

```bash
python tests/evaluate.py
# Output: outputs/eval_report.json
```

Metrics: Faithfulness, Answer Relevancy, Contextual Precision, Contextual Recall, Hallucination, Routing Accuracy.

---

## Team

| Member | Role |
|---|---|
| **Khaled Eissa** | M1 — Data Ingestion & Vector Store |
| **Seif Hassan** | M2 — LangGraph Workflow & Domain Router |
| **Mohamed Waleed** | M3 — Chat UI & Observability |
| **Rahma Mohamed** | M4 — Evaluation, Documentation & Demo |

---

## Deliverable Checklist

- [ ] Multi-format ingestion pipeline with Arabic support
- [ ] LangGraph workflow with typed state schema
- [ ] Session memory (in-session, keyed by `session_id`)
- [ ] Minimum 3 typed tools with Pydantic schemas
- [ ] Citations on every answer
- [ ] Single-command chat UI with RTL Arabic rendering
- [ ] Structured JSON logging to `outputs/run_logs.jsonl`
- [ ] DeepEval evaluation over 10 gold cases
- [ ] Reset script (`scripts/reset.sh`)
- [ ] Architecture diagram, demo recording, final report

---

*Graduation project — Arab Academy for Science, Technology & Maritime Transport.*
