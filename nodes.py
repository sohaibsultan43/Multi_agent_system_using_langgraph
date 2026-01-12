from langchain_openai import ChatOpenAI
from langchain_tavily import TavilySearch
from langchain_core.prompts import ChatPromptTemplate
from state import AgentState
from dotenv import load_dotenv
from credibility import score_url
from pydantic import BaseModel, Field
import re

load_dotenv()
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
# Tavily returns clean text and URLs - much better for AI agents
search_tool = TavilySearch(max_results=3)

# Pydantic model for structured output
class Plan(BaseModel):
    """Structured plan with search queries."""
    queries: list[str] = Field(
        description="List of exactly 3 distinct search queries for researching the topic",
        min_length=3,
        max_length=3
    )

# --- Node 1: The Planner ---
def planner(state: AgentState) -> AgentState:
    """Generate initial research plan based on topic using structured output."""
    topic = state.get('topic', '')
    print(f"---> [planner] \n    Thinking about: {topic}")
    
    # Use structured output for guaranteed format
    structured_llm = llm.with_structured_output(Plan)
    
    system_msg = (
        "You are a research planner. Generate exactly 3 distinct, comprehensive search queries "
        "that would help research the given topic thoroughly. "
        "Each query should target a different aspect of the topic (e.g., overview, applications, trends, challenges)."
    )
    user_msg = f"Topic: {topic}"
    
    try:
        response = structured_llm.invoke([("system", system_msg), ("user", user_msg)])
        plan = response.queries
        
        # Validate we got exactly 3 queries
        if len(plan) != 3:
            print(f"   \n-> Warning: Expected 3 queries, got {len(plan)}. Using fallback.\n")
            plan = [
                f"{topic} overview",
                f"{topic} applications and use cases",
                f"{topic} trends and future developments"
            ]
    except Exception as e:
        print(f"   \n-> Error in structured output: {e}. Using fallback.\n")
        # Fallback to simple queries if structured output fails
        plan = [
            f"{topic} overview",
            f"{topic} applications and use cases",
            f"{topic} trends and future developments"
        ]
    
    print(f"   \n-> Generated {len(plan)} search queries:\n")
    for i, query in enumerate(plan, 1):
        print(f"   {i}. {query}")
    print()
    
    return {"plan": plan, "revision_number": 0}

# --- NODE 2: REAL RESEARCHER ---
def researcher(state: AgentState):
    print("--- [researcher] \nRunning live web searches... ---")
    
    plan = state.get('plan', [])
    existing_data = state.get('research_data', [])
    results = list(existing_data)  # Keep existing research data
    
    if not plan:
        print("   \n-> Warning: No plan found, skipping research\n")
        return {"research_data": results}
    
    # Run searches for all queries in plan (or last 3 if plan is large)
    queries_to_run = plan[-3:] if len(plan) > 3 else plan
    
    for query in queries_to_run:
        # Clean query before searching
        clean_query = query.strip().strip('"').strip("'")
        if not clean_query or clean_query.upper() == "APPROVED":
            continue
            
        print(f"   \n-> Searching: {clean_query}\n")
        try:
            # TavilySearch expects a dict with the query
            search_results = search_tool.invoke({"query": clean_query})
            
            # Tavily returns a dict with a "results" list
            if isinstance(search_results, dict) and "results" in search_results:
                search_results = search_results["results"]
            
            # Tavily returns a list of dicts with 'url' and 'content'
            if isinstance(search_results, list):
                for result in search_results:
                    if isinstance(result, dict):
                        url = result.get('url', '')
                        content = result.get('content', '')
                        
                        # Only add if we have valid data
                        if url and content:
                            results.append({
                                "url": url,
                                "content": content,
                                "query": clean_query
                            })
                            print(f"   ✓ Found: {url[:60]}...")
                    else:
                        # Fallback for unexpected format
                        results.append({
                            "url": f"https://tavily-result-{clean_query.replace(' ', '-')}.com",
                            "content": str(result),
                            "query": clean_query
                        })
            else:
                # Fallback if Tavily returns unexpected format
                print(f"   \n-> Warning: Unexpected Tavily response format\n")
                results.append({
                    "url": f"https://tavily-result-{clean_query.replace(' ', '-')}.com",
                    "content": str(search_results),
                    "query": clean_query
                })
            
        except Exception as e:
            print(f"   \n-> Error searching {clean_query}: {e}\n")
            results.append({
                "url": f"https://error-{clean_query.replace(' ', '-')}.com",
                "content": f"Error searching {clean_query}: {e}",
                "query": clean_query
            })
    
    print(f"   \n-> Total research entries: {len(results)}\n")
    return {"research_data": results}


# --- NODE 3: THE REVIEWER ---
def reviewer(state: AgentState):
    print("--- [reviewer] \nChecking data quality... ---")
    
    # Convert research_data (list of dicts) to readable text for reviewer
    research_data = state.get('research_data', [])
    if isinstance(research_data, list) and research_data and isinstance(research_data[0], dict):
        # New format: list of dictionaries
        data = "\n".join([
            f"Query: {item.get('query', 'Unknown')}\nContent: {item.get('content', '')[:500]}..."
            for item in research_data
        ])
    else:
        # Fallback for old format (strings)
        data = "\n".join([str(item) for item in research_data])
    
    revision_number = state.get('revision_number', 0)
    
    # Ask LLM: Is this information enough?
    prompt = ChatPromptTemplate.from_template(
        """
        You are a research quality reviewer. 
        Topic: {topic}
        Collected Data: {data}
        Current Revision: {revision}
        
        Check if the data is sufficient to write a comprehensive report.
        
        IMPORTANT: Respond in ONE of these formats:
        - If data is sufficient, respond EXACTLY: "APPROVED"
        - If more data is needed, respond with ONLY a search query (no explanations, no "NO" prefix, just the query)
        
        Examples:
        Good: "APPROVED"
        Good: "agentic AI security concerns 2025"
        Bad: "NO, please search for agentic AI security concerns 2025"
        """
    )
    chain = prompt | llm
    response = chain.invoke({
        "topic": state['topic'], 
        "data": data,
        "revision": revision_number
    })
    
    review_text = response.content.strip()
    print(f"   \n-> Review result: {review_text[:80]}...\n")
    
    return {"review": review_text}

# --- NODE 4: SYNTHESIZER ---
def synthesizer_node(state: AgentState):
    """Filter low-quality sources and prepare clean notes for the writer."""
    print("--- [synthesizer] \nFiltering & Organizing Data... ---")
    
    raw_data = state.get('research_data', [])
    clean_data = []
    dropped_count = 0
    
    if not raw_data:
        print("   \n-> Warning: No research data to synthesize\n")
        return {"synthesized_notes": ""}
    
    for item in raw_data:
        # Handle both old format (strings) and new format (dicts)
        if isinstance(item, dict):
            url = item.get('url', '')
            content = item.get('content', '')
            query = item.get('query', 'Unknown')
        else:
            # Fallback: try to extract URL from string
            url_match = re.search(r'https?://[^\s\)]+', str(item))
            url = url_match.group(0) if url_match else f"https://unknown-source.com"
            content = str(item)
            query = "Unknown"
        
        # 1. Score the URL
        url_score_result = score_url(url)
        score = url_score_result['score']
        
        # 2. Filter: If score is too low, ignore it
        if score < 40:
            dropped_count += 1
            print(f"   \n-> Dropping low quality source: {url[:60]}... (Score: {score})\n")
            continue
            
        # 3. Format valid data with credibility score
        clean_data.append(
            f"SOURCE: {url} (Credibility Score: {score}/100)\n"
            f"QUERY: {query}\n"
            f"CONTENT: {content}\n"
        )
    
    # 4. Combine all valid sources
    combined_notes = "\n---\n".join(clean_data)
    
    print(f"   \n-> Kept {len(clean_data)} high-quality sources, dropped {dropped_count} low-quality sources\n")
    
    return {"synthesized_notes": combined_notes}

# --- NODE 5: Human Review Checkpoint ---
def human_review_checkpoint(state: AgentState):
    """Checkpoint node that signals human review is needed before writing."""
    print("--- [human review] \nCheckpoint reached - waiting for approval ---")
    # This node just marks that we're ready for human review
    # The actual input will be handled in main.py
    return {"human_review_ready": True}

# --- NODE 6: SMART WRITER ---
def writer(state: AgentState):
    """Generate final comprehensive report from synthesized notes."""
    print("--- [writer] \nWriting final report... ---")
    
    topic = state.get('topic', 'Unknown Topic')
    
    # Use synthesized_notes if available (filtered, high-quality data)
    # Otherwise fall back to raw research_data
    synthesized_notes = state.get('synthesized_notes', '')
    
    if synthesized_notes:
        data_text = synthesized_notes
        print("   \n-> Using synthesized (filtered) notes for report\n")
    else:
        # Fallback: use raw research_data
        research_data = state.get('research_data', [])
        if not research_data:
            print("   \n-> Warning: No research data available\n")
            return {"final_report": f"Report on {topic}: No research data was collected."}
        
        # Convert dict format to text if needed
        if isinstance(research_data, list) and research_data and isinstance(research_data[0], dict):
            data_text = "\n".join([
                f"Query: {item.get('query', '')}\nContent: {item.get('content', '')}"
                for item in research_data
            ])
        else:
            data_text = "\n".join([str(item) for item in research_data])
        print("   \n-> Using raw research data (no synthesis available)\n")
    
    prompt = ChatPromptTemplate.from_template(
        """
        Write a comprehensive, professional report on: {topic}
        
        Use the following research data to create a well-structured report:
        {data}
        
        Requirements:
        - Include an Executive Summary
        - Organize content into clear sections with headers
        - Cite specific information from the research data
        - Include a conclusion and recommendations
        - Use professional language and formatting
        - Make it comprehensive but concise
        """
    )
    chain = prompt | llm
    response = chain.invoke({
        "topic": topic, 
        "data": data_text
    })
    
    print("   \n-> Report generated successfully\n")
    return {"final_report": response.content}

# --- NODE 5: Replanner node ---
def replan_node(state: AgentState):
    """Extract clean query from reviewer feedback and update plan."""
    review = state.get('review', '').strip()
    revision_number = state.get('revision_number', 0)
    
    # Clean up the review text to extract just the query
    # Remove common prefixes that might appear
    query = review
    prefixes_to_remove = [
        "NO, ",
        "NO, new search query:",
        "new search query:",
        "Please search for:",
        "Search for:",
        "Query:",
    ]
    
    for prefix in prefixes_to_remove:
        if query.lower().startswith(prefix.lower()):
            query = query[len(prefix):].strip()
    
    # Remove quotes if present
    query = query.strip('"').strip("'").strip()
    
    # If query is empty or still contains "APPROVED", something went wrong
    if not query or "APPROVED" in query.upper():
        query = f"additional information about {state.get('topic', 'the topic')}"
    
    new_revision = revision_number + 1
    print(f"--- [replan] \nAdding query (revision {new_revision}): {query}")
    
    return {"plan": [query], "revision_number": new_revision}



