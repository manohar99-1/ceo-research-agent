"""
CEO/Founder Research Agent
Autonomous agent that researches founders & CEOs using web browsing + Groq LLM
"""

import os
import sys
import json
import argparse
from dotenv import load_dotenv
from agent.researcher import ResearchAgent

load_dotenv()

def main():
    parser = argparse.ArgumentParser(description="Autonomous CEO/Founder Research Agent")
    parser.add_argument("name", help="Name of the CEO or founder to research")
    parser.add_argument("--company", help="Company name (optional, improves accuracy)", default="")
    parser.add_argument("--output", help="Output file path", default="")
    args = parser.parse_args()

    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        print("❌ ERROR: GROQ_API_KEY not found in environment. Please set it in your .env file.")
        sys.exit(1)

    print(f"\n🤖 CEO Research Agent Starting...")
    print(f"🔍 Target: {args.name}" + (f" ({args.company})" if args.company else ""))
    print("=" * 60)

    agent = ResearchAgent(groq_api_key=groq_api_key)
    report = agent.research(name=args.name, company=args.company)

    # Save output
    output_path = args.output or f"results/{args.name.replace(' ', '_')}_report.json"
    os.makedirs("results", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Research complete! Report saved to: {output_path}")
    print("\n📋 SUMMARY:")
    print(f"  Name        : {report.get('name', 'N/A')}")
    print(f"  Company     : {report.get('current_company', 'N/A')}")
    print(f"  Role        : {report.get('current_role', 'N/A')}")
    print(f"  Sources     : {len(report.get('sources', []))} URLs scraped")
    print(f"  Memory Steps: {report.get('memory_steps', 0)}")

if __name__ == "__main__":
    main()
