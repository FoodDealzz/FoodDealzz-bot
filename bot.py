import asyncio
from telegram import Bot

TOKEN = "8575424045:AAHcZpBH0z5_F5JKYOQA2rQ-LcKLlj60eak"

async def main():
    bot = Bot(token=TOKEN)
    print("Bot lancé 🔥")
    while True:
        await asyncio.sleep(60)
