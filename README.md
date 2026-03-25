# 🤖 CEO / Founder Research Agent

An **autonomous AI agent** that researches any CEO or founder by browsing the web, following links, maintaining memory across steps, and producing a structured JSON report — all without human intervention.

Built for the **LegalSeva.org AI Agent Developer internship** assignment.

---

## 🧠 How It Works

The agent runs a **5-phase autonomous pipeline**:

```
Phase 1 → Plan search queries (LLM generates diverse queries)
Phase 2 → Browse the web    (DuckDuckGo search + page scraping)
Phase 3 → Extract facts     (LLM parses raw content into structured data)
Phase 4 → Gap-fill search   (Agent detects missing info, searches again)
Phase 5 → Synthesize report (LLM produces final structured JSON output)
```

### Key Agent Capabilities

| Feature | Description |
|---|---|
| 🔍 Autonomous Search | Plans and executes multiple targeted searches |
| 🌐 Link Following | Fetches and reads full page content from results |
| 🧠 Persistent Memory | `AgentMemory` accumulates facts & context across all steps |
| 🔄 Self-Correction | Detects gaps in gathered data and runs follow-up searches |
| 📊 Structured Output | Clean JSON report with sources, timeline, achievements |

---

## 🛠️ Tech Stack

- **Python 3.10+**
- **Groq API** (LLaMA 3 70B) — fast, free LLM for reasoning
- **BeautifulSoup4** — web page parsing
- **Requests** — HTTP browsing
- **DuckDuckGo HTML** — search engine (no API key needed)

---

## 🚀 Setup & Run

### 1. Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/ceo-research-agent.git
cd ceo-research-agent
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure API key
```bash
cp .env.example .env
# Edit .env and add your Groq API key
# Get one free at: https://console.groq.com
```

### 4. Run the agent
```bash
# Research a CEO by name
python main.py "Sam Altman"

# With company context for better accuracy
python main.py "Sundar Pichai" --company "Google"

# Custom output path
python main.py "Elon Musk" --output results/elon_report.json
```

---

## 📋 Sample Output

```json
{
  "name": "Sam Altman",
  "current_role": "CEO",
  "current_company": "OpenAI",
  "nationality": "American",
  "education": ["Computer Science - Stanford University (dropped out)"],
  "career_timeline": [
    "2005: Co-founded Loopt",
    "2014: President at Y Combinator",
    "2019: CEO at OpenAI"
  ],
  "companies_founded": ["Loopt (2005)", "OpenAI (2015)"],
  "key_achievements": [
    "Led OpenAI to $157B valuation",
    "Launched ChatGPT — fastest growing app in history",
    "Raised $6.6B funding round in 2024"
  ],
  "recent_news": ["..."],
  "sources": ["https://...", "..."],
  "memory_steps": 12,
  "search_queries_used": [...]
}
```

---

## 📁 Project Structure

```
ceo-research-agent/
├── agent/
│   ├── browser.py      # Web search & page scraping
│   ├── memory.py       # Persistent memory across steps
│   ├── researcher.py   # Core agent orchestration
│   └── output.py       # Report generation
├── results/            # Generated reports (gitignored)
├── main.py             # CLI entry point
├── requirements.txt
└── .env.example
```

---

## 🔮 Architecture Diagram

```
User Input (CEO Name)
        │
        ▼
┌─────────────────────┐
│   ResearchAgent     │◄──── Groq LLM (LLaMA 3 70B)
│   (researcher.py)   │
└────────┬────────────┘
         │  orchestrates
    ┌────┴────┐
    ▼         ▼
WebBrowser  AgentMemory
(browser.py) (memory.py)
    │         │
    │  feeds  │
    └────┬────┘
         ▼
   Structured JSON Report
```

---

## 📄 License

MIT License — open source, free to use.

---

*Built by Manohar Poleboina | LegalSeva.org AI Agent Developer Assignment*
