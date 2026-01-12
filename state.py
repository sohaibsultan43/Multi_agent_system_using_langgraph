import operator
from typing import Annotated, List, TypedDict
#we define a class called 'AgentState'
#It inherits from TypedDict, which means it works like a regular Python dictionary
#but with type hints (helpful for coding tools)

class AgentState(TypedDict):
    topic: str
    plan: List[str]
    # Changed from List[str] to List[dict] to store URL and content with scores
    research_data: Annotated[List[dict], operator.add]
    synthesized_notes: str  # Clean, filtered notes for the writer
    final_report: str
    review: str
    revision_number: int
    human_review_ready: bool