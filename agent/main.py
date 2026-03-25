"""
CodeGuard AI Agent (Gemini Version)
===================================
Main entry point for the CodeGuard AI agent.
Now powered by Google Gemini (FREE)

Author: Rahul Giri
License: MIT
"""

# ── ENV LOAD ────────────────────────────────────────────────────────────────
import os
from dotenv import load_dotenv
load_dotenv()

# ── IMPORTS ─────────────────────────────────────────────────────────────────
import json
import logging
import re
import gitlab
import google.generativeai as genai
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel

# ── LOGGING ─────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── FASTAPI APP ─────────────────────────────────────────────────────────────
app = FastAPI(
    title="CodeGuard AI Agent",
    description="AI-powered security scan, code review & test generation for GitLab MRs",
    version="1.0.0"
)

# ── GEMINI SETUP ────────────────────────────────────────────────────────────
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
MODEL = genai.GenerativeModel("gemini-1.5-flash")

# ── GITLAB CLIENT ───────────────────────────────────────────────────────────
gl = gitlab.Gitlab(os.environ["GITLAB_URL"], private_token=os.environ["GITLAB_TOKEN"])

# ── UTILITY ─────────────────────────────────────────────────────────────────
def extract_json(text: str) -> dict:
    """Extract JSON safely from Gemini response."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    return json.loads(match.group()) if match else {}

# ── Pydantic Model ──────────────────────────────────────────────────────────
class MREvent(BaseModel):
    project_id: int
    mr_iid: int
    diff: str
    source_branch: str
    target_branch: str
    author: str
    title: str

# ── PROMPTS ─────────────────────────────────────────────────────────────────
SECURITY_PROMPT = """
You are a senior application security engineer. Analyze the following code diff for:
- OWASP Top 10 vulnerabilities
- Hardcoded secrets
- SQL injection risks

Code Diff:
{diff}

Respond ONLY in JSON:
{
  "risk_level": "CRITICAL|HIGH|MEDIUM|LOW|NONE",
  "vulnerabilities": [
    {"type": "...", "line": "...", "description": "...", "fix": "..."}
  ],
  "summary": "..."
}
"""

CODE_REVIEW_PROMPT = """
You are a senior software engineer. Review this diff for:
- Code quality
- Best practices
- Performance

Code Diff:
{diff}

Respond ONLY in JSON:
{
  "score": 1,
  "issues": [],
  "positives": [],
  "summary": "..."
}
"""

TEST_GENERATION_PROMPT = """
Generate unit tests for this code diff.

Code Diff:
{diff}

Respond ONLY in JSON:
{
  "test_framework": "pytest",
  "filename": "test_file.py",
  "test_code": "...",
  "coverage_estimate": "...",
  "summary": "..."
}
"""

REPORT_PROMPT = """
Create a GitLab MR review comment.

Security: {security}
Review: {review}
Tests: {tests}

Format nicely in markdown with emojis.
"""

# ── CORE FUNCTIONS ──────────────────────────────────────────────────────────
def run_security_scan(diff: str) -> dict:
    logger.info("Running security scan...")
    response = MODEL.generate_content(SECURITY_PROMPT.format(diff=diff))
    return extract_json(response.text)


def run_code_review(diff: str) -> dict:
    logger.info("Running code review...")
    response = MODEL.generate_content(CODE_REVIEW_PROMPT.format(diff=diff))
    return extract_json(response.text)


def run_test_generation(diff: str) -> dict:
    logger.info("Generating tests...")
    response = MODEL.generate_content(TEST_GENERATION_PROMPT.format(diff=diff))
    return extract_json(response.text)


def compile_report(security: dict, review: dict, tests: dict, title: str, author: str) -> str:
    logger.info("Compiling report...")
    response = MODEL.generate_content(
        REPORT_PROMPT.format(
            security=json.dumps(security, indent=2),
            review=json.dumps(review, indent=2),
            tests=json.dumps(tests, indent=2)
        )
    )
    return response.text


# ── GITLAB ACTIONS ──────────────────────────────────────────────────────────
def post_mr_comment(project_id: int, mr_iid: int, comment: str):
    project = gl.projects.get(project_id)
    mr = project.mergerequests.get(mr_iid)
    mr.notes.create({"body": comment})


def add_mr_labels(project_id: int, mr_iid: int, risk_level: str, score: int):
    project = gl.projects.get(project_id)
    mr = project.mergerequests.get(mr_iid)

    labels = []
    if risk_level in ("CRITICAL", "HIGH"):
        labels.append("security-risk")
    if score < 6:
        labels.append("needs-review")
    if risk_level == "NONE" and score >= 8:
        labels.append("ai-approved")

    mr.labels = list(set((mr.labels or []) + labels))
    mr.save()


# ── API ─────────────────────────────────────────────────────────────────────
@app.post("/webhook/mr")
async def handle_mr_event(request: Request):
    try:
        payload = await request.json()
        event = MREvent(
            project_id=payload["project"]["id"],
            mr_iid=payload["object_attributes"]["iid"],
            diff=payload.get("diff", ""),
            source_branch=payload["object_attributes"]["source_branch"],
            target_branch=payload["object_attributes"]["target_branch"],
            author=payload["user"]["name"],
            title=payload["object_attributes"]["title"]
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    security = run_security_scan(event.diff)
    review = run_code_review(event.diff)
    tests = run_test_generation(event.diff)

    report = compile_report(security, review, tests, event.title, event.author)

    post_mr_comment(event.project_id, event.mr_iid, report)
    add_mr_labels(event.project_id, event.mr_iid, security["risk_level"], review["score"])

    return {"status": "success"}


@app.get("/health")
def health():
    return {"status": "CodeGuard AI is running 🛡️"}