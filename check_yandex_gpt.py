#!/usr/bin/env python3
"""
Утилита для проверки подключения к Yandex GPT
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

async def test_yandex_gpt():
    """Тестирование подключения к Yandex GPT"""
    from app.services.yandex_gpt_service import YandexGPTService
    
    print("🔍 Тестирование подключения к Yandex GPT...")
    
    # Проверяем переменные окружения
    api_key = os.getenv('YANDEX_API_KEY')
    folder_id = os.getenv('YANDEX_FOLDER_ID')
    
    print(f"YANDEX_API_KEY: {'✅ Установлен' if api_key else '❌ Отсутствует'}")
    print(f"YANDEX_FOLDER_ID: {'✅ Установлен' if folder_id else '❌ Отсутствует'}")
    
    if not api_key or not folder_id:
        print("\n❌ Необходимо установить YANDEX_API_KEY и YANDEX_FOLDER_ID в .env файле")
        return False
    
    service = YandexGPTService()
    service.api_key = api_key
    service.folder_id = folder_id
    
    try:
        print("\n🧪 Отправка тестового запроса...")
        response = await service._yandex_gpt_request("Привет! Какие у вас есть смартфоны?", [])
        print(f"✅ Успех! Ответ: {response}")
        return True
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        
        # Дополнительная диагностика
        if "401" in str(e):
            print("\n🔒 Проблема с аутентификацией. Проверьте:")
            print("   - Корректность YANDEX_API_KEY")
            print("   - Активность API ключа")
        elif "403" in str(e):
            print("\n🚫 Проблема с правами доступа. Проверьте:")
            print("   - Корректность YANDEX_FOLDER_ID") 
            print("   - Назначены ли права на каталог")
            print("   - Активен ли сервис Yandex GPT в каталоге")
        elif "500" in str(e):
            print("\n⚡ Внутренняя ошибка сервера Yandex. Возможные причины:")
            print("   - Временные проблемы с сервисом Yandex GPT")
            print("   - Неправильный формат запроса")
            print("   - Проблемы с моделью")
        elif "timeout" in str(e).lower():
            print("\n⏰ Таймаут запроса. Проверьте:")
            print("   - Интернет-соединение")
            print("   - Блокировку firewall")
        
        return False

async def test_simple_request():
    """Простой тест напрямую через aiohttp"""
    import aiohttp
    import json
    
    api_key = os.getenv('YANDEX_API_KEY')
    folder_id = os.getenv('YANDEX_FOLDER_ID')
    
    if not api_key or not folder_id:
        return
    
    headers = {
        "Authorization": f"Api-Key {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "modelUri": f"gpt://{folder_id}/yandexgpt/latest",
        "completionOptions": {
            "stream": False,
            "temperature": 0.3,
            "maxTokens": 100
        },
        "messages": [
            {
                "role": "user",
                "text": "Привет! Ответь коротко: как дела?"
            }
        ]
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://llm.api.cloud.yandex.net/foundationModels/v1/completion",
                headers=headers,
                json=payload,
                timeout=10
            ) as response:
                text = await response.text()
                print(f"\n🔧 Прямой запрос - статус: {response.status}")
                if response.status == 200:
                    result = json.loads(text)
                    print(f"✅ Прямой запрос успешен: {result}")
                else:
                    print(f"❌ Прямой запрос ошибка: {text}")
    except Exception as e:
        print(f"❌ Ошибка прямого запроса: {e}")

if __name__ == "__main__":
    print("Yandex GPT Connectivity Checker")
    print("=" * 50)
    
    # Запускаем тесты
    success = asyncio.run(test_yandex_gpt())
    
    if not success:
        print("\n🔄 Пробуем упрощенный запрос...")
        asyncio.run(test_simple_request())
    
    print("\n📋 Рекомендации по устранению проблем:")
    print("1. Проверьте .env файл с переменными YANDEX_API_KEY и YANDEX_FOLDER_ID")
    print("2. Убедитесь, что API ключ активен и имеет права на каталог")
    print("3. Проверьте, активирован ли сервис Yandex GPT в каталоге")
    print("4. Проверьте баланс в Yandex Cloud")
    print("5. Попробуйте другой каталог или создайте новый API ключ")
