import asyncio
from concurrent.futures import ThreadPoolExecutor
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import dotenv_values
import os
import mtranslate as mt

# Load environment variables
env_vars = dotenv_values(".env")
InputLanguage = env_vars.get("InputLanguage")

# Setup directories and Chrome options
current_dir = os.getcwd()
Link = f"{current_dir}/Data/Voice.html"
TempDirPath = rf"{current_dir}/Frontend/Files"

chrome_options = Options()
chrome_options.add_argument("--use-fake-ui-for-media-stream")
chrome_options.add_argument("--use-fake-device-for-media-stream")
chrome_options.add_argument("--headless=new")

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

executor = ThreadPoolExecutor()

# Translate + Query Cleanup
def SetAssistantStatus(Status):
    with open(rf"{TempDirPath}/Status.data", "w", encoding="utf-8") as file:
        file.write(Status)

def QueryModifier(Query):
    new_query = Query.lower().strip()
    query_words = new_query.split()  # noqa: F841
    question_words = ["how", "what", "who", "where", "when", "why", "which", "whose", "whom", "can you", "what's", "where's", "how's"]
    
    if any(word + " " in new_query for word in question_words):
        new_query = new_query.rstrip(".?!") + "?"
    else:
        new_query = new_query.rstrip(".?!") + "."

    return new_query.capitalize()

def UniversalTranslator(Text):
    return mt.translate(Text, "en", "auto").capitalize()

# Async wrapper for blocking Selenium calls
async def get_text_async():
    return await asyncio.get_event_loop().run_in_executor(executor, lambda: driver.find_element(By.ID, "output").text)

async def click_button_async(button_id):
    return await asyncio.get_event_loop().run_in_executor(executor, lambda: driver.find_element(By.ID, button_id).click())

# 🎤 Async Speech Recognition
async def SpeechRecognition():
    driver.get("file:///" + Link)
    await click_button_async("start")

    while True:
        await asyncio.sleep(1.2)  # Sleep a bit to avoid tight loop

        try:
            Text = await get_text_async()

            if Text:
                await click_button_async("end")

                if "en" in InputLanguage.lower():
                    return QueryModifier(Text)
                else:
                    SetAssistantStatus("Translating ...")
                    return QueryModifier(UniversalTranslator(Text))
        except Exception:
            continue

# 🧪 Main Loop to Test
async def main():
    while True:
        result = await SpeechRecognition()
        print("Recognized:", result)

# 🔁 Start the async loop
if __name__ == "__main__":
    asyncio.run(main())
