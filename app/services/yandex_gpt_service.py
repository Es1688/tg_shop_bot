import aiohttp
import json
import logging
from config import config
from database.crud import ChatHistoryCRUD

logger = logging.getLogger(__name__)

class YandexGPTService:
    def __init__(self):
        self.api_key = config.YANDEX_API_KEY
        self.folder_id = config.YANDEX_FOLDER_ID
        self.base_url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    
    async def get_ai_response(self, user_id: int, user_message: str) -> str:
        """Получение ответа от Yandex GPT"""
        # Сохраняем сообщение пользователя
        ChatHistoryCRUD.add_message(user_id, "user", user_message)
        
        # Получаем историю диалога
        history = ChatHistoryCRUD.get_recent_history(user_id)
        
        try:
            response = await self._yandex_gpt_request(user_message, history)
            
            # Сохраняем ответ ассистента
            ChatHistoryCRUD.add_message(user_id, "assistant", response)
            
            return response
        except Exception as e:
            logger.error(f"Yandex GPT error: {e}")
            error_msg = "Извините, произошла ошибка при обработке запроса. Попробуйте позже."
            ChatHistoryCRUD.add_message(user_id, "assistant", error_msg)
            return error_msg
    
    async def _yandex_gpt_request(self, user_message: str, history: list) -> str:
        """Запрос к Yandex GPT API"""
        headers = {
            "Authorization": f"Api-Key {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Формируем системный промпт
        system_prompt = """Ты - консультант интернет-магазина электроники. 
Твоя задача - вежливо и профессионально помогать клиентам:
- Консультировать по товарам и их характеристикам
- Помогать с выбором подходящей техники
- Отвечать на вопросы о доставке, оплате, гарантии
- При необходимости уточнять детали для лучшей помощи

Отвечай на русском языке, будь дружелюбным и полезным.
Если вопрос не по теме магазина, вежливо сообщи об этом."""
        
        # Формируем messages для API
        messages = [
            {
                "role": "system",
                "text": system_prompt
            }
        ]
        
        # Добавляем историю диалога если она есть
        if history:
            history_messages = self._parse_history_to_messages(history)
            messages.extend(history_messages)
        
        # Добавляем текущее сообщение пользователя
        messages.append({
            "role": "user", 
            "text": user_message
        })
        
        payload = {
            "modelUri": f"gpt://{self.folder_id}/yandexgpt-latest",
            "completionOptions": {
                "stream": False,
                "temperature": 0.3,
                "maxTokens": 1000
            },
            "messages": messages
        }
        
        logger.debug(f"Yandex GPT request payload: {json.dumps(payload, ensure_ascii=False)}")
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result["result"]["alternatives"][0]["message"]["text"]
                else:
                    error_text = await response.text()
                    logger.error(f"Yandex GPT API error: {response.status} - {error_text}")
                    raise Exception(f"API error: {response.status}")
    
    def _parse_history_to_messages(self, history: list) -> list:
        """Преобразует историю в формат сообщений для Yandex GPT"""
        messages = []
        # Берем последние 6 сообщений для ограничения контекста
        for msg in reversed(history[-6:]):
            role = "assistant" if msg['role'] == 'assistant' else 'user'
            messages.append({
                "role": role,
                "text": msg['message']
            })
        return messages

yandex_gpt_service = YandexGPTService()
