import os
import threading
import asyncio
from flask import Flask
from bot import main  # on importe le vrai bot

app = Flask(__name__)

@app.get("/")
def home():
    return "Bot running"

def run_bot():
    asyncio.run(main())

if __name__ == "__main__":
    # lance bot en arrière-plan
    threading.Thread(target=run_bot, daemon=True).start()

    # obligatoire pour Render
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
