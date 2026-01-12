#import stehe states defination we just created
from state import AgentState

# --- Node 1: The Planner ---
def planner(state: AgentState) -> AgentState:
    """
    Role:Receives the user topic and breaks it down into search queries.
    """
    print (f"--- [Planner] Thinking about :{state['topic']}")

    topic = state['topic']
    generated_plan = [
        f"what is {topic}",
        f"history of {topic}",
        f"future of {topic}"
    ]

    return{"plan": generated_plan}

#--- NODE 2: THE RESEARCHER ---
def researcher(state: AgentState):
    """
    Role: Takes the plan and finds information.
    """
    print("--- [RESEARCHER] Browsing the web... ---")
    
    # LOGIC: We look at the 'plan' from the state.
    plan = state['plan']
    results = []
    
    # We simulate searching the web for each item in the plan
    for query in plan:
        print(f"   -> Searching for: {query}")
        # In a real app, you would call a Search API (like Tavily or Google) here.
        # We simulate finding a result:
        mock_result = f"Found reliable info about: {query}"
        results.append(mock_result)
        
    # RETURN: We return 'research_data'. 
    # Because we used 'operator.add' in state.py, these results gets APPENDED to the memory.
    return {"research_data": results}

    # --- NODE 3: THE WRITER ---
def writer(state: AgentState):
    """
    Role: Reads the collected data and writes the final answer.
    """
    print("--- [WRITER] Writing report... ---")
    
    # LOGIC: Pull the data from state
    data = state['research_data']
    topic = state['topic']
    
    # Simulate writing a report by joining the data strings
    draft = f"FINAL REPORT ON: {topic}\n"
    draft += "--------------------------------\n"
    draft += "\n".join(data)
    
    # RETURN: Update the 'final_report' key in the state.
    return {"final_report": draft}