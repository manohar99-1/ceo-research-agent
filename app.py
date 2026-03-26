"""
app.py - Flask web server for CEO Research Agent
Serves the frontend and exposes /api/research endpoint
"""

import os
import json
import threading
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
from agent.researcher import ResearchAgent

load_dotenv()

app = Flask(__name__, static_folder="static")
CORS(app)

# In-memory job store { job_id: { status, result, error } }
jobs = {}
jobs_lock = threading.Lock()


def run_research(job_id: str, name: str, company: str):
    groq_api_key = os.getenv("GROQ_API_KEY", "")
    try:
        agent = ResearchAgent(groq_api_key=groq_api_key)
        report = agent.research(name=name, company=company)

        # Save to results/
        os.makedirs("results", exist_ok=True)
        filename = f"results/{name.replace(' ', '_')}_report.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        with jobs_lock:
            jobs[job_id] = {"status": "done", "result": report, "error": None}

    except Exception as e:
        with jobs_lock:
            jobs[job_id] = {"status": "error", "result": None, "error": str(e)}


@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/api/research", methods=["POST"])
def start_research():
    data = request.get_json(force=True)
    name = (data.get("name") or "").strip()
    company = (data.get("company") or "").strip()

    if not name:
        return jsonify({"error": "Name is required"}), 400

    if not os.getenv("GROQ_API_KEY"):
        return jsonify({"error": "GROQ_API_KEY not configured on server"}), 500

    import uuid
    job_id = str(uuid.uuid4())[:8]
    with jobs_lock:
        jobs[job_id] = {"status": "running", "result": None, "error": None}

    thread = threading.Thread(target=run_research, args=(job_id, name, company))
    thread.daemon = True
    thread.start()

    return jsonify({"job_id": job_id}), 202


@app.route("/api/status/<job_id>")
def job_status(job_id):
    with jobs_lock:
        job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    return jsonify(job)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
