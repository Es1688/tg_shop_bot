import logging
from config import config
from database.crud import ChatHistoryCRUD
from services.yandex_gpt_service import yandex_gpt_service

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.use_yandex_gpt = config.USE_YANDEX_GPT
        self.use_ollama = config.USE_OLLAMA
        
        # Проверяем конфигурацию
        if self.use_yandex_gpt and not config.YANDEX_API_KEY:
            logger.warning("YANDEX_API_KEY not set, but USE_YANDEX_GPT is True")
    
    async def get_ai_response(self, user_id: int, user_message: str) -> str:
        """Получение ответа от выбранного AI провайдера"""
        
        if self.use_yandex_gpt and config.YANDEX_API_KEY:
            return await yandex_gpt_service.get_ai_response(user_id, user_message)
        elif self.use_ollama:
            return await self._ollama_request(user_id, user_message)
        else:
            return "Извините, сервис AI временно недоступен."
    
    async def _ollama_request(self, user_id: int, user_message: str) -> str:
        """Резервный вариант с Ollama (если нужен)"""
        # Сохраняем сообщение пользователя
        ChatHistoryCRUD.add_message(user_id, "user", user_message)
        
        try:
            # Простая заглушка - в реальности здесь будет запрос к Ollama
            response = "Это ответ от локальной модели Ollama. Для работы с Yandex GPT настройте YANDEX_API_KEY."
            
            # Сохраняем ответ
            ChatHistoryCRUD.add_message(user_id, "assistant", response)
            return response
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            return "Ошибка локального AI сервиса."

llm_service = LLMService()
