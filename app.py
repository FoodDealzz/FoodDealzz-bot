import os
import threading
import asyncio
import traceback
from flask import Flask

from bot import main  # main() doit exister dans bot.py (async)

app = Flask(__name__)

@app.get("/")
def home():
    return "Bot running ✅"

def run_bot():
    try:
        print("=== BOT THREAD STARTING ===", flush=True)
        asyncio.run(main())
        print("=== BOT THREAD STOPPED (main ended) ===", flush=True)
    except Exception:
        print("=== BOT CRASH ===", flush=True)
        traceback.print_exc()

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()

    port = int(os.environ.get("PORT", "10000"))
    print(f"=== FLASK START on port {port} ===", flush=True)
    app.run(host="0.0.0.0", port=port)
