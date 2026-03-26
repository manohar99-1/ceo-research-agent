"""
researcher.py - Core autonomous research agent
Uses web browsing when available, falls back to LLM knowledge
"""

import json
import re
from groq import Groq
from agent.memory import AgentMemory

MODEL = "llama-3.3-70b-versatile"
MAX_TOKENS = 2000


class ResearchAgent:
    def __init__(self, groq_api_key: str):
        self.client = Groq(api_key=groq_api_key)

    def research(self, name: str, company: str = "") -> dict:
        memory = AgentMemory(subject_name=name)
        context = f"{name}" + (f", {company}" if company else "")
        print(f"\n🧠 Researching: {context}")
        web_data = self._try_web_research(context, memory)
        report = self._synthesize(context, memory, web_data)
        return report

    def _try_web_research(self, context: str, memory: AgentMemory) -> str:
        try:
            from agent.browser import WebBrowser
            memory.log_step("Attempting web search", context)
            browser = WebBrowser(delay=1.0)
            name = context.split(",")[0].strip()
            queries = [
                f"{name} CEO founder biography",
                f"{name} company career achievements",
                f"{name} latest news 2024 2025",
            ]
            snippets = []
            for query in queries:
                try:
                    results = browser.search(query, num_results=3)
                    for r in results[:2]:
                        if r.get("snippet"):
                            snippets.append(r["snippet"])
                            memory.add_source(r.get("url", ""))
                    memory.add_query(query)
                except Exception:
                    continue
            if snippets:
                memory.log_step("Web data gathered", f"{len(snippets)} snippets")
                return "\n".join(snippets)
        except Exception as e:
            memory.log_step("Web search unavailable", str(e))
        return ""

    def _synthesize(self, context: str, memory: AgentMemory, web_data: str) -> dict:
        memory.log_step("Synthesizing report with LLM")
        if web_data:
            data_section = f"WEB DATA GATHERED:\n{web_data[:3000]}"
        else:
            data_section = "No web data available. Use your training knowledge."

        prompt = f"""You are an expert researcher. Generate a comprehensive research report about: {context}

{data_section}

Return ONLY a valid JSON object with these exact fields:

{{
  "name": "full name",
  "current_role": "current job title",
  "current_company": "current company",
  "nationality": "country",
  "education": ["degree at institution"],
  "career_timeline": ["year: role at company"],
  "companies_founded": ["company (year)"],
  "key_achievements": ["achievement 1", "achievement 2", "achievement 3", "achievement 4", "achievement 5"],
  "net_worth_or_funding": "amount",
  "recent_news": ["news 1", "news 2", "news 3"],
  "notable_quotes": ["quote 1"],
  "social_links": {{"linkedin": "", "twitter": ""}},
  "summary": "3-4 sentence professional biography",
  "agent_notes": "data source used"
}}

Use your knowledge to fill ALL fields accurately. Do not leave fields empty."""

        response = self._llm(prompt, max_tokens=2000)
        try:
            clean = re.sub(r"```(?:json)?|```", "", response).strip()
            start = clean.find("{")
            end = clean.rfind("}") + 1
            if start >= 0 and end > start:
                clean = clean[start:end]
            report = json.loads(clean)
        except Exception as e:
            memory.log_step("JSON parse error", str(e))
            report = {
                "name": context.split(",")[0].strip(),
                "summary": response[:500] if response else "Research completed.",
                "agent_notes": "JSON parsing failed"
            }

        report["sources"] = memory.sources
        report["search_queries_used"] = memory.search_queries
        report["memory_steps"] = len(memory.steps)
        report["steps_log"] = memory.steps
        memory.log_step("Report complete")
        return report

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
            print(f"LLM error: {e}")
            return "{}"
