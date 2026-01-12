from langchain_openai import ChatOpenAI
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.prompts import ChatPromptTemplate
from state import AgentState
from dotenv import load_dotenv

load_dotenv()
llm= ChatOpenAI(model="gpt-4o-mini", temperature=0)
search_tool = DuckDuckGoSearchRun()

# --- Node 1: The Planner ---
def planner(state: AgentState) -> AgentState:
    print (f"--- [Planner] Thinking about :{state['topic']}")
    system_msg="you are research planner, Return only a comma separated list of 3 distinct search queries."
    user_msg=f"topic: {state['topic']}"
    response =llm.invoke([("system" , system_msg), ("user", user_msg)])
    plan=[q.strip() for q in response.content.split(",")]

    return{"plan": plan, "revision_number": 0}

# --- NODE 2: REAL RESEARCHER ---
def researcher(state: AgentState):
    print("--- [RESEARCHER] Running live web searches... ---")
    
    plan = state['plan']
    results = []
    
    # We only run the search queries that haven't been run yet 
    # (Simplified logic: just run the last 3 in the plan)
    for query in plan[-3:]: 
        print(f"   -> Searching: {query}")
        try:
            # ACTUAL WEB SEARCH HAPPENS HERE
            res = search_tool.invoke(query)
            results.append(f"Query: {query}\nResult: {res}\n")
        except Exception as e:
            results.append(f"Error searching {query}: {e}")
            
    return {"research_data": results}


# --- NODE 3: THE WRITER ---
def reviewer(state: AgentState):
    print("--- [REVIEWER] Checking data quality... ---")
    
    data = "\n".join(state['research_data'])
    
    # Ask LLM: Is this information enough?
    prompt = ChatPromptTemplate.from_template(
        """
        You are a harsh research critic. 
        Topic: {topic}
        Collected Data: {data}
        
        Check if the data is sufficient to write a comprehensive report.
        If YES, respond exactly with "APPROVED".
        If NO, respond with a new search query to fill the gap.
        """
    )
    chain = prompt | llm
    response = chain.invoke({"topic": state['topic'], "data": data})
    
    return {"review": response.content}

# --- NODE 4: SMART WRITER ---
def writer(state: AgentState):
    print("--- [WRITER] Writing final report... ---")
    
    prompt = ChatPromptTemplate.from_template(
        """
        Write a professional report on: {topic}
        Use the following research data:
        {data}
        """
    )
    chain = prompt | llm
    response = chain.invoke({
        "topic": state['topic'], 
        "data": "\n".join(state['research_data'])
    })
    
    return {"final_report": response.content}