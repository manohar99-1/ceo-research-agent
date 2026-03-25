"""
researcher.py - Core autonomous research agent
Orchestrates browsing, memory, and LLM reasoning across multiple steps
"""

import json
import re
from groq import Groq
from agent.browser import WebBrowser
from agent.memory import AgentMemory
from agent.output import build_report


# ── Groq model config ────────────────────────────────────────────────────────
MODEL = "llama3-70b-8192"
MAX_TOKENS = 1024


class ResearchAgent:
    """
    Autonomous multi-step agent that researches a CEO/Founder.

    Pipeline:
      Step 1 → Plan search queries
      Step 2 → Execute searches & browse top pages
      Step 3 → Extract facts from raw content (via LLM)
      Step 4 → Follow-up searches for gaps
      Step 5 → Final synthesis → structured JSON report
    """

    def __init__(self, groq_api_key: str):
        self.client = Groq(api_key=groq_api_key)
        self.browser = WebBrowser(delay=1.2)

    # ── Public API ────────────────────────────────────────────────────────────

    def research(self, name: str, company: str = "") -> dict:
        memory = AgentMemory(subject_name=name)
        context = f"{name}" + (f", {company}" if company else "")

        print(f"\n🧠 PHASE 1: Planning research strategy")
        queries = self._plan_queries(context, memory)

        print(f"\n🌐 PHASE 2: Browsing the web ({len(queries)} queries)")
        self._browse_and_collect(queries, memory)

        print(f"\n🔬 PHASE 3: Extracting facts with LLM")
        self._extract_facts(context, memory)

        print(f"\n🔄 PHASE 4: Gap-filling follow-up")
        self._followup_search(context, memory)

        print(f"\n📊 PHASE 5: Synthesizing final report")
        report = self._synthesize(context, memory)

        return report

    # ── Phase 1: Query Planning ───────────────────────────────────────────────

    def _plan_queries(self, context: str, memory: AgentMemory) -> list[str]:
        memory.log_step("Planning search queries", context)

        prompt = f"""You are a research agent planning web searches for: {context}

Generate exactly 6 diverse search queries to gather comprehensive information about this person.
Cover: biography, education, career history, companies founded/led, achievements, recent news.

Return ONLY a JSON array of 6 strings. No explanation.
Example: ["query 1", "query 2", ...]"""

        response = self._llm(prompt)
        try:
            queries = json.loads(response)
            if not isinstance(queries, list):
                raise ValueError
            queries = [str(q) for q in queries[:6]]
        except Exception:
            # Fallback queries
            name = context.split(",")[0].strip()
            queries = [
                f"{name} biography founder CEO",
                f"{name} career history education",
                f"{name} company founded achievements",
                f"{name} interview 2024 2025",
                f"{name} net worth funding",
                f"{name} latest news",
            ]

        for q in queries:
            memory.add_query(q)

        memory.log_step("Queries planned", f"{len(queries)} queries")
        print(f"  📋 Queries: {queries}")
        return queries

    # ── Phase 2: Browse & Collect ─────────────────────────────────────────────

    def _browse_and_collect(self, queries: list[str], memory: AgentMemory):
        search_results = self.browser.multi_search(queries)
        memory.log_step("Web search complete", f"{len(search_results)} results found")

        # Prioritize high-value domains
        priority_domains = ["linkedin.com", "wikipedia.org", "crunchbase.com",
                            "forbes.com", "techcrunch.com", "bloomberg.com"]
        def priority(r):
            for i, d in enumerate(priority_domains):
                if d in r.get("url", ""):
                    return i
            return len(priority_domains)

        sorted_results = sorted(search_results, key=priority)

        # Add snippets from search results immediately
        for r in sorted_results[:10]:
            if r.get("snippet"):
                memory.add_snippet(r["snippet"], r["url"])

        # Fetch top pages in full
        pages_fetched = 0
        for result in sorted_results[:8]:
            url = result.get("url", "")
            if not url or "youtube.com" in url or "twitter.com" in url:
                continue
            page = self.browser.fetch_page(url)
            if page["text"]:
                memory.add_snippet(page["text"], url)
                memory.add_source(url)
                pages_fetched += 1
            if pages_fetched >= 6:
                break

        memory.log_step("Pages fetched", f"{pages_fetched} pages scraped")

    # ── Phase 3: Extract Facts ────────────────────────────────────────────────

    def _extract_facts(self, context: str, memory: AgentMemory):
        memory.log_step("Extracting structured facts with LLM")

        raw_context = memory.get_context_summary(max_chars=5000)

        prompt = f"""You are extracting structured facts about: {context}

Based on the following research data, extract all available information.
Return ONLY valid JSON with these exact keys (use null if unknown):

{{
  "name": "full name",
  "current_role": "current job title",
  "current_company": "current company name",
  "nationality": "country",
  "education": ["degree - institution", ...],
  "career_timeline": ["year - role - company", ...],
  "companies_founded": ["company name (year)", ...],
  "key_achievements": ["achievement 1", ...],
  "net_worth_or_funding": "amount or description",
  "recent_news": ["news item 1", ...],
  "notable_quotes": ["quote 1", ...],
  "social_links": {{"linkedin": "url", "twitter": "url"}},
  "summary": "2-3 sentence professional bio"
}}

RESEARCH DATA:
{raw_context}"""

        response = self._llm(prompt, max_tokens=1500)

        try:
            # Strip markdown fences if present
            clean = re.sub(r"```(?:json)?|```", "", response).strip()
            facts = json.loads(clean)
            memory.update_facts(facts)
            memory.log_step("Facts extracted", f"{len(facts)} fields populated")
        except Exception as e:
            memory.log_step("Fact extraction partial", str(e))

    # ── Phase 4: Follow-up Search ─────────────────────────────────────────────

    def _followup_search(self, context: str, memory: AgentMemory):
        """Identify gaps and do targeted follow-up searches."""
        missing = [k for k, v in memory.facts.items()
                   if not v or v in ([], {}, "Unknown", "N/A", None)]

        if not missing:
            memory.log_step("No gaps found, skipping follow-up")
            return

        memory.log_step("Follow-up search", f"Filling gaps: {missing[:3]}")

        name = context.split(",")[0].strip()
        followup_queries = [f"{name} {gap.replace('_', ' ')}" for gap in missing[:3]]

        for query in followup_queries:
            memory.add_query(query)
            results = self.browser.search(query, num_results=3)
            for r in results[:2]:
                if r.get("snippet"):
                    memory.add_snippet(r["snippet"], r["url"])
                page = self.browser.fetch_page(r["url"])
                if page["text"]:
                    memory.add_snippet(page["text"], r["url"])
                    memory.add_source(r["url"])
                    break

        # Re-extract with enriched data
        self._extract_facts(context, memory)

    # ── Phase 5: Final Synthesis ──────────────────────────────────────────────

    def _synthesize(self, context: str, memory: AgentMemory) -> dict:
        memory.log_step("Final synthesis", "Generating structured report")

        prompt = f"""You are finalizing a research report about: {context}

Here is all gathered data:
{memory.get_context_summary(max_chars=5000)}

Write a comprehensive, factual, professional research report.
Return ONLY valid JSON with ALL these fields:

{{
  "name": "string",
  "current_role": "string",
  "current_company": "string",
  "nationality": "string",
  "education": ["list"],
  "career_timeline": ["year: role at company"],
  "companies_founded": ["list"],
  "key_achievements": ["list of 5+"],
  "net_worth_or_funding": "string",
  "recent_news": ["list of 3+"],
  "notable_quotes": ["list"],
  "social_links": {{"linkedin": "", "twitter": ""}},
  "summary": "3-4 sentence professional bio",
  "sources": ["url list"],
  "search_queries_used": ["list"],
  "memory_steps": 0,
  "agent_notes": "any caveats about data confidence"
}}"""

        response = self._llm(prompt, max_tokens=2000)

        try:
            clean = re.sub(r"```(?:json)?|```", "", response).strip()
            report = json.loads(clean)
        except Exception:
            # Return memory facts as fallback
            report = memory.facts.copy()

        # Always inject memory metadata
        report["sources"] = memory.sources
        report["search_queries_used"] = memory.search_queries
        report["memory_steps"] = len(memory.steps)
        report["steps_log"] = memory.steps

        memory.log_step("Report complete", "✅ Done")
        return report

    # ── LLM Helper ────────────────────────────────────────────────────────────

    def _llm(self, prompt: str, max_tokens: int = MAX_TOKENS) -> str:
        try:
            response = self.client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.3,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"    ⚠️  LLM error: {e}")
            return "{}"
