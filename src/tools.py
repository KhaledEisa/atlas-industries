from pydantic import BaseModel, Field
from langchain_core.tools import tool
from src.retriever import faiss_index, embeddings

# ── Tool 1: Policy Lookup ─────────────────────────────────────────
class PolicyLookupInput(BaseModel):
    policy_id: str = Field(
        description="Policy document ID e.g. FIN-001, HR-006, IT-002"
    )

@tool("PolicyLookup", args_schema=PolicyLookupInput)
def policy_lookup(policy_id: str) -> str:
    """
    Looks up a specific policy document by its ID.
    Use when the user asks about a specific policy number.
    """
    try:
        # Search FAISS for this specific policy ID
        retriever = faiss_index.as_retriever(
            search_kwargs={
                "k": 3,
                "filter": {"source_filename": {"$contains": policy_id}}
            }
        )
        results = retriever.invoke(policy_id)

        if not results:
            return f"Policy {policy_id} not found in the corpus."

        return "\n\n".join([doc.page_content for doc in results])

    except Exception as e:
        return f"Could not retrieve policy {policy_id}: {str(e)}"


# ── Tool 2: Reimbursement Calculator ─────────────────────────────
class ReimbursementInput(BaseModel):
    category:  str = Field(description="One of: hotel, meals, transport")
    days:      int = Field(description="Number of days of the trip")
    trip_type: str = Field(description="One of: domestic, international")

@tool("ReimbursementCalculator", args_schema=ReimbursementInput)
def reimbursement_calculator(category: str, days: int, trip_type: str) -> dict:
    """
    Calculates reimbursement total based on category, days, and trip type.
    Use when the user asks about totals or caps for expenses.
    """
    try:
        # Caps per Atlas Finance policy
        CAPS = {
            "domestic": {
                "hotel":     1500,
                "meals":     200,
                "transport": 300,
            },
            "international": {
                "hotel":     3000,
                "meals":     500,
                "transport": 800,
            }
        }

        trip_type = trip_type.lower().strip()
        category  = category.lower().strip()

        if trip_type not in CAPS:
            return {"error": f"Unknown trip type: {trip_type}. Use domestic or international."}

        if category not in CAPS[trip_type]:
            return {"error": f"Unknown category: {category}. Use hotel, meals, or transport."}

        cap_per_day = CAPS[trip_type][category]
        total       = cap_per_day * days

        return {
            "category":    category,
            "trip_type":   trip_type,
            "days":        days,
            "cap_per_day": cap_per_day,
            "total":       total,
            "currency":    "EGP"
        }

    except Exception as e:
        return {"error": str(e)}


# ── Tool 3: Leave Types Lister ────────────────────────────────────
class LeaveTypesInput(BaseModel):
    employee_type: str = Field(
        description="Optional filter: full_time, part_time, or all",
        default="all"
    )

@tool("LeaveTypesLister", args_schema=LeaveTypesInput)
def leave_types_lister(employee_type: str = "all") -> dict:
    """
    Lists all available leave types and their allowed days.
    Use when the user asks about leave, vacation, or time off types.
    """
    try:
        LEAVE_TYPES = {
            "full_time": [
                {"type": "Annual Leave",      "days": 21},
                {"type": "Sick Leave",        "days": 14},
                {"type": "Maternity Leave",   "days": 90},
                {"type": "Paternity Leave",   "days": 5},
                {"type": "Emergency Leave",   "days": 3},
                {"type": "Unpaid Leave",      "days": "unlimited, manager approval required"},
            ],
            "part_time": [
                {"type": "Annual Leave",      "days": 10},
                {"type": "Sick Leave",        "days": 7},
                {"type": "Emergency Leave",   "days": 3},
            ]
        }

        employee_type = employee_type.lower().strip()

        if employee_type == "all":
            return {"leave_types": LEAVE_TYPES}

        if employee_type not in LEAVE_TYPES:
            return {"error": f"Unknown employee type: {employee_type}. Use full_time, part_time, or all."}

        return {"leave_types": {employee_type: LEAVE_TYPES[employee_type]}}

    except Exception as e:
        return {"error": str(e)}


# ── Export all tools as a list ────────────────────────────────────
TOOLS = [policy_lookup, reimbursement_calculator, leave_types_lister]