import os
from flask import Flask
from bot import run_bot

app = Flask(__name__)

@app.get("/")
def home():
    return "OK", 200

run_bot()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
