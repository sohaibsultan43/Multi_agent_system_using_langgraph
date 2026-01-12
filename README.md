# Multi-Agent Research System

Terminal-first, multi-agent research workflow with credibility scoring, synthesis, and structured reporting.

## Features
- **Planner (Pydantic structured output):** Generates exactly 3 focused queries.
- **Researcher (Tavily):** Fetches clean results; stores `url`, `content`, `query`.
- **Credibility scoring:** `score_url` (0–100) boosts trusted domains (.gov/.edu/.org/.mil, Wikipedia, arXiv, etc.) and drops low-quality sources (<40).
- **Synthesizer:** Filters low-credibility sources and produces curated notes for the writer.
- **Writer:** Produces a professional report (exec summary, sections, citations from data, conclusion, recommendations).
- **One-shot terminal run:** `python main.py` — prints the final report with clear separators.

## Requirements
- Python 3.12+
- Environment variables in `.env`:
  ```env
  OPENAI_API_KEY=your_openai_key
  TAVILY_API_KEY=your_tavily_key
  ```

## Install
```bash
python -m venv .venv
.venv\Scripts\activate          # Windows PowerShell
pip install -r requirements.txt
```

## Run (Terminal)
```bash
.venv\Scripts\activate
python main.py
```
Output is printed to the console with a professional header and a FINAL REPORT block.

## Project Structure
- `main.py` — builds/compiles the LangGraph and runs one-shot report generation.
- `nodes.py` — agent nodes: planner, researcher (Tavily), reviewer, synthesizer, writer, replan, human_review checkpoint.
- `state.py` — `AgentState` schema (topic, plan, research_data as list[dict], synthesized_notes, review, revision_number, human_review_ready, final_report).
- `credibility.py` — URL scoring helper.
- `requirements.txt` — dependencies (langgraph, langchain, langchain-tavily, pydantic, python-dotenv).

## How It Works (Flow)
1) **Planner** → produces 3 queries (structured output via Pydantic).
2) **Researcher** → uses Tavily to fetch results; stores `url`, `content`, `query`.
3) **Reviewer** → decides APPROVED vs. needs more queries.
4) **Replan** (if needed) → cleans reviewer query and loops back to research.
5) **Synthesizer** → drops low-score sources; builds curated notes.
6) **Writer** → generates the final professional report from synthesized notes.

## Credibility Heuristics (credibility.py)
- +30 for trusted TLDs (.gov/.edu/.org/.mil)
- +20 for authoritative domains (wikipedia, arxiv, nih, etc.)
- +10 for https, -10 for http
- -20 for suspicious hosts (blogspot, wordpress, wixsite, etc.)
- Path hints (+15 for /research|/paper|/publication, -5 for /blog|/post)
- Sources with score <40 are dropped; `is_trusted` if score >65.

