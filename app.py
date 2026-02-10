import os
import threading
from flask import Flask
from bot import run_bot

app = Flask(__name__)

@app.get("/")
def home():
    return "OK"

# On démarre le bot en arrière-plan
threading.Thread(target=run_bot, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
