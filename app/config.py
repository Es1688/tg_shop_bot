import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Config:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN")
    YANDEX_API_KEY: str = os.getenv("YANDEX_API_KEY", "")
    YANDEX_FOLDER_ID: str = os.getenv("YANDEX_FOLDER_ID", "")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "shop_bot.db")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Флаги для выбора провайдера AI
    USE_YANDEX_GPT: bool = os.getenv("USE_YANDEX_GPT", "True").lower() == "true"
    USE_OLLAMA: bool = os.getenv("USE_OLLAMA", "False").lower() == "true"

config = Config()
