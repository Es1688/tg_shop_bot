import aiohttp
import json
import logging
from app.config import config
from app.database.crud import ChatHistoryCRUD

logger = logging.getLogger(__name__)

class YandexGPTService:
    def __init__(self):
        self.api_key = config.YANDEX_API_KEY
        self.folder_id = config.YANDEX_FOLDER_ID
        self.base_url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    
    async def get_ai_response(self, user_id: int, user_message: str) -> str:
        """Получение ответа от Yandex GPT"""
        try:
            # Сохраняем сообщение пользователя
            ChatHistoryCRUD.add_message(user_id, "user", user_message)
            
            # Получаем историю диалога
            history = ChatHistoryCRUD.get_recent_history(user_id)
            
            response = await self._yandex_gpt_request(user_message, history)
            
            # Сохраняем ответ ассистента
            ChatHistoryCRUD.add_message(user_id, "assistant", response)
            
            return response
        except Exception as e:
            logger.error(f"Yandex GPT service error: {e}")
            error_msg = self._get_fallback_response(user_message)
            ChatHistoryCRUD.add_message(user_id, "assistant", error_msg)
            return error_msg
    
    async def _yandex_gpt_request(self, user_message: str, history: list) -> str:
        """Запрос к Yandex GPT API с улучшенной обработкой ошибок"""
        # Проверяем наличие обязательных параметров
        if not self.api_key or not self.folder_id:
            raise Exception("Yandex API key or folder ID not configured")
        
        headers = {
            "Authorization": f"Api-Key {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Формируем системный промпт
        system_prompt = """Ты - консультант интернет-магазина электроники. 
Отвечай вежливо и помогай клиентам с выбором товаров.
Отвечай на русском языке."""
        
        # Формируем messages для API (упрощенная версия)
        messages = [{"role": "system", "text": system_prompt}]
        
        # Добавляем историю (ограниченную)
        if history:
            # Берем только последние 4 сообщения для надежности
            recent_history = history[-4:]
            for msg in recent_history:
                role = "assistant" if msg['role'] == 'assistant' else 'user'
                messages.append({
                    "role": role,
                    "text": msg['message'][:500]  # Ограничиваем длину сообщения
                })
        
        # Добавляем текущее сообщение пользователя
        messages.append({
            "role": "user", 
            "text": user_message[:1000]  # Ограничиваем длину
        })
        
        payload = {
            "modelUri": f"gpt://{self.folder_id}/yandexgpt/latest",
            "completionOptions": {
                "stream": False,
                "temperature": 0.3,
                "maxTokens": 500  # Уменьшаем количество токенов
            },
            "messages": messages
        }
        
        logger.info(f"Sending request to Yandex GPT with {len(messages)} messages")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.base_url,
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=15)  # Уменьшаем таймаут
                ) as response:
                    response_text = await response.text()
                    
                    if response.status == 200:
                        result = json.loads(response_text)
                        return result["result"]["alternatives"][0]["message"]["text"]
                    else:
                        logger.error(f"Yandex GPT API error {response.status}: {response_text}")
                        
                        # Анализируем ошибку
                        if response.status == 500:
                            raise Exception("Internal server error from Yandex GPT - possible model issues")
                        elif response.status == 400:
                            raise Exception(f"Bad request: {response_text}")
                        elif response.status == 401:
                            raise Exception("Unauthorized - check API key")
                        elif response.status == 403:
                            raise Exception("Forbidden - check folder ID and permissions")
                        else:
                            raise Exception(f"HTTP {response.status}: {response_text}")
                            
        except asyncio.TimeoutError:
            logger.error("Yandex GPT request timeout")
            raise Exception("Request timeout - service may be overloaded")
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            raise Exception("Invalid response format from Yandex GPT")
    
    def _get_fallback_response(self, user_message: str) -> str:
        """Резервные ответы при недоступности Yandex GPT"""
        user_message_lower = user_message.lower()
        
        if any(word in user_message_lower for word in ['привет', 'здравствуй', 'hello']):
            return "Здравствуйте! Чем могу помочь с выбором электроники?"
        elif any(word in user_message_lower for word in ['телефон', 'смартфон']):
            return "У нас есть широкий выбор смартфонов. Какие характеристики вас интересуют: бюджет, камера, производитель?"
        elif any(word in user_message_lower for word in ['ноутбук', 'компьютер']):
            return "Для подбора ноутбука важно знать: для каких задач (работа, игры, учеба), бюджет и предпочитаемый размер экрана."
        elif any(word in user_message_lower for word in ['доставка', 'доставить']):
            return "Доставка осуществляется в течение 1-3 дней по городу. Есть самовывоз."
        elif any(word in user_message_lower for word in ['оплата', 'заплатить']):
            return "Принимаем оплату картой, наличными и онлайн. Есть рассрочка."
        elif any(word in user_message_lower for word in ['гарантия', 'возврат']):
            return "Гарантия на технику от 1 года. Возврат в течение 14 дней."
        else:
            return "Извините, в данный момент сервис консультаций временно недоступен. Вы можете задать вопрос по телефону +7 (999) 123-45-67 или написать на shop@example.com"

yandex_gpt_service = YandexGPTService()
