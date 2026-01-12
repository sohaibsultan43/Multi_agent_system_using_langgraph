from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from state import AgentState
from nodes import planner, reviewer, researcher, replan_node, writer, human_review_checkpoint, synthesizer_node


def should_continue(state: AgentState):
    """Decide next step based on reviewer feedback."""
    review = state.get('review', "").strip().upper()
    revision_number = state.get('revision_number', 0)

    # Max revisions reached - ready for human review before writing
    if revision_number >= 3:
        print("-> [Decision] Max revisions reached. Ready for human review.")
        return "human_review"
    
    # Review approved - ready for human review before writing
    if "APPROVED" in review:
        print("-> [Decision] Review approved. Ready for human review.")
        return "human_review"
    
    # Need more research - go to replan
    print(f"-> [Decision] More research needed (revision {revision_number + 1}/3).")
    return "replan"



workflow = StateGraph(AgentState)

workflow.add_node("planner", planner)
workflow.add_node("researcher", researcher)
workflow.add_node("reviewer", reviewer)
workflow.add_node("human_review", human_review_checkpoint)
workflow.add_node("synthesizer", synthesizer_node)
workflow.add_node("writer", writer)
workflow.add_node("replan", replan_node)

workflow.set_entry_point("planner")
workflow.add_edge("planner", "researcher")
workflow.add_edge("researcher", "reviewer")
workflow.add_conditional_edges("reviewer", should_continue, {
    "replan": "replan",
    "human_review": "human_review"
})
workflow.add_edge("replan", "researcher")
workflow.add_edge("human_review", "synthesizer")  # Synthesize before writing
workflow.add_edge("synthesizer", "writer")
workflow.add_edge("writer", END)



memory = MemorySaver()


app=workflow.compile(checkpointer=memory)


if __name__ == "__main__":
    thread = {"configurable": {"thread_id": "terminal_run"}}
    initial_input = {"topic": "Agentic AI trends 2025"}

    print("\n============================================================")
    print("            Multi-Agent Research System (Terminal)")
    print("============================================================")
    print(f"Topic: {initial_input['topic']}")
    print("============================================================\n")

    # One-shot run: invoke the graph and print the final report
    result = app.invoke(initial_input, config=thread)

    if "final_report" in result:
        print("============================================================")
        print("                        FINAL REPORT")
        print("============================================================\n")
        print(result["final_report"])
        print("\n============================================================\n")
    else:
        print("\nNo final report was produced.")
