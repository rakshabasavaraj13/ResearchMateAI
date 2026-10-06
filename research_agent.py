
# ============================================================
# Gemini LLM Setup
# ============================================================

import os

try:
    from langchain_google_genai import ChatGoogleGenerativeAI

    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

    if not GOOGLE_API_KEY:
        try:
            from google.colab import userdata
            GOOGLE_API_KEY = userdata.get("GOOGLE_API_KEY")
            os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY
        except Exception:
            pass

    planner_llm = ChatGoogleGenerativeAI(
        model="gemini-3.5-flash-lite",
        google_api_key=GOOGLE_API_KEY,
        temperature=0.2
    )

except Exception as e:
    print("Gemini initialization error:", e)
    planner_llm = None



# ============================================================
# ResearchMate AI - Configuration
# ============================================================

import os
import json
import re
import requests
from typing import *

# Gemini configuration
os.environ["GOOGLE_API_KEY"] = os.environ.get(
    "GOOGLE_API_KEY",
    ""
)

os.environ["FAST_LLM"] = "google_genai:gemini-3.5-flash-lite"
os.environ["SMART_LLM"] = "google_genai:gemini-3.5-flash-lite"
os.environ["STRATEGIC_LLM"] = "google_genai:gemini-3.5-flash-lite"

# Academic search
os.environ["RETRIEVER"] = "tavily"

# ============================================================
# ResearchMate AI - Autonomous Academic Research Engine
# ============================================================

def create_research_plan(topic):

    prompt = f"""
You are an academic research planning agent.

Research topic:
{topic}

Create a research plan for a comprehensive literature survey.

Return ONLY valid JSON in exactly this format:

{{
  "research_objective": "one sentence objective",
  "research_questions": [
    "question 1",
    "question 2",
    "question 3",
    "question 4",
    "question 5",
    "question 6",
    "question 7"
  ],
  "literature_themes": [
    "theme 1",
    "theme 2",
    "theme 3",
    "theme 4",
    "theme 5"
  ]
}}

The 7 research questions must cover:
- background
- major applications
- current methods
- existing research findings
- challenges
- research gaps
- future directions
"""

    response = planner_llm.invoke(prompt)

    # Gemini may return structured content
    if isinstance(response.content, list):
        text = ""
        for item in response.content:
            if isinstance(item, dict) and item.get("type") == "text":
                text += item.get("text", "")
            elif isinstance(item, str):
                text += item
    else:
        text = str(response.content)

    # Remove possible markdown code fences
    text = text.strip()

    if text.startswith("```"):
        text = text.replace("```json", "").replace("```", "").strip()

    return json.loads(text)



# ============================================================

# ============================================================

# ============================================================

# ============================================================

# ============================================================
# Academic Report Generation LLM
# ============================================================

try:
    report_llm = ChatGoogleGenerativeAI(
        model="gemini-3.5-flash-lite",
        google_api_key=GOOGLE_API_KEY,
        temperature=0.2
    )
except Exception:
    report_llm = planner_llm


# Literature Survey LLM
# ============================================================

try:
    survey_llm = ChatGoogleGenerativeAI(
        model="gemini-3.5-flash-lite",
        google_api_key=GOOGLE_API_KEY,
        temperature=0.2
    )
except Exception:
    survey_llm = planner_llm


# Research Gap Analysis LLM
# ============================================================

try:
    gap_llm = ChatGoogleGenerativeAI(
        model="gemini-3.5-flash-lite",
        google_api_key=GOOGLE_API_KEY,
        temperature=0.2
    )
except Exception:
    gap_llm = planner_llm


# Literature Comparison LLM
# ============================================================

try:
    comparison_llm = ChatGoogleGenerativeAI(
        model="gemini-3.5-flash-lite",
        google_api_key=GOOGLE_API_KEY,
        temperature=0.2
    )
except Exception:
    comparison_llm = planner_llm


# Search Query Cleaning Helper
# ============================================================

def clean_search_query(text, max_words=10):
    """Convert a research question into a concise academic search query."""
    import re

    text = str(text)

    # Remove common question words
    text = re.sub(
        r"\b(what|how|why|which|who|where|when|does|do|can|could|should|is|are)\b",
        "",
        text,
        flags=re.IGNORECASE
    )

    # Remove punctuation
    text = re.sub(r"[^\w\s-]", " ", text)

    # Normalize whitespace
    words = text.split()

    return " ".join(words[:max_words])




def search_openalex_targeted(topic, research_plan, papers_per_query=3):
    """
    Robust academic literature search.

    Primary source:
        Semantic Scholar Academic Graph API

    Fallback:
        OpenAlex

    Results are normalized into the format expected by
    the rest of ResearchMate AI.
    """

    import requests
    import time

    queries = [topic]

    # Add research questions
    for question in research_plan.get("research_questions", []):
        short_query = clean_search_query(question)

        if short_query:
            queries.append(f"{topic} {short_query}")

    # Add literature themes
    for theme in research_plan.get("literature_themes", []):
        short_theme = clean_search_query(theme)

        if short_theme:
            queries.append(f"{topic} {short_theme}")

    # Remove duplicate queries
    queries = list(dict.fromkeys(queries))

    papers = {}

    semantic_url = (
        "https://api.semanticscholar.org/"
        "graph/v1/paper/search"
    )

    print("=" * 70)

    for query_index, query in enumerate(queries):

        print(f"🔎 Searching academic literature: {query}")

        params = {
            "query": query,
            "limit": papers_per_query,
            "fields": (
                "paperId,title,abstract,year,"
                "citationCount,authors,venue,"
                "url,externalIds,publicationTypes"
            )
        }

        success = False

        # ----------------------------------------------------
        # Semantic Scholar
        # ----------------------------------------------------

        for attempt in range(2):

            try:

                if query_index > 0:
                    time.sleep(1.0)

                response = requests.get(
                    semantic_url,
                    params=params,
                    timeout=30
                )

                if response.status_code == 429:

                    wait = 5 * (attempt + 1)

                    print(
                        f"⚠️ Semantic Scholar rate limit. "
                        f"Waiting {wait}s..."
                    )

                    time.sleep(wait)
                    continue

                response.raise_for_status()

                data = response.json()

                for item in data.get("data", []):

                    abstract = item.get("abstract")

                    if not abstract:
                        continue

                    paper_id = item.get("paperId")

                    if not paper_id:
                        continue

                    authors = []

                    for author in item.get("authors", []):

                        name = author.get("name")

                        if name:
                            authors.append(name)

                    external_ids = item.get(
                        "externalIds"
                    ) or {}

                    doi = external_ids.get("DOI")

                    papers[paper_id] = {
                        "id": paper_id,
                        "title": item.get("title", ""),
                        "year": item.get("year"),
                        "cited_by_count": (
                            item.get("citationCount") or 0
                        ),
                        "doi": (
                            f"https://doi.org/{doi}"
                            if doi
                            else None
                        ),
                        "abstract": abstract,
                        "authors": authors,
                        "venue": item.get("venue"),
                        "url": item.get("url"),
                        "source": "Semantic Scholar"
                    }

                success = True
                break

            except Exception as e:

                print(
                    f"⚠️ Semantic Scholar request failed: {e}"
                )

                if attempt == 0:
                    time.sleep(3)

        # ----------------------------------------------------
        # OpenAlex fallback for this query
        # ----------------------------------------------------

        if not success:

            print(
                "↪ Trying OpenAlex fallback..."
            )

            try:

                openalex_params = {
                    "search": query,
                    "per-page": papers_per_query,
                    "filter": "has_abstract:true"
                }

                response = requests.get(
                    "https://api.openalex.org/works",
                    params=openalex_params,
                    timeout=30
                )

                if response.status_code == 200:

                    data = response.json()

                    for item in data.get("results", []):

                        paper_id = item.get("id")

                        if not paper_id:
                            continue

                        abstract = ""

                        inverted_index = item.get(
                            "abstract_inverted_index"
                        )

                        if inverted_index:

                            words = []

                            for word, positions in inverted_index.items():

                                for position in positions:
                                    words.append(
                                        (position, word)
                                    )

                            words.sort(
                                key=lambda x: x[0]
                            )

                            abstract = " ".join(
                                word for _, word in words
                            )

                        if not abstract:
                            continue

                        papers[paper_id] = {
                            "id": paper_id,
                            "title": item.get("title", ""),
                            "year": item.get(
                                "publication_year"
                            ),
                            "cited_by_count": item.get(
                                "cited_by_count", 0
                            ),
                            "doi": item.get("doi"),
                            "abstract": abstract,
                            "authors": [
                                author.get(
                                    "author", {}
                                ).get(
                                    "display_name"
                                )
                                for author in item.get(
                                    "authorships", []
                                )
                                if author.get("author")
                            ],
                            "venue": (
                                item.get(
                                    "primary_location",
                                    {}
                                )
                                .get("source", {})
                                .get("display_name")
                            ),
                            "source": "OpenAlex"
                        }

                else:

                    print(
                        "⚠️ OpenAlex fallback unavailable:",
                        response.status_code
                    )

            except Exception as e:

                print(
                    f"⚠️ OpenAlex fallback failed: {e}"
                )

    print("=" * 70)
    print(
        f"Unique academic papers collected: "
        f"{len(papers)}"
    )
    print("=" * 70)

    return list(papers.values())

def select_best_papers(papers, max_papers=15):
    """
    Select the strongest papers for detailed analysis.

    Priority:
    1. Papers with abstracts
    2. Higher citation count
    3. More recent publications
    """

    usable = [
        paper for paper in papers
        if paper.get("abstract")
    ]

    usable.sort(
        key=lambda p: (
            p.get("cited_by_count", p.get("cited_by", 0)),
            p.get("year", 0)
        ),
        reverse=True
    )

    selected = usable[:max_papers]

    print("=" * 80)
    print(f"Selected {len(selected)} papers for detailed analysis")
    print("=" * 80)

    for i, paper in enumerate(selected, 1):
        print(
            f"{i}. {paper['title']} "
            f"({paper['year']}) — "
            f"{paper.get('cited_by_count', paper.get('cited_by', 0))} citations"
        )

    return selected



# ============================================================
# Individual Academic Paper Analyzer
# ============================================================

def analyze_paper_with_abstract(paper):
    """Analyze one academic paper using its abstract."""

    title = paper.get("title", "")
    abstract = paper.get("abstract", "")
    year = paper.get("year", "")
    citations = paper.get("cited_by_count", 0)

    if not abstract:
        return None

    prompt = f"""
You are an academic research analyst.

Analyze the following research paper for a literature survey.

Paper Title:
{title}

Publication Year:
{year}

Citation Count:
{citations}

Abstract:
{abstract}

Return ONLY valid JSON with exactly these fields:

{{
  "research_problem": "...",
  "methodology": "...",
  "key_findings": "...",
  "limitations": "...",
  "research_theme": "..."
}}

Rules:
- Base the analysis only on the information available in the abstract.
- Do not invent details.
- Keep each field concise but academically useful.
"""

    try:
        response = planner_llm.invoke(prompt)

        content = response.content

        # Gemini may return structured content blocks
        if isinstance(content, list):
            parts = []

            for block in content:
                if isinstance(block, dict):
                    if "text" in block:
                        parts.append(str(block["text"]))
                elif hasattr(block, "text"):
                    parts.append(str(block.text))
                else:
                    parts.append(str(block))

            content = "\n".join(parts)

        content = str(content).strip()

        # Remove markdown JSON fences if Gemini adds them
        content = re.sub(r"^```json\s*", "", content)
        content = re.sub(r"^```\s*", "", content)
        content = re.sub(r"\s*```$", "", content)

        return json.loads(content)

    except Exception as e:
        print(f"Analysis error for '{title}': {e}")
        return None


def analyze_papers(papers, topic):

    analyzed = []

    for i, paper in enumerate(papers, 1):

        if not paper.get("abstract"):
            print(f"Skipping paper {i}: No abstract available")
            continue

        print(f"Analyzing paper {i}/{len(papers)}...")

        try:
            analysis = analyze_paper_with_abstract(paper)

            analyzed.append({
                "title": paper["title"],
                "year": paper["year"],
                "doi": paper["doi"],
                "citations": paper.get("cited_by_count", paper.get("cited_by", 0)),
                "abstract": paper["abstract"],
                "analysis": analysis
            })

        except Exception as e:
            print(f"Could not analyze paper {i}: {e}")

    return analyzed


def compare_literature(analyzed_papers, topic):

    literature_data = ""

    for i, paper in enumerate(analyzed_papers, 1):

        analysis = paper["analysis"]

        literature_data += f"""
PAPER {i}
Title: {paper["title"]}
Year: {paper["year"]}
Citations: {paper["citations"]}

Research Problem:
{analysis["research_problem"]}

Methodology:
{analysis["methodology"]}

Key Findings:
{analysis["key_findings"]}

Limitations:
{analysis["limitations"]}

Research Theme:
{analysis["research_theme"]}

-----------------------------------
"""

    prompt = f"""
You are an academic literature comparison agent.

Research topic:
{topic}

Below is a collection of analyzed academic papers:

{literature_data}

Compare these studies and return ONLY valid JSON using this structure:

{{
  "common_findings": [
    "finding 1",
    "finding 2",
    "finding 3"
  ],
  "methodological_patterns": [
    "pattern 1",
    "pattern 2",
    "pattern 3"
  ],
  "key_differences": [
    "difference 1",
    "difference 2",
    "difference 3"
  ],
  "common_limitations": [
    "limitation 1",
    "limitation 2",
    "limitation 3"
  ],
  "research_gaps": [
    "gap 1",
    "gap 2",
    "gap 3"
  ],
  "future_directions": [
    "direction 1",
    "direction 2",
    "direction 3"
  ]
}}

Important:
- Base the comparison ONLY on the supplied paper analyses.
- Do not invent specific results.
- If the evidence is insufficient for a claim, say so.
"""

    response = comparison_llm.invoke(prompt)

    if isinstance(response.content, list):
        text = ""

        for item in response.content:
            if isinstance(item, dict) and item.get("type") == "text":
                text += item.get("text", "")
            elif isinstance(item, str):
                text += item

    else:
        text = str(response.content)

    text = text.strip()

    if text.startswith("```"):
        text = text.replace("```json", "").replace("```", "").strip()

    return json.loads(text)


def generate_research_gap(topic, comparison):

    prompt = f"""
You are a research gap identification agent.

Research Topic:
{topic}

Literature comparison:
{json.dumps(comparison, indent=2)}

Identify research gaps based ONLY on the literature comparison.

Return ONLY valid JSON in this format:

{{
  "major_research_gap": "The most important unresolved research gap.",
  "supporting_gaps": [
    "Supporting gap 1",
    "Supporting gap 2",
    "Supporting gap 3"
  ],
  "why_gap_matters": "Why addressing this gap is important.",
  "possible_research_direction": "A possible direction for future research."
}}

Rules:
- Do not invent evidence.
- Do not claim that a gap is completely unexplored unless the supplied literature supports that conclusion.
- Use cautious academic language such as "limited attention", "insufficient evidence", or "requires further investigation" where appropriate.
"""

    response = gap_llm.invoke(prompt)

    if isinstance(response.content, list):
        text = ""

        for item in response.content:
            if isinstance(item, dict) and item.get("type") == "text":
                text += item.get("text", "")
            elif isinstance(item, str):
                text += item

    else:
        text = str(response.content)

    text = text.strip()

    if text.startswith("```"):
        text = text.replace("```json", "").replace("```", "").strip()

    return json.loads(text)


def generate_literature_survey(topic, analyzed_papers, comparison):

    papers_summary = ""

    for i, paper in enumerate(analyzed_papers, 1):

        analysis = paper["analysis"]

        papers_summary += f"""
Paper {i}: {paper["title"]} ({paper["year"]})

Research Problem:
{analysis["research_problem"]}

Methodology:
{analysis["methodology"]}

Key Findings:
{analysis["key_findings"]}

Limitations:
{analysis["limitations"]}

Theme:
{analysis["research_theme"]}

"""

    prompt = f"""
You are an academic literature survey writing agent.

Research Topic:
{topic}

Analyzed Literature:
{papers_summary}

Literature Comparison:
{json.dumps(comparison, indent=2)}

Write a structured academic literature survey.

Use the following structure:

## 2. Literature Survey

### 2.1 Major Research Themes

Discuss the major themes found across the literature.

### 2.2 Existing Approaches and Methodologies

Compare the approaches used by researchers.

### 2.3 Major Findings

Synthesize the important findings across studies.

### 2.4 Challenges and Limitations

Discuss recurring limitations and implementation challenges.

### 2.5 Comparative Analysis

Explain similarities and differences between the studies.

### 2.6 Research Gaps

Clearly identify gaps supported by the analyzed literature.

### 2.7 Future Research Directions

Discuss future research directions emerging from the literature.

Rules:
- Write in formal academic language.
- Do not invent studies, results, statistics, or citations.
- Base the discussion only on the supplied literature information.
- Refer to studies as "the analyzed studies" when specific citation details are unavailable.
- Do not include a reference list yet.
"""

    response = survey_llm.invoke(prompt)

    if isinstance(response.content, list):
        text = ""

        for item in response.content:
            if isinstance(item, dict) and item.get("type") == "text":
                text += item.get("text", "")
            elif isinstance(item, str):
                text += item

    else:
        text = str(response.content)

    return text.strip()


def generate_academic_report(
    topic,
    research_plan,
    literature_survey,
    comparison,
    research_gap,
    analyzed_papers,
    target_pages=10
):

    # Approximate academic pages assuming ~450 words/page.
    target_words = int(target_pages * 450)

    references = ""

    for i, paper in enumerate(analyzed_papers, 1):
        references += (
            f"[{i}] {paper.get('title', 'Unknown Title')}. "
            f"Publication Year: {paper.get('year', 'N/A')}. "
            f"DOI: {paper.get('doi', 'N/A')}. "
            f"Citations: {paper.get('citations', 0)}.\\n"
        )

    prompt = f"""
You are an expert academic research paper generation agent.

Research Topic:
{topic}

TARGET REPORT LENGTH:
Approximately {target_pages} pages.

TARGET WORD COUNT:
Approximately {target_words} words.

IMPORTANT:
Generate a substantial academic report close to the requested
word count. Do NOT produce a short summary.

Research Objective:
{research_plan["research_objective"]}

Research Questions:
{json.dumps(research_plan["research_questions"], indent=2)}

Literature Survey:
{literature_survey}

Literature Comparison:
{json.dumps(comparison, indent=2)}

Research Gap:
{json.dumps(research_gap, indent=2)}

Available References:
{references}

Generate a complete academic-style research paper.

Use exactly this structure:

# {topic}

## Abstract

Write approximately 250-350 words covering:
- background
- objective
- literature-based approach
- major findings
- research gap
- future direction

## Keywords

Provide 5-7 relevant keywords.

## 1. Introduction

Provide a detailed academic introduction covering:
- background
- importance of the topic
- motivation
- research objective
- research questions
- scope
- significance

## 2. Research Methodology

Explain the AI-assisted literature survey methodology:
- research planning
- literature/source discovery
- source selection
- paper analysis
- thematic synthesis
- comparative analysis
- research-gap identification

Clearly state that this is a literature-based study and do not claim
that peer review was programmatically verified.

## 3. Literature Survey

Use the generated literature survey and expand it substantially.

Include:

### 3.1 Major Research Themes

### 3.2 Existing Approaches and Methodologies

### 3.3 Major Findings

### 3.4 Challenges and Limitations

### 3.5 Comparative Analysis of Existing Studies

### 3.6 Research Gaps

### 3.7 Future Research Directions

Discuss the literature in depth rather than merely listing papers.

## 4. Comparative Analysis

Provide a detailed synthesis comparing:
- methodologies
- approaches
- findings
- strengths
- limitations
- research themes

Use tables where useful.

## 5. Research Gaps

Discuss the major research gap and supporting gaps in detail.

Explain:
- what is missing
- why it matters
- what existing studies do not adequately address
- potential research opportunities

## 6. Future Research Directions

Provide detailed and realistic future research directions supported
by the analyzed literature.

Clearly distinguish proposed future work from established findings.

## 7. Conclusion

Provide a detailed academic conclusion summarizing the literature,
major findings, gaps, significance, and future opportunities.

## References

List all supplied references.

IMPORTANT RULES:

- Target approximately {target_words} words.
- Maintain formal academic language.
- Do not invent statistics, experiments, authors, journals, or results.
- Do not create fake citations.
- Use only information supplied above.
- Clearly distinguish literature findings from future suggestions.
- If information is unavailable from the analyzed literature, explicitly
  state that it is unavailable.
- Do not intentionally make the report shorter than necessary.
- Develop each section proportionally to achieve the requested length.
"""

    response = report_llm.invoke(prompt)

    if isinstance(response.content, list):
        result_text = ""

        for item in response.content:
            if isinstance(item, dict) and item.get("type") == "text":
                result_text += item.get("text", "")
            elif isinstance(item, str):
                result_text += item

    else:
        result_text = str(response.content)

    return result_text.strip()

def run_full_research_agent(topic, max_papers=15, target_pages=10):
    """
    Complete autonomous academic research agent.

    Input:
        topic - any research topic

    Output:
        Complete research package containing:
        - research plan
        - academic papers
        - paper analyses
        - literature comparison
        - research gaps
        - literature survey
        - academic report
    """

    if not isinstance(topic, str) or not topic.strip():
        raise ValueError("Please enter a valid research topic.")

    topic = topic.strip()

    print("=" * 80)
    print("              AUTONOMOUS ACADEMIC RESEARCH AGENT")
    print("=" * 80)

    # ---------------------------------------------------------
    # 1. RESEARCH PLANNING
    # ---------------------------------------------------------
    print("\n[1/7] Creating research plan...")

    research_plan = create_research_plan(topic)

    print("✓ Research plan created")
    print(f"  Research questions: "
          f"{len(research_plan.get('research_questions', []))}")
    print(f"  Literature themes: "
          f"{len(research_plan.get('literature_themes', []))}")

    # ---------------------------------------------------------
    # 2. TARGETED ACADEMIC SEARCH
    # ---------------------------------------------------------
    print("\n[2/7] Searching academic literature...")

    targeted_papers = search_openalex_targeted(
        topic,
        research_plan,
        papers_per_query=3
    )

    print(f"✓ Collected {len(targeted_papers)} unique papers")

    if not targeted_papers:
        raise ValueError(
            "No academic papers were found for this topic."
        )

    # ---------------------------------------------------------
    # 3. PAPER SELECTION + ANALYSIS
    # ---------------------------------------------------------
    print("\n[3/7] Selecting and analyzing academic papers...")

    selected_papers = select_best_papers(
        targeted_papers,
        max_papers=max_papers
    )

    analyzed_papers = analyze_papers(
        selected_papers,
        topic
    )

    print(f"✓ Analyzed {len(analyzed_papers)} papers")

    if not analyzed_papers:
        raise ValueError(
            "No papers with usable abstracts could be analyzed."
        )

    # ---------------------------------------------------------
    # 4. LITERATURE COMPARISON
    # ---------------------------------------------------------
    print("\n[4/7] Comparing literature...")

    comparison = compare_literature(
        analyzed_papers,
        topic
    )

    print("✓ Literature comparison completed")

    # ---------------------------------------------------------
    # 5. RESEARCH GAP
    # ---------------------------------------------------------
    print("\n[5/7] Identifying research gaps...")

    research_gap = generate_research_gap(
        topic,
        comparison
    )

    print("✓ Research gaps identified")

    # ---------------------------------------------------------
    # 6. LITERATURE SURVEY
    # ---------------------------------------------------------
    print("\n[6/7] Writing literature survey...")

    literature_survey = generate_literature_survey(
        topic,
        analyzed_papers,
        comparison
    )

    print("✓ Literature survey generated")

    # ---------------------------------------------------------
    # 7. FINAL ACADEMIC REPORT
    # ---------------------------------------------------------
    print("\n[7/7] Generating academic report...")

    academic_report = generate_academic_report(
        topic,
        research_plan,
        literature_survey,
        comparison,
        research_gap,
        analyzed_papers,
        target_pages=target_pages
    )

    print("✓ Academic report generated")

    # ---------------------------------------------------------
    # FINAL RESULT
    # ---------------------------------------------------------
    print("\n" + "=" * 80)
    print("                 RESEARCH COMPLETED")
    print("=" * 80)

    print(f"\nTopic: {topic}")
    print(f"Academic papers collected: {len(targeted_papers)}")
    print(f"Papers analyzed: {len(analyzed_papers)}")

    print("\nAgent successfully completed all stages.")

    return {
        "topic": topic,
        "research_plan": research_plan,
        "papers": targeted_papers,
        "selected_papers": selected_papers,
        "analyzed_papers": analyzed_papers,
        "comparison": comparison,
        "research_gap": research_gap,
        "literature_survey": literature_survey,
        "academic_report": academic_report
    }





def search_openalex_targeted(topic, research_plan, papers_per_query=3):
    """
    Fast academic search.
    Uses Tavily first to avoid Semantic Scholar/OpenAlex rate limits.
    Falls back to one OpenAlex request if Tavily is unavailable.
    """

    import os
    import requests
    import re

    print(f"🔎 Fast academic search: {topic}")

    papers = []
    seen = set()

    tavily_key = os.getenv("TAVILY_API_KEY")

    # ---------------------------------------------------------
    # 1. FAST TAVILY SEARCH
    # ---------------------------------------------------------
    if tavily_key:
        try:
            response = requests.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": tavily_key,
                    "query": topic + " research literature review",
                    "search_depth": "basic",
                    "max_results": 12,
                    "include_answer": False
                },
                timeout=20
            )

            if response.status_code == 200:
                results = response.json().get("results", [])

                for item in results:
                    title = item.get("title", "").strip()
                    content = item.get("content", "").strip()
                    url = item.get("url", "").strip()

                    if not title or not content:
                        continue

                    key = url or title.lower()

                    if key in seen:
                        continue

                    seen.add(key)

                    papers.append({
                        "id": key,
                        "title": title,
                        "abstract": content,
                        "year": None,
                        "citation_count": 0,
                        "doi": None,
                        "url": url,
                        "authors": [],
                        "venue": "",
                        "source": "Tavily academic/web search"
                    })

                if papers:
                    print(f"✅ Fast search found {len(papers)} sources")
                    return papers

        except Exception as e:
            print("⚠️ Tavily search failed:", str(e))

    # ---------------------------------------------------------
    # 2. ONE OPENALEX FALLBACK REQUEST
    # ---------------------------------------------------------
    try:
        params = {
            "search": topic,
            "filter": "has_abstract:true",
            "per-page": 12,
            "mailto": os.getenv("RESEARCH_EMAIL", "")
        }

        response = requests.get(
            "https://api.openalex.org/works",
            params=params,
            timeout=15
        )

        if response.status_code == 200:
            data = response.json()

            for item in data.get("results", []):
                abstract = ""

                inverted = item.get("abstract_inverted_index") or {}

                if inverted:
                    words = []
                    for word, positions in inverted.items():
                        for pos in positions:
                            words.append((pos, word))

                    abstract = " ".join(
                        word for _, word in sorted(words)
                    )

                if not abstract:
                    continue

                papers.append({
                    "id": item.get("id"),
                    "title": item.get("title", ""),
                    "abstract": abstract,
                    "year": item.get("publication_year"),
                    "citation_count": item.get("cited_by_count", 0),
                    "doi": item.get("doi"),
                    "url": item.get("primary_location", {}).get("landing_page_url"),
                    "authors": [
                        a.get("author", {}).get("display_name", "")
                        for a in item.get("authorships", [])
                    ],
                    "venue": (
                        item.get("primary_location", {})
                        .get("source", {}) or {}
                    ).get("display_name", ""),
                    "source": "OpenAlex"
                })

            if papers:
                print(f"✅ OpenAlex fallback found {len(papers)} papers")
                return papers

        print(f"⚠️ OpenAlex returned HTTP {response.status_code}")

    except Exception as e:
        print("⚠️ OpenAlex fallback failed:", str(e))

    print("❌ No academic sources found.")
    return []

