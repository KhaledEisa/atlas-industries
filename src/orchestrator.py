from __future__ import annotations  

#from tkinter import END

import os
import uuid
from typing import TypedDict, Literal    
from pathlib import Path
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from pydantic import BaseModel, Field

from src.ingest import load_index, build_embeddings
from src.settings import settings
from src.tools import TOOLS
from src.retriever import faiss_index, embeddings 

load_dotenv()

# ── Initialize LLM ────────────────────────────────────────────────
llm = ChatGroq(
    model       = "llama-3.3-70b-versatile",   # free, fast, multilingual
    api_key     = os.getenv("GROQ_API_KEY"),
    temperature = 0
)

llm_with_tools = llm.bind_tools(TOOLS)

class AtlasState(TypedDict):

    # ── The Question ──────────────────────────────
    question: str
    # What the user typed
    # Example: "How do I submit a reimbursement?"

    # ── Routing ───────────────────────────────────
    domain: str
    # Stamped by Router node
    # One of: "hr" | "it" | "finance" | "unknown"

    # ── Retrieval ─────────────────────────────────
    retrieved_chunks: list[dict]
    # Filled by Retriever node
    # Each dict has: content, source_filename, domain, language
    # Example:
    # [
    #   {
    #     "content": "Submit within 14 days...",
    #     "source_filename": "FIN-001-travel-reimbursement-policy.md",
    #     "domain": "finance",
    #     "language": "en"
    #   }
    # ]

    # ── Tools ─────────────────────────────────────
    tool_calls: list[dict]
    # Filled by Agent node each time it calls a tool
    # Each dict has: tool_name, input, output
    # Example:
    # [
    #   {
    #     "tool_name": "ReimbursementCalculator",
    #     "input": {"category": "hotel", "days": 3, "trip_type": "domestic"},
    #     "output": {"total": 4500, "cap": 1500}
    #   }
    # ]

    # ── Answer ────────────────────────────────────
    answer: str
    # Filled by Answer Composer node
    # Final cited answer in user's language

    sources: list[str]
    # Filled by Answer Composer node
    # Real filenames only — no fabrication
    # Example: ["FIN-001-travel-reimbursement-policy.md", "FIN-002-expense-claim-sop.pdf"]

    # ── Session & Logging ─────────────────────────
    session_id: str
    # Identifies the conversation session
    # Same session_id = same memory thread
    # New chat = new session_id

    run_id: str
    # Unique ID for THIS specific question
    # Used by Member 3 for logging in run_logs.jsonl
    # Generate with: str(uuid.uuid4())

    # ── Memory ────────────────────────────────────
    memory: list[dict]
    # Loaded by Memory Loader node at the start
    # Previous Q&A pairs from this session
    # Example:
    # [
    #   {"role": "user",      "content": "How do I submit reimbursement?"},
    #   {"role": "assistant", "content": "You must submit within 14 days..."}
    # ]

    # ── Planning ──────────────────────────────────
    plan: str
    # Filled by Planner node
    # Describes the strategy for this question
    # Example: "Simple lookup — 1 retrieval step, no tools needed"
    # Example: "Multi-step — retrieve FIN-001, then calculate total"

    # ── Safety Counters ───────────────────────────
    step_count: int
    # Incremented by every node that runs
    # When it hits
    
    checker_retries : int

# ─────────────────────────────────────────────
# 1. Load ONCE at startup (outside the graph)
#    Never load inside the node — 2.27GB model!
# ─────────────────────────────────────────────
embeddings = build_embeddings()
faiss_index = load_index(Path(settings.vector_store_path), embeddings)

# =================================================
# ── 1. Router's own Pydantic schema ──────────────────────────────
# =================================================
class RouterOutput(BaseModel):
    domain: str = Field(
        description="The domain of the question. Must be exactly one of: hr, it, finance, unknown"
    )
    confidence: str = Field(
        description="How confident you are: high, medium, low"
    )
    reasoning: str = Field(
        description="One sentence explaining why you chose this domain"
    )

RouterOutput.model_rebuild()

ROUTER_PROMPT = '''
You are a domain classifier for an internal company knowledge base.
Classify the user's question into EXACTLY one of these domains:

- hr       → questions about leave, vacation, hiring, onboarding, 
             performance, remote work, grievances, sick days
- it       → questions about VPN, passwords, software, laptops, 
             network, email, MFA, incidents
- finance  → questions about reimbursement, expenses, invoices, 
             per diem, procurement, corporate card, vendor payments
- unknown  → if you genuinely cannot classify it

Rules:
- Return only lowercase: hr, it, finance, or unknown
- Never return anything else
- If the question could fit two domains, pick the most likely one
'''

def router_node(state: AtlasState) -> dict:
    
    memory_context = ""
    if state["memory"]:
        last_turn = state["memory"][-1]
        memory_context = f"\nPrevious topic: {last_turn.get('content', '')}"

    # Combine question + memory context into one string
    full_question = state["question"] + memory_context
    
    structured_router = llm.with_structured_output(RouterOutput)
    try:
        router_obj = structured_router.invoke([
            SystemMessage(content=ROUTER_PROMPT),
            HumanMessage(content=full_question)
        ])

        # Extract just the domain string, not the whole dict
        domain = router_obj.domain.lower().strip()
        
        # Safety check — only accept known values
        if domain not in ("hr", "it", "finance", "unknown"):
            domain = "unknown"
            
    except Exception:
        # Never crash — fallback to unknown
        domain = "unknown"

    return {
        "domain":     domain,
        "step_count": state["step_count"] + 1
    }
    
memory_saver = MemorySaver()
# =============================================
# ── 3. Memory Loader & Writer Nodes ──────────────────────────────
# =============================================
def memory_loader_node(state: AtlasState) -> dict:
    """
    Runs first, every single turn.
    Loads previous Q&A pairs from this session into state["memory"].
    New session = empty memory, no crash.
    """

    session_id = state["session_id"]
    try:
        # Get checkpoint for this session
        config = {"configurable": {"thread_id": session_id}}
        checkpoint = memory_saver.get(config)

        if checkpoint and "memory" in checkpoint["channel_values"]:
            loaded_memory = checkpoint["channel_values"]["memory"]
        else:
            loaded_memory = []   # new session, start fresh

    except Exception:
        loaded_memory = []       # never crash on memory failure

    return {
        "memory":     loaded_memory,
        "step_count": state["step_count"] + 1
    }

def memory_writer_node(state: AtlasState) -> dict:
    """
    Runs at the end of the graph.
    Saves the updated memory (including this turn's Q&A) back to the checkpoint.
    """
    # Build new memory entry from this turn
    new_entry_user = {
        "role":    "user",
        "content": state["question"]
    }
    new_entry_assistant = {
        "role":    "assistant",
        "content": state["answer"]
    }

    # Append to existing memory
    updated_memory = state["memory"] + [new_entry_user, new_entry_assistant]

    return {
        "memory":     updated_memory,
        "step_count": state["step_count"] + 1
    }

# =================================================
# ── 4. Planner Node ──────────────────────────────  
# =================================================

class Plan(BaseModel):
    complexity: Literal["simple", "multi_step"] = Field(
        description="simple = one retrieval no tools | multi_step = needs tools or multiple retrievals"
    )
    needs_tools: bool = Field(
        description="True if the agent will need to call any tool"
    )
    suggested_tools: list[str] = Field(
        description="List of tools to use, empty if none needed. Options: PolicyLookup, ReimbursementCalculator, LeaveTypesLister",
        default=[]
    )
    reasoning: str = Field(
        description="One sentence explaining the strategy"
    )

PLANNER_PROMPT = """
You are a planning assistant for an internal company knowledge base.
Given the user's question and domain, decide the strategy to answer it.

Available tools:
- PolicyLookup            → use when question asks about a specific policy ID (e.g FIN-001)
- ReimbursementCalculator → use when question needs a calculation (amounts, totals, caps)
- LeaveTypesLister        → use when question asks about types of leave available

Rules:
- If the question is a simple factual lookup → complexity: simple, needs_tools: false
- If the question needs calculation or specific policy → complexity: multi_step, needs_tools: true
- Always explain your reasoning in one sentence
"""

def planner_node(state: AtlasState) -> dict:

    structured_planner = llm.with_structured_output(Plan)

    # Build context from memory + domain
    memory_context = ""
    if state["memory"]:
        last_turn = state["memory"][-1]
        memory_context = f"\nPrevious topic: {last_turn.get('content', '')}"

    full_context = f"""
    Domain   : {state["domain"]}
    Question : {state["question"]}
    {memory_context}
    """

    try:
        plan_obj = structured_planner.invoke([
            SystemMessage(content=PLANNER_PROMPT),
            HumanMessage(content=full_context)
        ])

        # Convert to readable string for state
        plan_str = (
            f"Complexity: {plan_obj.complexity} | "
            f"Needs tools: {plan_obj.needs_tools} | "
            f"Tools: {plan_obj.suggested_tools} | "
            f"Reasoning: {plan_obj.reasoning}"
        )

    except Exception:
        # Safe fallback
        plan_obj  = None
        plan_str  = "Complexity: simple | Needs tools: false | Tools: [] | Reasoning: fallback plan"

    return {
        "plan":       plan_str,
        "step_count": state["step_count"] + 1
    }
    
# =================================================
# ── 5. Retriever Node ───────────────────────────────
# =================================================

# ── Retriever Node ────────────────────────────────────────────────
def retriever_node(state: AtlasState) -> dict:
    """
    Reads domain from state.
    Searches FAISS index filtered by that domain.
    Returns top-k chunks into state["retrieved_chunks"].
    """

    question = state["question"]
    domain   = state["domain"]

    # ── 1. Safety check ───────────────────────────────────────────
    if domain not in ("hr", "it", "finance"):
        domain = "finance"   # default fallback

    # ── 2. Check if fan-out needed (unknown domain) ───────────────
    if state["domain"] == "unknown":
        chunks = _fanout_retrieval(question)
    else:
        chunks = _single_domain_retrieval(question, domain)

    return {
        "retrieved_chunks": chunks,
        "step_count":       state["step_count"] + 1
    }


# ── Helper: single domain retrieval ──────────────────────────────
def _single_domain_retrieval(question: str, domain: str) -> list[dict]:
    retriever = faiss_index.as_retriever(
        search_kwargs={
            "k":      5,
            "filter": {"domain": domain}
        }
    )

    results = retriever.invoke(question)
    return _to_chunks(results)


# ── Helper: fan-out retrieval (unknown domain) ────────────────────
def _fanout_retrieval(question: str) -> list[dict]:
    """
    Searches all 3 domains and merges results.
    Used when Router returns unknown.
    Returns 3 chunks per domain = 9 total.
    """
    all_chunks = []

    for domain in ("finance", "hr", "it"):
        retriever = faiss_index.as_retriever(
            search_kwargs={
                "k":      3,
                "filter": {"domain": domain}
            }
        )
        results = retriever.invoke(question)
        all_chunks.extend(_to_chunks(results))

    return all_chunks


# ── Helper: convert LangChain Documents to clean dicts ────────────
def _to_chunks(results) -> list[dict]:
    """
    Converts LangChain Document objects to clean dicts
    that the rest of the graph can use easily.
    """
    chunks = []
    for doc in results:
        chunks.append({
            "content":         doc.page_content,
            "source_filename": doc.metadata.get("source_filename", "unknown"),
            "domain":          doc.metadata.get("domain",          "unknown"),
            "language":        doc.metadata.get("language",        "en"),
        })
    return chunks


# =================================================
# ── 5. Agent Node ───────────────────────────────
# =================================================


AGENT_PROMPT = """
You are Atlas, an internal knowledge assistant for Atlas Industries.
You help employees find answers from official company documents only.

Rules:
- Answer ONLY from the retrieved document chunks provided
- NEVER fabricate policies, numbers, or rules
- If the answer is not in the chunks, say: "This information is not available in the company documents"
- Always respond in the same language as the user's question
- Arabic question → Arabic answer
- English question → English answer
- Use tools when the plan suggests it or when calculation is needed
- Maximum 3 tool calls per question
"""


def agent_node(state: AtlasState) -> dict:
    """
    The brain of the graph.
    Reads chunks + plan, reasons, calls tools if needed,
    produces a raw answer for the Checker to evaluate.
    """

    # ── 1. Check step limit ───────────────────────────────────────
    if state["step_count"] >= 10:
        return {
            "answer":     "I was unable to complete this request within the allowed steps.",
            "step_count": state["step_count"] + 1
        }

    # ── 2. Build context from retrieved chunks ────────────────────
    chunks_text = ""
    for i, chunk in enumerate(state["retrieved_chunks"]):
        chunks_text += f"\n[{i+1}] Source: {chunk['source_filename']}\n{chunk['content']}\n"

    # ── 3. Build memory context ───────────────────────────────────
    memory_text = ""
    for turn in state["memory"]:
        role    = turn.get("role", "user")
        content = turn.get("content", "")
        memory_text += f"{role.capitalize()}: {content}\n"

    # ── 4. Build full prompt ──────────────────────────────────────
    full_context = f"""
    Previous conversation:
    {memory_text if memory_text else "No previous conversation."}

    Retrieved document chunks:
    {chunks_text if chunks_text else "No chunks retrieved."}

    Plan: {state["plan"]}

    User question: {state["question"]}
    """

    # ── 5. First LLM call — reason and decide on tools ───────────
    messages = [
        SystemMessage(content=AGENT_PROMPT),
        HumanMessage(content=full_context)
    ]

    tool_calls_log = []
    tool_call_count = 0

    try:
        response = llm_with_tools.invoke(messages)

        # ── 6. Handle tool calls if any ──────────────────────────
        while response.tool_calls and tool_call_count < 3:

            for tool_call in response.tool_calls:
                tool_name  = tool_call["name"]
                tool_input = tool_call["args"]

                # Find and call the right tool
                tool_result = _call_tool(tool_name, tool_input)

                # Log the tool call for state
                tool_calls_log.append({
                    "tool_name": tool_name,
                    "input":     tool_input,
                    "output":    tool_result
                })

                tool_call_count += 1

                # Add tool result to messages for next LLM call
                messages.append(response)
                messages.append(
                    ToolMessage(
                        content=str(tool_result),
                        tool_call_id=tool_call["id"]
                    )
                )

            # ── 7. Second LLM call — now with tool results ───────
            if tool_call_count < 3:
                response = llm_with_tools.invoke(messages)
            else:
                break

        # ── 8. Extract final answer ───────────────────────────────
        raw_answer = response.content if response.content else "I could not generate an answer."

    except Exception as e:
        raw_answer     = "I encountered an error while processing your question."
        tool_calls_log = []

    return {
        "answer":     raw_answer,
        "tool_calls": state["tool_calls"] + tool_calls_log,
        "step_count": state["step_count"] + 1
    }


# ── Helper: call the right tool by name ──────────────────────────
def _call_tool(tool_name: str, tool_input: dict) -> str:
    """
    Finds the right tool by name and calls it safely.
    Never crashes — returns error message on failure.
    """
    tool_map = {tool.name: tool for tool in TOOLS}

    if tool_name not in tool_map:
        return f"Tool {tool_name} not found."

    try:
        result = tool_map[tool_name].invoke(tool_input)
        return str(result)
    except Exception as e:
        return f"Tool {tool_name} failed: {str(e)}"
    

# ===================================================
# ── 6. Checker Node ───────────────────────────────
# ===================================================

class CheckerOutput(BaseModel):
    passed: bool = Field(
        description="True if the answer is good enough to send to the user, False if it needs improvement"
    )
    reason: str = Field(
        description="One sentence explaining why it passed or failed"
    )
    issue: str = Field(
        description="What specific issue was found if failed. Empty string if passed.",
        default=""
    )
    suggestion: str = Field(
        description="What the agent should do differently if failed. Empty string if passed.",
        default=""
    )
    
CheckerOutput.model_rebuild()

CHECKER_PROMPT = """
You are a quality control assistant for an internal company knowledge base.
Your job is to evaluate if an answer is good enough to send to the user.

Evaluate the answer against these criteria:

1. GROUNDED    → Is every claim supported by the retrieved chunks? No fabrication?
2. RELEVANT    → Does it actually answer what the user asked?
3. CITED       → Does it mention where the information came from?
4. LANGUAGE    → If the question was in Arabic, is the answer in Arabic?
                 If the question was in English, is the answer in English?
5. COMPLETE    → Is the answer complete or did it cut off mid-sentence?

Rules:
- If ALL 5 criteria pass → passed: True
- If ANY criterion fails → passed: False
- Be strict about fabrication — if you see any claim not in the chunks, fail it
- Be strict about language — wrong language is always a fail
"""


def checker_node(state: AtlasState) -> dict:
    """
    Quality gate between Agent and Answer Composer.
    Passes  → moves to Answer Composer
    Fails   → loops back to Planner (max 2 retries)
    """

    # ── 1. Check retry limit first ────────────────────────────────
    if state["checker_retries"] >= 2:
        # Force pass after 2 retries — don't loop forever
        return {
            "plan":             state["plan"] + " | checker forced pass after max retries",
            "checker_retries":  state["checker_retries"],
            "step_count":       state["step_count"] + 1
        }

    # ── 2. Build evaluation context ───────────────────────────────
    chunks_text = ""
    for i, chunk in enumerate(state["retrieved_chunks"]):
        chunks_text += f"\n[{i+1}] {chunk['source_filename']}:\n{chunk['content']}\n"

    evaluation_context = f"""
User question  : {state["question"]}
Agent answer   : {state["answer"]}

Retrieved chunks used:
{chunks_text if chunks_text else "No chunks were retrieved."}
"""

    # ── 3. Call LLM to evaluate ───────────────────────────────────
    structured_checker = llm.with_structured_output(CheckerOutput)

    try:
        checker_result = structured_checker.invoke([
            SystemMessage(content=CHECKER_PROMPT),
            HumanMessage(content=evaluation_context)
        ])

        passed     = checker_result.passed
        reason     = checker_result.reason
        issue      = checker_result.issue
        suggestion = checker_result.suggestion

    except Exception:
        # On failure, pass anyway — don't block the graph
        passed     = True
        reason     = "Checker failed to evaluate — passing by default"
        issue      = ""
        suggestion = ""

    # ── 4. If failed, update plan with feedback for Planner ───────
    if not passed:
        updated_plan = (
            f"{state['plan']} | "
            f"CHECKER FAILED: {issue} | "
            f"SUGGESTION: {suggestion}"
        )
        return {
            "plan":            updated_plan,
            "checker_retries": state["checker_retries"] + 1,
            "step_count":      state["step_count"] + 1
        }

    # ── 5. Passed — move to Answer Composer ───────────────────────
    return {
        "plan":            state["plan"] + f" | checker passed: {reason}",
        "checker_retries": state["checker_retries"],
        "step_count":      state["step_count"] + 1
    }
    
def should_retry(state: AtlasState) -> str:
    """
    Conditional edge after Checker.
    Reads the plan to decide where to go next.
    """

    # Force pass after max retries
    if state["checker_retries"] >= 2:
        return "composer"

    # Force exit if step limit hit
    if state["step_count"] >= 10:
        return "composer"

    # Check if checker passed or failed
    if "CHECKER FAILED" in state["plan"]:
        return "planner"   # loop back
    else:
        return "composer"  # move forward
    
class ComposerOutput(BaseModel):
    final_answer: str = Field(
        description="The final clean answer in the user's language"
    )
    sources: list[str] = Field(
        description="List of real source filenames cited in the answer"
    )
    language: str = Field(
        description="Language of the answer: en or ar"
    )

ComposerOutput.model_rebuild() 

COMPOSER_PROMPT = """
You are a professional answer formatter for Atlas Industries internal knowledge base.
Your job is to take a raw answer and format it into a clean, cited, professional response.

Rules:
1. LANGUAGE
   - If the user asked in Arabic  → write the entire answer in Arabic
   - If the user asked in English → write the entire answer in English
   - Never mix languages in the answer

2. CITATIONS
   - Every fact must be followed by its source filename in brackets
   - Example: "You must submit within 14 days [FIN-001-travel-reimbursement-policy.md]"
   - Arabic example: "يجب التقديم خلال 14 يوم [FIN-001-travel-reimbursement-policy.md]"
   - Only cite real filenames from the retrieved chunks
   - Never invent a filename

3. SOURCES SECTION
   - End every answer with a Sources section
   - English: "Sources:" followed by the list
   - Arabic:  "المصادر:" followed by the list

4. TONE
   - Professional and concise
   - No filler phrases like "Great question!" or "Certainly!"
   - Get straight to the answer

5. NO FABRICATION
   - If a fact is not in the retrieved chunks, do not include it
   - If the answer is incomplete, say so honestly
"""


def composer_node(state: AtlasState) -> dict:
    """
    Takes the raw agent answer and formats it into
    a clean, cited, professional response.
    Always runs after Checker passes.
    """

    # ── 1. Detect user language ───────────────────────────────────
    question = state["question"]
    arabic_chars = sum(1 for c in question if 0x0600 <= ord(c) <= 0x06FF)
    language = "ar" if arabic_chars / max(len(question.strip()), 1) > 0.3 else "en"

    # ── 2. Build context for composer ─────────────────────────────
    chunks_text = ""
    for i, chunk in enumerate(state["retrieved_chunks"]):
        chunks_text += f"\n[{i+1}] {chunk['source_filename']}:\n{chunk['content']}\n"

    tool_calls_text = ""
    for call in state["tool_calls"]:
        tool_calls_text += (
            f"\nTool: {call['tool_name']}"
            f"\nInput: {call['input']}"
            f"\nOutput: {call['output']}\n"
        )

    composition_context = f"""
    User question  : {question}
    Detected language : {language}
    Raw agent answer  : {state["answer"]}

    Retrieved chunks:
    {chunks_text if chunks_text else "No chunks retrieved."}

    Tool call results:
    {tool_calls_text if tool_calls_text else "No tools were called."}
    """

    # ── 3. Call LLM to format ─────────────────────────────────────
    structured_composer = llm.with_structured_output(ComposerOutput)

    try:
        composer_result = structured_composer.invoke([
            SystemMessage(content=COMPOSER_PROMPT),
            HumanMessage(content=composition_context)
        ])

        final_answer = composer_result.final_answer
        sources      = composer_result.sources
        language     = composer_result.language

    except Exception:
        # Safe fallback — use raw answer with basic sources
        final_answer = state["answer"]
        sources      = list({
            chunk["source_filename"]
            for chunk in state["retrieved_chunks"]
        })
        language     = "en"

    # ── 4. Safety check — never return
    if not final_answer.strip():
        if language == "ar":
            final_answer = "عذراً، هذه المعلومات غير متوفرة في وثائق الشركة."
        else:
            final_answer = "This information is not available in the company documents."
        sources = []

    # ── 5. Safety check — never return fake filenames ─────────────
    real_filenames = {chunk["source_filename"] for chunk in state["retrieved_chunks"]}
    sources        = [s for s in sources if s in real_filenames]

    return {
        "answer":     final_answer,
        "sources":    sources,
        "step_count": state["step_count"] + 1
    }
    
    
    
    
def build_graph():
    """
    Wires all nodes together into the full Atlas graph.
    Returns a compiled graph ready to run.
    """

    # ── 1. Initialize graph with state schema ─────────────────────
    builder = StateGraph(AtlasState)

    # ── 2. Add all nodes ──────────────────────────────────────────
    builder.add_node("memory_loader", memory_loader_node)
    builder.add_node("router",        router_node)
    builder.add_node("planner",       planner_node)
    builder.add_node("retriever",     retriever_node)
    builder.add_node("agent",         agent_node)
    builder.add_node("checker",       checker_node)
    builder.add_node("composer",      composer_node)
    builder.add_node("memory_writer", memory_writer_node)

    # ── 3. Add straight edges ─────────────────────────────────────
    builder.add_edge(START,           "memory_loader")
    builder.add_edge("memory_loader", "router")
    builder.add_edge("router",        "planner")
    builder.add_edge("planner",       "retriever")
    builder.add_edge("retriever",     "agent")
    builder.add_edge("agent",         "checker")

    # ── 4. Add conditional edge after checker ─────────────────────
    builder.add_conditional_edges(
        "checker",
        should_retry,        # the function that decides
        {
            "planner":  "planner",    # loop back if failed
            "composer": "composer"    # move forward if passed
        }
    )

    builder.add_edge("composer",      "memory_writer")
    builder.add_edge("memory_writer", END)

    # ── 5. Compile with memory ────────────────────────────────────
    memory_saver = MemorySaver()
    return builder.compile(checkpointer=memory_saver)


# ── Build the graph once at startup ──────────────────────────────
graph = build_graph()

import uuid

def run(question: str, session_id: str) -> dict:
    """
    Entry point for the UI.
    Member 3 calls this function with every user message.
    Returns the final state with answer + sources.
    """

    # Build initial state
    initial_state: AtlasState = {
        "question":         question,
        "domain":           "unknown",
        "retrieved_chunks": [],
        "tool_calls":       [],
        "answer":           "",
        "sources":          [],
        "session_id":       session_id,
        "run_id":           str(uuid.uuid4()),
        "memory":           [],
        "plan":             "",
        "step_count":       0,
        "checker_retries":  0,
    }

    # Run the graph
    config = {"configurable": {"thread_id": session_id}}
    final_state = graph.invoke(initial_state, config=config)

    return {
        "answer":     final_state["answer"],
        "sources":    final_state["sources"],
        "domain":     final_state["domain"],
        "tool_calls": final_state["tool_calls"],
        "run_id":     final_state["run_id"],
    }