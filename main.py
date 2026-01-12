from langgraph.graph import StateGraph, END
from state import AgentState
from nodes import planner, researcher, writer, reviewer


def should_continue(state: AgentState):
    """
    Decide the next step based on the Reviewer's feedback.
    """
    review = state['review']
    revision_number = state['revision_number']

    if revision_number > 3:
        print("-> [Decision] Max revision reached. Writing report now.")
        return "writer"
    if "APPROVED" in review:
        print("-> [Decision] Review approved. Writing report now.")
        return "writer"
    print(f"-> [Decision] Research missing info. New query: {review}")
    return "researcher"

def replan_node(state:AgentState):
    new_query = state['review']
    new_revision = state['revision_number'] + 1
    return {"plan": [new_query], "revision_number": new_revision}
workflow = StateGraph(AgentState)
workflow.add_node("planner", planner)
workflow.add_node("researcher", researcher)
workflow.add_node("writer", writer)
workflow.add_node("replan", replan_node)
workflow.add_node("reviewer", reviewer)

workflow.set_entry_point("planner")

# Base edges for one full iteration
workflow.add_edge("planner", "researcher")
workflow.add_edge("researcher", "reviewer")
workflow.add_conditional_edges(
    "reviewer",
    should_continue,
    {
        "researcher":"replan",
        "writer":"writer"
    }
)

workflow.add_edge("replan", "reviewer")
workflow.add_edge("writer", END)

app = workflow.compile()
if __name__ == "__main__":
    inputs = {"topic": "DeepSeek R1 Model details"}
    print(f"Starting Deep Research on: {inputs['topic']}...\n")
    
    result = app.invoke(inputs)
    
    print("\n\n========================================")
    print("FINAL GENERATED REPORT")
    print("========================================")
    print(result['final_report'])