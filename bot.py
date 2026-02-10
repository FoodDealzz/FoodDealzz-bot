import os
import threading
from flask import Flask

from bot import run_bot  # on importe la fonction qui lance le bot

app = Flask(__name__)

@app.get("/")
def home():
    return "OK"

if __name__ == "__main__":
    # lance le bot dans un thread (ok car run_bot va gérer son propre asyncio)
    threading.Thread(target=run_bot, daemon=True).start()

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
