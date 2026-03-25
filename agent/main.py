"""
CodeGuard AI Agent (FINAL VERSION WITH UI + WEBHOOK)
Author: Rahul Giri
"""

# ── ENV ───────────────────────────────────────────
import os
from dotenv import load_dotenv
load_dotenv()

# ── IMPORTS ───────────────────────────────────────
import json
import logging
import re
import gitlab
import threading
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from openai import OpenAI

# ── SETUP ─────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
gl = gitlab.Gitlab(os.environ["GITLAB_URL"], private_token=os.environ["GITLAB_TOKEN"])

MODEL = "gpt-4o-mini"

# ── UTILITY ───────────────────────────────────────
def extract_json(text):
    try:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        return json.loads(match.group()) if match else {}
    except:
        return {}

# ── DATA MODEL ────────────────────────────────────
class MREvent(BaseModel):
    project_id: int
    mr_iid: int
    diff: str
    source_branch: str
    target_branch: str
    author: str
    title: str

# ── PROMPTS ───────────────────────────────────────
SECURITY_PROMPT = """
Analyze this code for security issues.

Code:
{diff}

Return JSON:
{{
  "risk_level": "LOW",
  "summary": ""
}}
"""

CODE_REVIEW_PROMPT = """
Review this code.

Code:
{diff}

Return JSON:
{{
  "score": 5,
  "summary": ""
}}
"""

TEST_PROMPT = """
Generate tests.

Code:
{diff}

Return JSON:
{{
  "test_code": "",
  "summary": ""
}}
"""

REPORT_PROMPT = """
Create a GitLab MR comment.

Security: {security}
Review: {review}
Tests: {tests}
"""

# ── AI FUNCTIONS ─────────────────────────────────
def ask_ai(prompt):
    res = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}]
    )
    return res.choices[0].message.content

def run_security_scan(diff):
    logger.info("Security scan")
    return extract_json(ask_ai(SECURITY_PROMPT.format(diff=diff)))

def run_code_review(diff):
    logger.info("Code review")
    return extract_json(ask_ai(CODE_REVIEW_PROMPT.format(diff=diff)))

def run_tests(diff):
    logger.info("Test generation")
    return extract_json(ask_ai(TEST_PROMPT.format(diff=diff)))

def compile_report(security, review, tests):
    return ask_ai(
        REPORT_PROMPT.format(
            security=json.dumps(security),
            review=json.dumps(review),
            tests=json.dumps(tests)
        )
    )

# ── BACKGROUND PROCESS ────────────────────────────
def process_ai(event):
    try:
        security = run_security_scan(event.diff)
        review = run_code_review(event.diff)
        tests = run_tests(event.diff)

        report = compile_report(security, review, tests)

        post_comment(event.project_id, event.mr_iid, report)
        logger.info("✅ Comment posted successfully")

    except Exception as e:
        logger.error(f"❌ Background error: {e}")

# ── GITLAB ───────────────────────────────────────
def post_comment(project_id, mr_iid, text):
    project = gl.projects.get(project_id)
    mr = project.mergerequests.get(mr_iid)
    mr.notes.create({"body": text})

# ── WEBHOOK ──────────────────────────────────────
@app.post("/webhook/mr")
async def webhook(request: Request):
    try:
        data = await request.json()

        event = MREvent(
            project_id=data["project"]["id"],
            mr_iid=data["object_attributes"]["iid"],
            diff=data.get("diff", "No diff"),
            source_branch=data["object_attributes"]["source_branch"],
            target_branch=data["object_attributes"]["target_branch"],
            author=data["user"]["name"],
            title=data["object_attributes"]["title"]
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    threading.Thread(target=process_ai, args=(event,)).start()

    return {"status": "processing"}

# ── UI PAGE ──────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <html>
    <head>
        <title>CodeGuard AI</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background: #f5f7fb;
                padding: 30px;
                color: #333;
            }

            h1 {
                text-align: center;
                color: #2563eb;
            }

            textarea {
                width: 100%;
                height: 200px;
                padding: 10px;
                border-radius: 8px;
                border: 1px solid #ccc;
            }

            button {
                margin-top: 10px;
                padding: 12px 20px;
                background: #2563eb;
                color: white;
                border: none;
                border-radius: 8px;
                cursor: pointer;
            }

            .box {
                background: white;
                padding: 20px;
                margin-top: 20px;
                border-radius: 10px;
            }

            pre {
                background: #f1f5f9;
                padding: 10px;
                border-radius: 6px;
            }
        </style>
    </head>
    <body>
        <h1>🛡️ CodeGuard AI Dashboard</h1>

        <textarea id="code" placeholder="Paste code here..."></textarea><br>
        <button onclick="analyze()">Analyze</button>

        <div class="box">
            <h2>🔍 Security</h2>
            <pre id="security"></pre>
        </div>

        <div class="box">
            <h2>🧠 Review</h2>
            <pre id="review"></pre>
        </div>

        <div class="box">
            <h2>🧪 Tests</h2>
            <pre id="tests"></pre>
        </div>

        <script>
        async function analyze() {
            const code = document.getElementById("code").value;

            const res = await fetch("/analyze", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({ diff: code })
            });

            const data = await res.json();

            document.getElementById("security").innerText =
                JSON.stringify(data.security, null, 2);

            document.getElementById("review").innerText =
                JSON.stringify(data.review, null, 2);

            document.getElementById("tests").innerText =
                JSON.stringify(data.tests, null, 2);
        }
        </script>
    </body>
    </html>
    """

# ── ANALYZE API (UI) ─────────────────────────────
@app.post("/analyze")
async def analyze(data: dict):
    diff = data.get("diff", "")

    security = run_security_scan(diff)
    review = run_code_review(diff)
    tests = run_tests(diff)

    return {
        "security": security,
        "review": review,
        "tests": tests
    }

# ── HEALTH ───────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "running"}

# ── MAIN ─────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("agent.main:app", host="0.0.0.0", port=port)