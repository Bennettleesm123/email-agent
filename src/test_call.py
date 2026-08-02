import requests

# The address of your local Ollama server's chat endpoint
url = "http://localhost:11434/v1/chat/completions"

# The data we send to the model, as a Python dictionary
payload = {
    "model": "qwen3:8b",
    "messages": [
        {"role": "user", "content": "Explain what an API is in one sentence."}
    ]
}

# YOU: send a POST request. Use requests.post(), pass it `url`,
# and pass the payload with the keyword argument json=payload.
# Store what comes back in a variable called `response`.
response = requests.post(url, json = payload)

# YOU: convert the response to JSON and store it in `data`
data = response.json()
answer = data['choices'][0]['message']['content']
# YOU: print `data` so you can see the full structure
print(answer)