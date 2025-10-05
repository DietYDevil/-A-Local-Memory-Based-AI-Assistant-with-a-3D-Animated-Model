import os
import edge_tts
from dotenv import dotenv_values
import sounddevice as sd
import soundfile as sf
import asyncio
# import random 

env_vars = dotenv_values(".env")
AssistantVoice = env_vars.get("AssistantVoice")


async def TextToAudioFile(text) -> None:
    filepath = r"Data/speech.mp3"
    
    if os.path.exists(filepath):
        os.remove(filepath)
        
    communicate = edge_tts.Communicate(text, AssistantVoice, pitch='+5Hz',rate='+13%')
    
    await communicate.save(filepath)
    

# New function to play audio using sounddevice
async def play_audio(file_path, func=lambda r=None: True):
    try:
        data, fs = sf.read(file_path, dtype='float32')
        sd.play(data, fs, device='CABLE In 16 Ch (2- VB-Audio Virtual Cable), Windows DirectSound')

        # Wait until audio playback is done or interrupted by func
        while sd.get_stream().active:
            if func() == False:  # noqa: E712
                sd.stop()
                break
            await asyncio.sleep(0.1)  

        return True

    except Exception as e:
        print(f"Error playing audio: {e}")
        return False

    finally:
        try:
            func(False)
        except Exception as e:
            print(f"Error in cleanup: {e}")


async def TTS(Text, func=lambda r=None: True):
    try:
        await TextToAudioFile(Text)  # Convert to speech and save file
        return await play_audio(r"Data/speech.mp3", func)  # Play using sounddevice
    except Exception as e:
        print(f"Error in TTS: {e}")
        return False


# Function to manage Text-to-Speech with additional responses for long text
async def TextToSpeech(Text, func=lambda r=None: True):
    Data = str(Text).split(".")  # Split the text by periods into a list of sentences

    # List of predefined responses for cases where the text is too long
    responses = [
        "The rest of the result has been printed to the chat screen, kindly check it out sir.",
        "The rest of the text is now on the chat screen, sir, please check it.",
        "You can see the rest of the text on the chat screen, sir.",
        "The remaining part of the text is now on the chat screen, sir.",
        "Sir, you'll find more text on the chat screen for you to see.",
        "The rest of the answer is now on the chat screen, sir.",
        "Sir, please look at the chat screen, the rest of the answer is there.",
        "You'll find the complete answer on the chat screen, sir.",
        "The next part of the text is on the chat screen, sir.",
        "Sir, please check the chat screen for more information.",
        "There's more text on the chat screen for you, sir.",
        "Sir, take a look at the chat screen for additional text.",
        "You'll find more to read on the chat screen, sir.",
        "Sir, check the chat screen for the rest of the text.",
        "The chat screen has the rest of the text, sir.",
        "There's more to see on the chat screen, sir, please look.",
        "Sir, the chat screen holds the continuation of the text.",
        "You'll find the complete answer on the chat screen, kindly check it out sir.",
        "Please review the chat screen for the rest of the text, sir.",
        "Sir, look at the chat screen for the complete answer."
    ]
    
    # If the text is very long (more than 4 sentences and 250 characters), add a response message
    # if len(Data) > 5 or len(Text) >=250:
    #     await TTS(" ".join(Text.split(".")[0:2]) + ". " + random.choice(responses),func)
    # # Otherwise, just play the whole text
    # else:
    await TTS(Text,func)


if __name__ == "__main__":
    while True:
        TextToSpeech(input("Enter the text : "))