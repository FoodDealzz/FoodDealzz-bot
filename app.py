import os
import threading
import asyncio
from flask import Flask

# 👉 importe ton code bot depuis bot.py
# IMPORTANT: dans bot.py il doit y avoir une fonction async "main()"
from bot import main

app = Flask(__name__)

@app.get("/")
def home():
    return "OK"

def run_bot():
    asyncio.run(main())

if name == "__main__":
    # lance le bot en arrière-plan
    threading.Thread(target=run_bot, daemon=True).start()

    # ouvre le port pour Render
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
