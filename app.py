import os
from flask import Flask
from threading import Thread
from bot import run_bot

app = Flask(__name__)

# Lance le bot une seule fois (thread)
Thread(target=run_bot, daemon=True).start()

@app.get("/")
def home():
    return "OK"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
