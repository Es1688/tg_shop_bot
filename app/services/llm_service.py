import openai
from app.config import config
import aiohttp
import json
from app.database.crud import ChatHistoryCRUD

class LLMService:
    def __init__(self):
        if not config.USE_OLLAMA and config.OPENAI_API_KEY:
            openai.api_key = config.OPENAI_API_KEY
    
    async def get_ai_response(self, user_id: int, user_message: str) -> str:
        # Сохраняем сообщение пользователя
        ChatHistoryCRUD.add_message(user_id, "user", user_message)
        
        # Получаем историю диалога
        history = ChatHistoryCRUD.get_recent_history(user_id)
        context = self._build_context(history)
        
        if config.USE_OLLAMA:
            response = await self._ollama_request(user_message, context)
        else:
            response = await self._openai_request(user_message, context)
        
        # Сохраняем ответ ассистента
        ChatHistoryCRUD.add_message(user_id, "assistant", response)
        
        return response
    
    def _build_context(self, history: list) -> str:
        context_messages = []
        for msg in reversed(history):  # Восстанавливаем хронологический порядок
            context_messages.append(f"{msg['role']}: {msg['message']}")
        return "\n".join(context_messages[-6:])  # Берем последние 6 сообщений
    
    async def _ollama_request(self, user_message: str, context: str) -> str:
        prompt = f"""
        Ты - консультант интернет-магазина электроники. 
        Отвечай вежливо, помогай выбрать товар, консультируй по характеристикам.
        Если вопрос не по теме магазина, вежливо откажись отвечать.
        
        Контекст предыдущего разговора:
        {context}
        
        Вопрос клиента: {user_message}
        """
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{config.OLLAMA_BASE_URL}/api/generate",
                    json={
                        "model": config.OLLAMA_MODEL,
                        "prompt": prompt,
                        "stream": False
                    }
                ) as response:
                    result = await response.json()
                    return result.get("response", "Извините, произошла ошибка.")
        except Exception as e:
            return f"Ошибка соединения с AI: {str(e)}"
    
    async def _openai_request(self, user_message: str, context: str) -> str:
        messages = [
            {
                "role": "system",
                "content": "Ты - консультант интернет-магазина электроники. Отвечай вежливо и помогай выбрать товар."
            }
        ]
        
        if context:
            messages.append({"role": "system", "content": f"Контекст: {context}"})
        
        messages.append({"role": "user", "content": user_message})
        
        try:
            response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=500
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Ошибка OpenAI: {str(e)}"

llm_service = LLMService()
