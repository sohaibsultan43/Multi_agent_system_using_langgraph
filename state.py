import operator
from typing import Annotated, List, TypedDict
#we define a class called 'AgentState'
#It inherits from TypedDict, which means it works like a regular Python dictionary
#but with type hints (helpful for coding tools)

class AgentState(TypedDict):
    topic: str
    plan: List[str]
    research_data: Annotated[List[str], operator.add]
    final_report: str