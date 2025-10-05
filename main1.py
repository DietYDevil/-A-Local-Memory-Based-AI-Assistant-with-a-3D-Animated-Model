# main.py  -- updated to integrate MemoryManager (long-term + short-term memory)
# Based on original main.py uploaded by user. (I inspected it to keep changes minimal.) :contentReference[oaicite:1]{index=1}

from Backend.Model import FirstLayerDMM
from Backend.RealtimeSearchEngine import RealtimeSearchEngine
from Backend.Automation import Automation
from Backend.Chatbot import ChatBot
from Backend.TextToSpeech import TextToSpeech
from Backend.MemoryManager import MemoryManager   # NEW
from dotenv import dotenv_values
# from time import sleep
import asyncio
from Frontend.animaze import eye_blink, animation
# from Backend.speechtotxt import SpeechRecognition
# from Backend.SpeechToText import SpeechRecognition
import os
import time
import logging
logging.disable(logging.CRITICAL)


# ---------------- Config ----------------
env_vars = dotenv_values(".env")
Username = env_vars.get("Username", "User")
Assistantname = env_vars.get("Assistantname", "Genni")
COHERE_API_KEY = env_vars.get("COHERE_API_KEY")  # optional, used by MemoryManager summarizer
MEMORY_DB = env_vars.get("MEMORY_DB", "genni_memory.db")
# device name used earlier in your project for TTS -> Animaze routing should remain unchanged
#-----------------------------------------

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

DefaultMessage = f'''{Username} : Hello {Assistantname} ! How are you ?
{Assistantname} : Hello sir, I'm doing well , how may i help you sir today?'''

subprocesses = []
Functions = ["open", "close", "play", "system", "content", "google search","youtube search"]

# Instantiate MemoryManager (creates DB if needed)
memory = MemoryManager(db_path=MEMORY_DB, cohere_api_key=COHERE_API_KEY)

# ----------------- Helper functions -----------------
def build_query_with_memory(user_query: str, recent_count: int = 8, summary_count: int = 4) -> str:
    """
    Build a prompt/context by combining:
      - latest persona (if present in summaries)
      - long-term summaries (most recent summaries)
      - recent short-term messages (uncompressed)
      - then the user's query
    This is a simple prefixing approach so existing ChatBot/RealtimeSearchEngine can stay unchanged.
    """
    # get long-term summaries
    longterm = memory.get_recent_summaries_text(limit=summary_count)
    # get recent uncompressed messages (short-term context)
    recent_msgs = memory.get_recent(n=recent_count)
    recent_text = "\n".join([f"{m['role']}: {m['content']}" for m in recent_msgs]) if recent_msgs else ""

    prefix_parts = []
    if longterm:
        prefix_parts.append("Long-term memory summaries:\n" + longterm + "\n")
    if recent_text:
        prefix_parts.append("Recent context:\n" + recent_text + "\n")
    prefix_parts.append("Now respond to the user's message below.\n")
    prefix_parts.append("User: " + user_query)
    return "\n".join(prefix_parts)

async def memory_background_loop():
    """
    Background job: periodically compress old messages into concise summaries.
    Runs every 10 minutes by default. Adjust timing as desired.
    """
    while True:
        try:
            # compress when there are >= 40 uncompressed messages (you can tune)
            r = memory.compress_old_if_needed(min_messages=40, batch_size=400)
            if r:
                logging.info("[Memory] Compressed old messages into summary.")
        except Exception as e:
            logging.exception("[Memory] background error: %s", e)
        await asyncio.sleep(60 * 10)

# ----------------- talk_animation (kept mostly as original) -----------------
async def talk_animation(response):
    if len(str(response).split(".")) < 2:
        await TextToSpeech(response)
    else:
        await asyncio.gather(
            TextToSpeech(response),
            animation("TriggerIdle",26,delay=0))

# ----------------- Main loop -----------------
async def main():
    # start memory background task
    asyncio.create_task(memory_background_loop())

    while True:
        # keep idle animation running between interactions
        await animation("TriggerIdle",17)

        # get user input (your original console input)
        user_input = input(f"\n{Username} : ")

        # store user input to memory immediately
        try:
            memory.add_message("user", user_input)
        except Exception as e:
            logging.warning("Failed to store user message in memory: %s", e)

        Decision = FirstLayerDMM(user_input)
        # print(f"{Username} : {user_input}")
        # print(f"\nDecision : {Decision}\n")

        G = any([i for i in Decision if i.startswith("general")])
        R = any([i for i in Decision if i.startswith("realtime")])

        Merged_query = " and ".join(
            [" ".join(i.split()[1:]) for i in Decision if i.startswith("general") or i.startswith("realtime")]
        )

        # automation handlers (unchanged)
        for queries in Decision:
            if any(queries.startswith(func) for func in Functions):
                await Automation(list(Decision))

        # ------------- Combined realtime & general (prefer realtime) -------------
        if G and R or R:
            # include memory context for web queries too
            full_query = build_query_with_memory(Merged_query)
            Answer = await RealtimeSearchEngine(full_query)
            print(f"{Assistantname} : {Answer}")
            # store assistant reply
            try:
                memory.add_message("assistant", Answer)
            except Exception as e:
                logging.warning("Failed to store assistant message in memory: %s", e)
            await talk_animation(Answer)

        # ------------- system commands & simple actions -------------
        elif "exit the system" in user_input.lower():
            await TextToSpeech("Goodbye Sir !")
            await animation("TriggerSpecialAction",19)
            print("Genni : Goodbye Sir !")
            break

        elif "turn around" in user_input.lower():
            await TextToSpeech("yes sir, sure i can !")
            await animation("TriggerSpecialAction",23,delay=1)

        elif "can u dance" in user_input.lower():
            await TextToSpeech("yes sir, i can which one u like to see sir?")

        # ------------- normal non-realtime chatbot branch -------------
        else:
            for queries in Decision:
                if "general" in queries:
                    query = queries.replace("general ", "")
                    # build query with memory prefix so ChatBot can see context
                    full_query = build_query_with_memory(query)
                    # Note: ChatBot appears to be synchronous in your original file; keep the same call style
                    Answer = ChatBot(full_query)
                    print(f"{Assistantname} : {Answer}")
                    # store assistant reply
                    try:
                        memory.add_message("assistant", Answer)
                    except Exception as e:
                        logging.warning("Failed to store assistant message in memory: %s", e)
                    await talk_animation(Answer)

                elif "realtime" in queries:
                    query = queries.replace("realtime ", "")
                    full_query = build_query_with_memory(query)
                    # RealtimeSearchEngine is async in your original -> keep await
                    Answer = await RealtimeSearchEngine(full_query)
                    print(f"{Assistantname} : {Answer}")
                    try:
                        memory.add_message("assistant", Answer)
                    except Exception as e:
                        logging.warning("Failed to store assistant message in memory: %s", e)
                    await talk_animation(Answer)


if __name__ == "__main__":
    print("\n\nPlease write 'exit the system' to close the programme\n\n")

    # start initial animaze actions (kept from original)
    asyncio.run(eye_blink("SetOverride","Auto Blink",True))
    asyncio.run(animation("TriggerSpecialAction",0))

    asyncio.run(TextToSpeech("Hello sir,Your Genni is here. How may i help you sir ?"))

    # run main loop
    asyncio.run(main())
