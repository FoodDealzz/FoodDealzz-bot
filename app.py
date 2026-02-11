import os
import threading
from flask import Flask

from bot import main  # on démarre le bot depuis bot.py

app = Flask(__name__)

@app.get("/")
def home():
    return "OK"

def run_bot():
    main()

if __name__ == "__main__":
    # Lance le bot en arrière-plan
    threading.Thread(target=run_bot, daemon=True).start()

    # Obligatoire pour Render Web Service
    port = int(os.environ.get("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
