import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties

from config import config
from database.crud import UserCRUD, OrderCRUD
from services.llm_service import llm_service

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота
bot = Bot(token=config.BOT_TOKEN, default=DefaultBotProperties(parse_mode='HTML'))
dp = Dispatcher()

# Клавиатуры
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛍️ Консультация по товарам"), KeyboardButton(text="📦 Сделать заказ")],
            [KeyboardButton(text="❓ Частые вопросы"), KeyboardButton(text="📞 Контакты")]
        ],
        resize_keyboard=True
    )

# Обработчики
@dp.message(Command("start"))
async def start_command(message: types.Message):
    user = message.from_user
    UserCRUD.get_or_create_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )
    
    welcome_text = f"""
👋 Добро пожаловать, {user.first_name}!

Я - умный помощник интернет-магазина электроники. Чем могу помочь?

• 🛍️ Консультация по товарам
• 📦 Оформление заказов
• ❓ Ответы на вопросы
• 📞 Контактная информация
    """
    
    await message.answer(welcome_text, reply_markup=get_main_keyboard())

@dp.message(F.text == "🛍️ Консультация по товарам")
async def consultation_handler(message: types.Message):
    await message.answer(
        "Расскажите, какой товар вас интересует? "
        "Я помогу с выбором и отвечу на вопросы!",
        reply_markup=types.ReplyKeyboardRemove()
    )

@dp.message(F.text == "❓ Частые вопросы")
async def faq_handler(message: types.Message):
    faq_text = """
🤔 Частые вопросы:

• <b>Доставка</b> - 1-3 дня по городу, 3-7 дней по стране
• <b>Оплата</b> - наличные, карта, онлайн
• <b>Гарантия</b> - от 1 года на всю технику
• <b>Возврат</b> - в течение 14 дней

Что вас интересует?
    """
    await message.answer(faq_text, reply_markup=get_main_keyboard())

@dp.message(F.text == "📞 Контакты")
async def contacts_handler(message: types.Message):
    contacts_text = """
📞 Наши контакты:

• Телефон: +7 (999) 123-45-67
• Email: shop@example.com
• Адрес: г. Москва, ул. Примерная, 123
• График: Пн-Пт 9:00-18:00
    """
    await message.answer(contacts_text, reply_markup=get_main_keyboard())

@dp.message(F.text == "📦 Сделать заказ")
async def order_handler(message: types.Message):
    await message.answer(
        "Для оформления заказа напишите, что вы хотите заказать. "
        "Я помогу оформить заказ!",
        reply_markup=types.ReplyKeyboardRemove()
    )

@dp.message()
async def handle_all_messages(message: types.Message):
    user_id = message.from_user.id
    
    # Создаем/обновляем пользователя
    UserCRUD.get_or_create_user(
        user_id=user_id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name
    )
    
    # Показываем индикатор набора
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")
    
    try:
        # Получаем ответ от AI
        response = await llm_service.get_ai_response(user_id, message.text)
        await message.answer(response, reply_markup=get_main_keyboard())
        
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        await message.answer(
            "Извините, произошла ошибка. Попробуйте позже.",
            reply_markup=get_main_keyboard()
        )

async def main():
    logger.info("Starting bot...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
