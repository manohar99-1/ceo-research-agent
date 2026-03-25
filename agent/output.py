"""
output.py - Report generation and formatting
Produces clean structured JSON and human-readable Markdown reports
"""

import json
from datetime import datetime


def build_report(facts: dict, memory_meta: dict) -> dict:
    """Merge facts with metadata into final report structure."""
    return {
        **facts,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        **memory_meta,
    }


def to_markdown(report: dict) -> str:
    """Convert structured report to readable Markdown."""
    lines = [
        f"# Research Report: {report.get('name', 'Unknown')}",
        f"*Generated: {report.get('generated_at', '')}*",
        "",
        "## 📌 Overview",
        f"- **Role**: {report.get('current_role', 'N/A')}",
        f"- **Company**: {report.get('current_company', 'N/A')}",
        f"- **Nationality**: {report.get('nationality', 'N/A')}",
        f"- **Net Worth / Funding**: {report.get('net_worth_or_funding', 'N/A')}",
        "",
        "## 📝 Professional Summary",
        report.get("summary", "N/A"),
        "",
    ]

    def _list_section(title: str, key: str):
        items = report.get(key, [])
        if items:
            lines.append(f"## {title}")
            for item in items:
                lines.append(f"- {item}")
            lines.append("")

    _list_section("🎓 Education", "education")
    _list_section("📅 Career Timeline", "career_timeline")
    _list_section("🚀 Companies Founded", "companies_founded")
    _list_section("🏆 Key Achievements", "key_achievements")
    _list_section("📰 Recent News", "recent_news")
    _list_section("💬 Notable Quotes", "notable_quotes")

    links = report.get("social_links", {})
    if any(links.values()):
        lines.append("## 🔗 Social Links")
        for platform, url in links.items():
            if url:
                lines.append(f"- **{platform.title()}**: {url}")
        lines.append("")

    _list_section("🔍 Sources", "sources")

    lines += [
        "## 🤖 Agent Metadata",
        f"- Memory steps: {report.get('memory_steps', 0)}",
        f"- Queries used: {len(report.get('search_queries_used', []))}",
        f"- Sources scraped: {len(report.get('sources', []))}",
        f"- Agent notes: {report.get('agent_notes', 'N/A')}",
    ]

    return "\n".join(lines)


def save_markdown(report: dict, path: str):
    """Save report as Markdown file."""
    md = to_markdown(report)
    with open(path, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"  📄 Markdown report saved: {path}")
