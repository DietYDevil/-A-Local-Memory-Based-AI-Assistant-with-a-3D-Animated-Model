from groq import Groq
from json import load, dump
from datetime import datetime
import os
from dotenv import dotenv_values


env_vars = dotenv_values(".env")
Username = env_vars.get("Username")
Assistantname = env_vars.get("Assistantname")
GroqAPIKey = env_vars.get("GroqAPIKey")

client = Groq(api_key=GroqAPIKey)

def current_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def load_chatlog(n=10):
    try:
        with open(r"Data\chatlog.json", "r") as f:
            chatlog = load(f)[-n*2]       # Last n user+assistant pairs
            return "\n".join([f"{m['role'].capitalize()}: {m['content']}" for m in chatlog])
    except:
        return ""
    
def summarize_with_mistral(chat_text: str) -> str:
    prompt = f"Summarize the following conversation in a single paragraph to help remember it later:\n\n{chat_text}\n\nSummary:"
    
    completion = client.chat.completions.create(
        model="mistral-7b-8k",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=512,
        temperature=0.5
    )
    
    return completion.choices[0].message.content.strip()

def save_to_long_memory(summary: str):
    try:
        with open(r"Data\long_memory.json", "r") as f:
            memory = load(f)
    except FileNotFoundError:
        memory = []

    memory.append({
        "timestamp": current_timestamp(),
        "summary": summary
    })

    with open(r"Data\long_memory.json", "w") as f:
        dump(memory, f, indent=4)
        
def summarize_and_store_memory():
    chat_text = load_chatlog(n=5)
    if not chat_text.strip():
        return
    summary = summarize_with_mistral(chat_text)
    save_to_long_memory(summary)
    print("🧠 Genni remembered this conversation forever.")