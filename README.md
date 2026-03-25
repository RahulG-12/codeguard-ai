# 🛡️ CodeGuard AI — Intelligent Security & Code Review Agent

> Built by Rahul Giri | Powered by Google Gemini + GitLab

---

## 🚀 What is this?

CodeGuard AI is an automated AI agent that reviews every Merge Request.

It:
- 🔒 Finds security vulnerabilities
- 👀 Reviews code quality
- 🧪 Generates unit tests
- 💬 Posts comments on GitLab MR

---

## ⚙️ Tech Stack

- FastAPI (Python)
- Google Gemini API
- GitLab API
- Docker
- GitLab CI/CD

---

## 🧠 How it works

GitLab MR → Webhook → FastAPI → Gemini → GitLab Comment

---

## 🚀 Run Locally

```bash
pip install -r requirements.txt
uvicorn agent.main:app --reload