import requests

def ask_ollama(prompt, model="llama3.2"):
    url = "http://localhost:11434/api/generate"
    data = {
        "model": model,
        "prompt": prompt,
        "stream": False  # if you want streaming, set True and use a generator
    }

    response = requests.post(url, json=data)
    if response.status_code == 200:
        return response.json()["response"]
    else:
        return f"Error: {response.status_code} - {response.text}"

def chat():
    print("👩‍💻 Welcome to your local chatbot! Type 'exit' to quit.")
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            break
        reply = ask_ollama(user_input)
        print(f"AI he: {reply}")

if __name__ == "__main__":
    chat()
