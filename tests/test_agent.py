"""
Unit Tests for CodeGuard AI Agent
"""
import pytest
import json
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from agent.main import app, run_security_scan, run_code_review, run_test_generation

client = TestClient(app)

SAMPLE_DIFF = """
+def get_user(user_id):
+    query = f"SELECT * FROM users WHERE id = {user_id}"
+    return db.execute(query)
+
+API_KEY = "sk-abc123hardcoded"
"""

MOCK_SECURITY = {
    "risk_level": "CRITICAL",
    "vulnerabilities": [
        {
            "type": "SQL Injection",
            "line": "+    query = f\"SELECT * FROM users WHERE id = {user_id}\"",
            "description": "Direct string interpolation in SQL query allows injection",
            "fix": "Use parameterized queries: cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))"
        },
        {
            "type": "Hardcoded Secret",
            "line": "+API_KEY = \"sk-abc123hardcoded\"",
            "description": "API key hardcoded in source code",
            "fix": "Move to environment variable: API_KEY = os.environ['API_KEY']"
        }
    ],
    "summary": "Critical security issues found including SQL injection and hardcoded credentials."
}

MOCK_REVIEW = {
    "score": 4,
    "issues": [
        {
            "severity": "major",
            "line": "+def get_user(user_id):",
            "description": "No input validation or type checking",
            "fix": "Add type hints and validate user_id is a positive integer"
        }
    ],
    "positives": ["Function name is descriptive"],
    "summary": "Code has significant security and quality issues."
}

MOCK_TESTS = {
    "test_framework": "pytest",
    "filename": "tests/test_user.py",
    "test_code": "def test_get_user_valid_id():\n    assert get_user(1) is not None\n\ndef test_get_user_invalid_id():\n    with pytest.raises(ValueError):\n        get_user(-1)",
    "coverage_estimate": "80%",
    "summary": "Tests cover basic usage and invalid input handling."
}


# ── Health Check ──────────────────────────────────────────────────────────────
def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "CodeGuard AI is running 🛡️"


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "CodeGuard AI Agent"
    assert "Rahul Giri" in data["author"]


# ── Security Scan ─────────────────────────────────────────────────────────────
@patch("agent.main.claude")
def test_security_scan_returns_dict(mock_claude):
    mock_response = MagicMock()
    mock_response.content[0].text = json.dumps(MOCK_SECURITY)
    mock_claude.messages.create.return_value = mock_response

    result = run_security_scan(SAMPLE_DIFF)
    assert isinstance(result, dict)
    assert result["risk_level"] == "CRITICAL"
    assert len(result["vulnerabilities"]) == 2


# ── Code Review ───────────────────────────────────────────────────────────────
@patch("agent.main.claude")
def test_code_review_returns_dict(mock_claude):
    mock_response = MagicMock()
    mock_response.content[0].text = json.dumps(MOCK_REVIEW)
    mock_claude.messages.create.return_value = mock_response

    result = run_code_review(SAMPLE_DIFF)
    assert isinstance(result, dict)
    assert "score" in result
    assert result["score"] == 4


# ── Test Generation ───────────────────────────────────────────────────────────
@patch("agent.main.claude")
def test_test_generation_returns_dict(mock_claude):
    mock_response = MagicMock()
    mock_response.content[0].text = json.dumps(MOCK_TESTS)
    mock_claude.messages.create.return_value = mock_response

    result = run_test_generation(SAMPLE_DIFF)
    assert isinstance(result, dict)
    assert "test_code" in result
    assert result["test_framework"] == "pytest"


# ── Webhook ───────────────────────────────────────────────────────────────────
@patch("agent.main.run_security_scan", return_value=MOCK_SECURITY)
@patch("agent.main.run_code_review", return_value=MOCK_REVIEW)
@patch("agent.main.run_test_generation", return_value=MOCK_TESTS)
@patch("agent.main.compile_report", return_value="## CodeGuard AI Review\nAll good!")
@patch("agent.main.post_mr_comment")
@patch("agent.main.add_mr_labels")
@patch("agent.main.create_security_issue")
def test_webhook_success(mock_issue, mock_labels, mock_comment, mock_report, mock_tests, mock_review, mock_security):
    payload = {
        "project": {"id": 123},
        "object_attributes": {
            "iid": 42,
            "source_branch": "feature/new-login",
            "target_branch": "main",
            "title": "Add user login endpoint"
        },
        "user": {"name": "Rahul Giri"},
        "diff": SAMPLE_DIFF
    }
    response = client.post("/webhook/mr", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["mr"] == 42
    assert data["risk_level"] == "CRITICAL"
