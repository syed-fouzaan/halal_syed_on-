import asyncio
import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.telegram.bot import TelegramAgent

def main():
    print("=" * 60)
    print("Starting Halal SIP AI Telegram Bot...")
    print("=" * 60)
    
    agent = TelegramAgent()
    asyncio.run(agent.start_polling())

if __name__ == "__main__":
    main()
