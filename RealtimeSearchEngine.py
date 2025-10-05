import datetime
import aiofiles
import asyncio
from dotenv import dotenv_values
from groq import Groq
from json import loads, dumps
from googlesearch import search

# Load .env config
env_vars = dotenv_values(".env")
Username = env_vars.get("Username")
Assistantname = env_vars.get("Assistantname")
GroqAPIKey = env_vars.get("GroqAPIKey")
GroqModel  = env_vars.get("GroqModel")

# Initialize Groq client
client = Groq(api_key=GroqAPIKey)

# System message
System = f"""Hello, I am {Username}, You are a very accurate and advanced AI chatbot named {Assistantname} which has real-time up-to-date information from the internet.
*** Provide Answers In a Professional Way, make sure to add full stops, commas, question marks, and use proper grammar.***
*** Just answer the question from the provided data in a professional way. ***"""

# Initial chat memory
SystemChatBot = [
    {"role": "system", "content": System},
    {"role": "user", "content": "Hi"},
    {"role": "assistant", "content": "Hello, how can I help you sir?"}
]

# Clean empty lines
def AnswerModifier(Answer):
    lines = Answer.split('\n')
    non_empty_lines = [line for line in lines if line.strip()]
    return '\n'.join(non_empty_lines)

# Real-time info
def Information():
    now = datetime.datetime.now()
    return (
        f"Use This Real-time Information if needed:\n"
        f"Day: {now.strftime('%A')}\n"
        f"Date: {now.strftime('%d')}\n"
        f"Month: {now.strftime('%B')}\n"
        f"Year: {now.strftime('%Y')}\n"
        f"Time: {now.strftime('%H')} hours, {now.strftime('%M')} minutes, {now.strftime('%S')} seconds.\n"
    )

# Google search (non-blocking using asyncio.to_thread)
async def GoogleSearch(query):
    results = await asyncio.to_thread(search, query, advanced=True, num_results=5)
    Answer = f"The search results for '{query}' are:\n[start]\n"
    for i in results:
        Answer += f"Title: {i.title}\nDescription: {i.description}\n\n"
    Answer += "[end]"
    return Answer

# Load chatlog
async def load_chatlog():
    try:
        async with aiofiles.open("Data/ChatLog.json", mode="r") as f:
            content = await f.read()
            return loads(content)
    except FileNotFoundError:
        return []

# Save chatlog
async def save_chatlog(messages):
    async with aiofiles.open("Data/ChatLog.json", mode="w") as f:
        await f.write(dumps(messages, indent=4))

# Core engine
async def RealtimeSearchEngine(prompt: str):
    global SystemChatBot

    # Load history
    messages = await load_chatlog()
    messages.append({"role": "user", "content": prompt})

    # Prepare fresh system + search + info
    search_result = await GoogleSearch(prompt)
    system_copy = SystemChatBot.copy()
    system_copy.append({"role": "system", "content": search_result})
    system_copy.append({"role": "system", "content": Information()})

    # Chat completion with streaming
    completion = await asyncio.to_thread(
        client.chat.completions.create,
        model=GroqModel,
        messages=system_copy + messages,
        temperature=0.7,
        max_tokens=2048,
        top_p=1,
        stream=True,
        stop=None
    )

    # Handle stream
    Answer = ""
    for chunk in completion:
        if chunk.choices[0].delta.content:
            Answer += chunk.choices[0].delta.content

    Answer = Answer.strip().replace("</s>", "")
    messages.append({"role": "assistant", "content": Answer})
    await save_chatlog(messages)

    return AnswerModifier(Answer)

# Run if main
async def main():
    while True:
        user_input = input("Enter your query: ")
        reply = await RealtimeSearchEngine(user_input)
        print(reply)

# Start the event loop
if __name__ == "__main__":
    asyncio.run(main())
