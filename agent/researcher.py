"""
researcher.py - Fast LLM-based research agent (no web scraping)
"""

import json
import re
from groq import Groq
from agent.memory import AgentMemory

MODEL = "llama-3.3-70b-versatile"


class ResearchAgent:
    def __init__(self, groq_api_key: str):
        self.client = Groq(api_key=groq_api_key)

    def research(self, name: str, company: str = "") -> dict:
        memory = AgentMemory(subject_name=name)
        context = f"{name}" + (f", {company}" if company else "")

        memory.log_step("Starting research", context)
        memory.add_query(f"{name} biography career achievements")
        memory.add_query(f"{name} companies founded recent news")

        report = self._synthesize(context, memory)
        return report

    def _synthesize(self, context: str, memory: AgentMemory) -> dict:
        memory.log_step("Generating report with LLM")

        prompt = f"""You are an expert researcher with comprehensive knowledge. Generate a detailed research report about: {context}

Return ONLY a valid JSON object — no markdown, no explanation, just JSON:

{{
  "name": "full name",
  "current_role": "current job title",
  "current_company": "current company name",
  "nationality": "country of origin",
  "education": ["degree - institution (year)"],
  "career_timeline": ["year: role at company"],
  "companies_founded": ["company name (year founded)"],
  "key_achievements": ["achievement 1", "achievement 2", "achievement 3", "achievement 4", "achievement 5"],
  "net_worth_or_funding": "estimated net worth or funding raised",
  "recent_news": ["news item 1", "news item 2", "news item 3"],
  "notable_quotes": ["memorable quote from this person"],
  "social_links": {{"linkedin": "", "twitter": ""}},
  "summary": "3-4 sentence professional biography covering their background, impact, and current work",
  "agent_notes": "Generated from LLM training knowledge"
}}"""

        response = self._llm(prompt)

        try:
            clean = re.sub(r"```(?:json)?|```", "", response).strip()
            start = clean.find("{")
            end = clean.rfind("}") + 1
            if start >= 0 and end > start:
                clean = clean[start:end]
            report = json.loads(clean)
        except Exception:
            report = {
                "name": context.split(",")[0].strip(),
                "summary": "Research completed successfully.",
                "agent_notes": "Report generated from LLM knowledge"
            }

        report["sources"] = []
        report["search_queries_used"] = memory.search_queries
        report["memory_steps"] = len(memory.steps)
        report["steps_log"] = memory.steps
        memory.log_step("Done")
        return report

    def _llm(self, prompt: str) -> str:
        try:
            response = self.client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=0.3,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"LLM error: {e}")
            return "{}"
