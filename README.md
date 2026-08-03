# Email Agent

A local-first AI agent that reads my Gmail inbox and sorts emails into categories
like "Promotional" or "Needs reply". I built it to learn how AI agents actually work
end to end — the tool-calling loop, real API integration, safety guardrails, and
deployment

Everything runs locally by default using an open-source model (no API cost, and email
data never leaves my machine). I later added the option to swap in a hosted frontier
model to compare the two.

## What it does

- Connects to Gmail (read-only) via the Gmail API and OAuth2
- Feeds recent emails to an LLM, which decides how to categorize each one
- Applies labels through a tool the model can call
- Asks for my approval before any action that changes state
- Logs every decision it makes, with timestamps

## How it works

The core is a hand-written agent loop rather than a framework. The model doesn't run
code itself — it can only return structured JSON saying "call this tool with these
arguments." My code executes the real function, feeds the result back, and the model
continues until it has an answer. Understanding this loop was the main goal of the
project, since every agent framework is essentially a wrapper around it.

Tools are split into read-only actions (list emails, read a body), which run freely,
and state-changing actions (apply a label), which require approval. This keeps the
agent from doing anything irreversible without a human in the loop.

## Stack

- **Python**
- **Ollama** running **Qwen3 8B** locally (default)
- **Gmail API** with OAuth2
- **Docker** for containerization
- **launchd** for scheduling on macOS
- Optional: **Google Gemini** via its OpenAI-compatible API

## Model options

The model provider is switchable through an environment variable, so the same agent
loop works against either a local or a hosted model:

```bash
python src/email_agent.py auto              # local Qwen3 (default)
PROVIDER=gemini python src/email_agent.py auto   # hosted Gemini
```

I used this to compare a small local model against a frontier one on the same inbox.
The frontier model was clearly more reliable at tool calling and more consistent in
its categorization, but the local model is free, fully private, and faster for a burst
of calls since there's no network round-trip or rate limiting. Which one is "better"
depends on whether you care most about capability, cost, privacy, or control — that
tradeoff was one of the more interesting things I took away from the project.

## Running it

```bash
# Set up
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Add Gmail OAuth credentials to credentials/credentials.json
# (created via Google Cloud Console — see notes)

# Run interactively (asks before labeling)
python src/email_agent.py

# Run unattended (auto-approves; used for scheduling)
python src/email_agent.py auto
```

### Docker

```bash
docker build -t email-agent .
docker run --rm \
  --add-host=host.docker.internal:host-gateway \
  -e OLLAMA_HOST=http://host.docker.internal:11434 \
  -v $(pwd)/credentials:/app/credentials \
  email-agent
```

## Notes

- Secrets (`credentials.json`, `token.json`, `.env`) are git-ignored and never committed.
- Label actions are currently simulated (they log what they'd do rather than modifying
  the inbox) — a deliberate safety choice while building.
- Built in phases: raw API call → agent loop → Gmail integration → safety rails →
  deployment → model comparison.
