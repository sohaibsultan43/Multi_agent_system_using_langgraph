from langgraph.graph import StateGraph, END

from state import AgentState
from nodes import planner, researcher, writer

workflow = StateGraph(AgentState)
workflow.add_node("planner", planner)
workflow.add_node("researcher", researcher)
workflow.add_node("writer", writer)

workflow.set_entry_point("planner")

workflow.add_edge("planner", "researcher")
workflow.add_edge("researcher", "writer")
workflow.add_edge("writer", END)

app = workflow.compile()

if __name__ == "__main__":
    print("Initializing Multiagent System...")
    input={"topic": "Deep Learning"}
    result = app.invoke(input)

    print("\nFinal Report:")
    print(result["final_report"])
