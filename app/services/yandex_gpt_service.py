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
        context = self._build_context(history)
        
        try:
            response = await self._yandex_gpt_request(user_message, context)
            
            # Сохраняем ответ ассистента
            ChatHistoryCRUD.add_message(user_id, "assistant", response)
            
            return response
        except Exception as e:
            logger.error(f"Yandex GPT error: {e}")
            error_msg = "Извините, произошла ошибка при обработке запроса. Попробуйте позже."
            ChatHistoryCRUD.add_message(user_id, "assistant", error_msg)
            return error_msg
    
    def _build_context(self, history: list) -> str:
        """Строим контекст из истории диалога"""
        context_messages = []
        for msg in reversed(history[-6:]):  # Берем последние 6 сообщений
            role = "Пользователь" if msg['role'] == 'user' else "Консультант"
            context_messages.append(f"{role}: {msg['message']}")
        return "\n".join(context_messages)
    
    async def _yandex_gpt_request(self, user_message: str, context: str) -> str:
        """Запрос к Yandex GPT API"""
        headers = {
            "Authorization": f"Api-Key {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Формируем промпт с учетом контекста
        system_prompt = """Ты - консультант интернет-магазина электроники. 
Твоя задача - вежливо и профессионально помогать клиентам:
- Консультировать по товарам и их характеристикам
- Помогать с выбором подходящей техники
- Отвечать на вопросы о доставке, оплате, гарантии
- При необходимости уточнять детали для лучшей помощи

Отвечай на русском языке, будь дружелюбным и полезным.
Если вопрос не по теме магазина, вежливо сообщи об этом."""
        
        full_prompt = system_prompt
        if context:
            full_prompt += f"\n\nКонтекст предыдущего разговора:\n{context}"
        
        full_prompt += f"\n\nВопрос клиента: {user_message}"
        
        payload = {
            "modelUri": f"gpt://{self.folder_id}/yandexgpt-latest",
            "completionOptions": {
                "stream": False,
                "temperature": 0.3,  # Более консервативные ответы
                "maxTokens": 1000
            },
            "messages": [
                {
                    "role": "system",
                    "text": system_prompt
                },
                {
                    "role": "user", 
                    "text": user_message
                }
            ]
        }
        
        # Добавляем контекст в сообщения если он есть
        if context:
            # Парсим историю и добавляем в messages
            history_messages = self._parse_history_to_messages(history)
            payload["messages"] = history_messages + [{"role": "user", "text": user_message}]
        
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
        for msg in reversed(history[-8:]):  # Ограничиваем историю
            role = "assistant" if msg['role'] == 'assistant' else 'user'
            messages.append({
                "role": role,
                "text": msg['message']
            })
        return messages

yandex_gpt_service = YandexGPTService()
