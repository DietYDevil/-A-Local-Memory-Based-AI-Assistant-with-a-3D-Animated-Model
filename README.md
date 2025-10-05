# -A-Local-Memory-Based-AI-Assistant-with-a-3D-Animated-Model
Developed a personal AI assistant capable of multimodal interaction, including voice, text, body movement, and facial recognition,The assistant can perform web searches, manage local files, and features a self- animating 3D model that responds to interactions. The GUI is launched using Animaze.

In Main folder

        main1.py file
        requirements.txt file
        .env file
        local.py file


Backend folder

    --> Automation.py
    --> Chatbot.py
    --> displaytext.py
    --> MemoryManager.py
    --> Model.py
    --> RealtimeSearchEngine.py
    --> SpeechToText.py
    --> summerize.py
    --> TextToSpeech.py

    
Frontend folder

    --> animaze.py

    
Data Folder 

    --> Chatlog.json


--> create a virtual environment in this folder and run in terminal

    pip install -r requirements.txt

--> Install Animaze launcher and do setup

    https://www.animaze.us/download

--> Create API key of Groq , Cohere, Huggingface ALL ARE FREE.

    https://console.groq.com/keys
    https://dashboard.cohere.com/welcome/login
    https://huggingface.co/join

--> Put your API Key in .env file

--> In Animaze laucnch the 3D model as u want in .vrm format ( I have uploaded one model)
--> in animaze settings turn oon web server port 3000

--> now run main1.py file 

ENJOY !

( Still in progress)
