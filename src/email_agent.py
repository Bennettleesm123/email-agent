import requests
import json
from tools.gmail_tools import list_recent_emails, get_email_body, label_email
from datetime import datetime
import os
from dotenv import load_dotenv
import time

load_dotenv()

PROVIDER = os.environ.get("PROVIDER", "ollama")

if PROVIDER == "ollama":
    OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    URL = f"{OLLAMA_HOST}/v1/chat/completions"
    MODEL = "qwen3:8b"
    HEADERS = {}
elif PROVIDER == "gemini":
    URL = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
    MODEL = "gemini-3.5-flash"
    HEADERS = {"Authorization": f"Bearer {os.environ['GEMINI_API_KEY']}"}
else:
    raise ValueError(f"Unknown PROVIDER: {PROVIDER}")
# Tools in this set require human approval before running.
# Read-only tools (list, get_body) are NOT here, so they run freely.
ACTION_TOOLS = {"label_email"}
LOG_FILE = "logs/agent_log.txt"
os.makedirs("logs", exist_ok=True)

def log(text):
    # Append a timestamped line to the log file AND print it.
    line = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | {text}"
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")
    print(line)

# Tool schemas handed to the model so it knows what it can call and
# what arguments each function expects.
tools = [
    {
        "type": "function",
        "function": {
            "name": "list_recent_emails",
            "description": "List the most recent emails. Returns id, sender, subject for each.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_email_body",
            "description": "Get a preview of a specific email's body. Requires the email's id.",
            "parameters": {
                "type": "object",
                "properties": {
                    "email_id": {"type": "string", "description": "The id of the email"}
                },
                "required": ["email_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "label_email",
            "description": "Apply a label to an email, e.g. 'Promotional' or 'Needs reply'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "email_id": {"type": "string", "description": "The id of the email"},
                    "label": {"type": "string", "description": "The label to apply"}
                },
                "required": ["email_id", "label"]
            }
        }
    }
]

available_tools = {
    "list_recent_emails": list_recent_emails,
    "get_email_body": get_email_body,
    "label_email": label_email,
}


def run_agent(user_message, max_turns=12, auto=False):
    messages = [{"role": "user", "content": user_message}]

    # max_turns is a safety cap so a confused model can't loop forever.
    for turn in range(max_turns):
        payload = {"model": MODEL, "messages": messages, "tools": tools}
        # Retry on rate-limit (429) errors, which the free tier hits easily.
        for attempt in range(5):
            response = requests.post(URL, json=payload, headers=HEADERS)
            data = response.json()

            # A 429 error comes back as a list with an "error" dict inside.
            if isinstance(data, list) and data and "error" in data[0]:
                if data[0]["error"].get("code") == 429:
                    wait = 2 ** attempt  # 1s, 2s, 4s, 8s, 16s — exponential backoff
                    print(f"[rate limited, waiting {wait}s...]")
                    time.sleep(wait)
                    continue  # try again
            break  # success (or a non-429 error) — stop retrying
        message = data["choices"][0]["message"]
        messages.append(message)

        tool_calls = message.get("tool_calls")
        if not tool_calls:
            return message["content"]

        for call in tool_calls:
            fn_name = call["function"]["name"]
            args = json.loads(call["function"]["arguments"])

            log(f"MODEL WANTS: {fn_name}({args})")

            # ---- The safety gate ----
            if fn_name in ACTION_TOOLS:
                if auto:
                    # Unattended run: auto-approve (safe because actions are simulated).
                    log(f"AUTO-APPROVED: {fn_name}({args})")
                else:
                    answer = input(f"   >> Approve {fn_name}({args})? [y/n]: ")
                    if answer.strip().lower() != "y":
                        result = f"SKIPPED by human: {fn_name}"
                        log(result)
                        messages.append({
                            "role": "tool",
                            "tool_call_id": call["id"],
                            "content": str(result),
                        })
                        continue

            # If we get here, it's either a read tool or an approved action.
            fn = available_tools[fn_name]
            result = fn(**args)

            # log the result of the tool that just ran.
            log(f"EXECUTED: {fn_name} -> {result}")

            messages.append({
                "role": "tool",
                "tool_call_id": call["id"],
                "content": str(result),
            })

    return "(stopped: reached max turns)"


if __name__ == "__main__":
    import sys

    task = (
        "Review my 5 most recent emails. For each one, decide if it's "
        "promotional or needs my attention, and label them accordingly."
    )

    # Pass "auto" as a command-line argument for unattended runs.
    auto_mode = "auto" in sys.argv
    print(run_agent(task, auto=auto_mode))