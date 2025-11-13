#!/usr/bin/env python3
"""
Комплексное тестирование бота
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

async def test_bot_functionality():
    """Тестирование основных функций бота"""
    from app.database.models import Database
    from app.database.crud import UserCRUD, OrderCRUD
    from app.services.llm_service import LLMService
    
    print("🧪 Комплексное тестирование бота...")
    
    # Тест базы данных
    print("1. Тестирование базы данных...")
    try:
        db = Database("test_bot.db")
        user = UserCRUD.get_or_create_user(123, "test_user", "Test", "User")
        assert user is not None
        print("   ✅ База данных работает")
        
        # Тест заказа
        order_id = OrderCRUD.create_order(123, [{"name": "Тестовый товар", "price": 1000}], 1000.0)
        assert order_id is not None
        print("   ✅ Система заказов работает")
        
    except Exception as e:
        print(f"   ❌ Ошибка базы данных: {e}")
        return False
    
    # Тест LLM сервиса
    print("2. Тестирование LLM сервиса...")
    try:
        llm_service = LLMService()
        response = await llm_service.get_ai_response(123, "Привет! Какие у вас есть смартфоны?")
        print(f"   ✅ LLM сервис работает. Ответ: {response[:100]}...")
    except Exception as e:
        print(f"   ❌ Ошибка LLM сервиса: {e}")
        return False
    
    # Тест конфигурации
    print("3. Проверка конфигурации...")
    from app.config import config
    if config.BOT_TOKEN and config.BOT_TOKEN != "your_bot_token_here":
        print("   ✅ Токен бота настроен")
    else:
        print("   ❌ Токен бота не настроен")
        return False
    
    if config.YANDEX_API_KEY and config.YANDEX_FOLDER_ID:
        print("   ✅ Yandex GPT настроен")
    else:
        print("   ⚠️  Yandex GPT не настроен, будут использоваться локальные ответы")
    
    print("\n🎉 Все системы работают! Бот готов к запуску.")
    return True

if __name__ == "__main__":
    success = asyncio.run(test_bot_functionality())
    
    if success:
        print("\n🚀 Запуск бота...")
        print("Для остановки нажмите Ctrl+C")
        
        # Можно автоматически запустить бота
        import subprocess
        try:
            subprocess.run([sys.executable, "-m", "app.main"])
        except KeyboardInterrupt:
            print("\n👋 Бот остановлен")
    else:
        print("\n❌ Есть проблемы с настройкой. Проверьте конфигурацию.")
        sys.exit(1)
