import requests
import json
from datetime import datetime

URL = "http://localhost:11434/v1/chat/completions"
MODEL = "qwen3:8b"


# ---- STEP 1: The actual tool (a real Python function) ----
def get_current_time():
    return datetime.now().strftime("%H:%M:%S")


# ---- STEP 2: Describe the tool to the model ----
# This is the "menu" we hand the model so it knows the tool exists.
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Get the current time of day. Use when the user asks what time it is.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    }
]

# A lookup so we can find the real function by its name string later.
available_tools = {"get_current_time": get_current_time}


def run_agent(user_message):
    # The conversation history — starts with the user's message.
    messages = [{"role": "user", "content": user_message}]

    # ---- STEP 3: The agent loop ----
    while True:
        payload = {
            "model": MODEL,
            "messages": messages,
            "tools": tools,      # <-- the new part: we hand over the tool menu
        }

        response = requests.post(URL, json=payload)
        data = response.json()
        message = data["choices"][0]["message"]

        # Add the model's reply to the history no matter what.
        messages.append(message)

        # ---- STEP 4: Did the model ask to call a tool? ----
        tool_calls = message.get("tool_calls")

        if not tool_calls:
            # No tool wanted → this is the final answer. Return it.
            # YOU: return message["content"]
            return message ['content']

        # ---- STEP 5: Run each requested tool, feed results back ----
        for call in tool_calls:
            fn_name = call["function"]["name"]
            print(f"[model wants to call: {fn_name}]")

            # Look up and run the real Python function.
            # YOU: get the function from available_tools using fn_name, then call it.
            result = available_tools[fn_name]()

            # Send the tool's result back to the model as a new message.
            messages.append({
                "role": "tool",
                "tool_call_id": call["id"],
                "content": str(result),
            })
        # Loop repeats: model now sees the result and can answer.


# ---- Try it ----
print(run_agent("what time is it now?"))