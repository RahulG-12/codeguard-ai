# 🛡️ CodeGuard AI — Intelligent Security & Code Review Agent

> **GitLab Duo Agent Platform Challenge Submission**
> Built by **Rahul Giri** | Powered by **Anthropic Claude** + **GitLab Duo**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110-green.svg)](https://fastapi.tiangolo.com/)
[![Anthropic Claude](https://img.shields.io/badge/Claude-Sonnet-orange.svg)](https://anthropic.com/)

---

## 🎯 What Problem Does This Solve?

Every developer knows the pain:
- You open a Merge Request at 11pm
- Nobody reviews it for 2 days
- When they finally do — they find a SQL injection vulnerability
- Now you're rolling back production at midnight

**CodeGuard AI eliminates this.** It acts as your always-on AI teammate that reviews every MR the moment it's opened — scanning for security holes, reviewing code quality, and generating the tests you forgot to write.

No more waiting. No more vulnerable code shipping unnoticed.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🔒 **Security Scan** | Detects OWASP Top 10, hardcoded secrets, injection risks |
| 👀 **Code Review** | Scores code quality, flags issues, praises good patterns |
| 🧪 **Test Generation** | Writes missing unit tests for all new code in the diff |
| 💬 **MR Comments** | Posts a structured, emoji-rich report directly on the MR |
| 🏷️ **Auto Labeling** | Adds labels like `security-risk`, `ai-approved`, `needs-review` |
| 🐛 **Issue Creation** | Auto-creates GitLab issues for CRITICAL vulnerabilities |

---

## 🏗️ Architecture

```
GitLab MR Opened/Updated
         │
         ▼
  GitLab Duo Workflow
  (.gitlab/duo_workflow/workflow.yml)
         │
         ▼
  CodeGuard Agent (FastAPI)
         │
    ┌────┼────┐
    ▼    ▼    ▼
Security Code  Test
 Scan  Review  Gen
    │    │    │
    └────┼────┘
         ▼
  Claude (Anthropic)
  claude-sonnet-4-20250514
         │
         ▼
  Compiled Report
         │
         ▼
  GitLab MR Comment ✅
  + Labels + Issues
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- GitLab account with API access
- Anthropic API key ([Get one here](https://console.anthropic.com/))
- Docker (optional)

### 1. Clone the Repository
```bash
git clone https://gitlab.com/gitlab-ai-hackathon/codeguard-ai.git
cd codeguard-ai
```

### 2. Set Up Environment Variables
```bash
cp .env.example .env
# Edit .env and fill in your keys:
# ANTHROPIC_API_KEY=your_key_here
# GITLAB_URL=https://gitlab.com
# GITLAB_TOKEN=your_personal_access_token
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Agent
```bash
uvicorn agent.main:app --host 0.0.0.0 --port 8000 --reload
```

### 5. Configure GitLab Webhook
Go to your GitLab project → **Settings → Webhooks** and add:
- **URL:** `http://your-server:8000/webhook/mr`
- **Trigger:** Merge Request events
- **Secret Token:** (optional, recommended)

---

## 🐳 Docker Setup

```bash
# Build
docker build -t codeguard-ai .

# Run
docker run -d \
  -p 8000:8000 \
  --env-file .env \
  --name codeguard-ai \
  codeguard-ai
```

---

## 🧪 Run Tests

```bash
pip install pytest pytest-asyncio httpx
pytest tests/ -v
```

---

## 📋 GitLab Duo Agent Configuration

The agent is configured via `.gitlab/duo_workflow/workflow.yml`.

**Trigger:** Activates on `merge_request_opened` and `merge_request_updated` events.

**Steps:**
1. `security_scan` — Claude analyzes the diff for vulnerabilities
2. `code_review` — Claude scores and reviews code quality
3. `test_generation` — Claude writes unit tests for new code
4. `post_report` — Compiles all findings into a formatted MR comment

---

## 📊 Example Output

When CodeGuard AI reviews an MR, it posts a comment like this:

```
## 🛡️ CodeGuard AI Review — MR !42

### 🔒 Security Analysis
**Risk Level: 🔴 CRITICAL**

| Issue | Line | Fix |
|---|---|---|
| SQL Injection | Line 14 | Use parameterized queries |
| Hardcoded API Key | Line 28 | Move to environment variable |

---

### 👀 Code Review Score: 6/10

**Issues Found:**
- ⚠️ [Major] Missing input validation on `user_id` parameter
- 💡 [Suggestion] Consider extracting DB logic to a repository class

**What's Good:**
- ✅ Clear function naming
- ✅ Consistent error handling pattern

---

### 🧪 Generated Tests
<details>
<summary>Click to see 8 generated unit tests</summary>

\`\`\`python
def test_get_user_valid_id():
    assert get_user(1) is not None
...
\`\`\`
</details>

---
*🤖 Reviewed by CodeGuard AI powered by Anthropic Claude*
```

---

## 🧰 Tech Stack

- **AI Model:** Anthropic Claude (claude-sonnet-4-20250514)
- **Agent Platform:** GitLab Duo Agent Platform
- **Backend:** FastAPI (Python)
- **GitLab Integration:** python-gitlab
- **Containerization:** Docker
- **CI/CD:** GitLab CI

---

## 🗂️ Project Structure

```
codeguard-ai/
├── .gitlab/
│   └── duo_workflow/
│       └── workflow.yml        # GitLab Duo Agent config
├── agent/
│   └── main.py                 # Core agent logic (FastAPI)
├── tests/
│   └── test_agent.py           # Unit tests
├── .env.example                # Environment variables template
├── .gitlab-ci.yml              # CI/CD pipeline
├── Dockerfile                  # Container config
├── requirements.txt            # Python dependencies
├── LICENSE                     # MIT License
└── README.md                   # This file
```

---

## 🏆 Hackathon Context

This project was built for the **GitLab Duo Agent Platform Challenge** (February–March 2026).

**Prize targets:**
- 🥇 Grand Prize ($15,000)
- 🤖 Most Impactful on GitLab & Anthropic ($10,000)
- 🔒 Most Technically Impressive ($5,000)

---

## 👤 Author

**Rahul Giri** — AI/ML Engineer
- 📧 rahulgiri12033@gmail.com
- 🐙 [GitHub](https://github.com/RahulG-12)
- 💼 [LinkedIn](https://linkedin.com/in/rahulgiri)
- 🌐 Portfolio

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

All configuration YAML files are original work subject to MIT License and GitLab's Developer Certificate of Origin v1.1.
