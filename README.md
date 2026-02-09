# AI Prompt Logger

## Run locally (free stub mode)
1) Create a venv:
   python -m venv .venv
   .\.venv\Scripts\activate   (Windows)
   source .venv/bin/activate  (Mac/Linux)

2) Install deps:
   pip install -r requirements.txt

3) Copy env file:
   copy .env.example .env   (Windows)
   cp .env.example .env     (Mac/Linux)

4) Run:
   python app.py

Open: http://localhost:5000

## Enable real AI replies
Edit .env:
USE_REAL_AI=true
OPENAI_API_KEY=...your key...

Then restart the server.