from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, FSInputFile
from bot.keyboards.inline import get_start_keyboard
from bot.keyboards.reply import get_worker_menu, get_admin_menu
from bot.services.user import get_user_status 
from bot.utils.formatting import format_rules
from config import load_config
from bot.services.user import save_utm_assignment
import os
import logging

router = Router()
logger = logging.getLogger(__name__)

async def send_welcome_image_with_text(message: Message, text: str, reply_markup=None):
    """Отправляет изображение с текстом"""
    possible_paths = [
        "images/welcome.jpg",
        "assets/welcome.jpg", 
        "welcome.jpg",
        "bot/images/welcome.jpg",
        "static/welcome.jpg"
    ]
    
    image_found = False
    
    for image_path in possible_paths:
        if os.path.exists(image_path):
            try:
                photo = FSInputFile(image_path)
                await message.answer_photo(
                    photo=photo,
                    caption=text,
                    reply_markup=reply_markup,
                    parse_mode="Markdown"
                )
                image_found = True
                logger.info(f"Изображение отправлено: {image_path}")
                break
            except Exception as e:
                logger.error(f"Ошибка при отправке изображения {image_path}: {e}")
                continue
    
    if not image_found:
        logger.warning("Изображение не найдено, отправляем только текст")
        await message.answer(
            text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

@router.message(CommandStart(deep_link=True))
async def cmd_start_deeplink(message: Message):
    """Обработка команды /start с UTM параметром"""
    try:
        config = load_config()
        
        # Проверяем, является ли пользователь админом
        if message.from_user.id in config.admin_ids:
            await message.answer(
                "Добро пожаловать, администратор!",
                reply_markup=get_admin_menu()
            )
            return

        # Извлекаем UTM параметр
        args = message.text.split()
        if len(args) < 2:
            await message.answer("Доступ к боту только по UTM ссылке.")
            return
            
        utm_param = args[1]
        status = await get_user_status(message.from_user.id)
        
        if status == "active":
            await message.answer(
                f"Добро пожаловать! Меню бота доступно по клавиатуре.",
                reply_markup=get_worker_menu()
            )
            return
        elif status == "pending":
            await message.answer("Ваша заявка на рассмотрении. Ожидайте одобрения.")
            return
        elif status == "banned":
            await message.answer("Ваш аккаунт заблокирован.")
            return

        # Сохраняем UTM источник и привязываем к админу
        await save_utm_assignment(message.from_user.id, utm_param)

        # Показываем правила и кнопку подачи заявки
        rules_text = format_rules()
        welcome_text = (
            "ДОБРО ПОЖАЛОВАТЬ!\n\n"
            "Ты находишься в нужном месте и в нужное время. Ознакомься с правилами проекта прежде, чем подать заявку.\n\n"
            f"{rules_text}\n\n"
            "Нажимая **Подать заявку**, ты подтверждаешь своё согласие с правилами."
        )
        
        await send_welcome_image_with_text(
            message,
            welcome_text,
            get_start_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Ошибка в cmd_start_deeplink: {e}")
        await message.answer("Произошла ошибка. Попробуйте позже.")

@router.message(CommandStart())
async def cmd_start_no_utm(message: Message):
    """Обработка команды /start без UTM"""
    try:
        config = load_config()
        
        # Проверяем, является ли пользователь админом
        if message.from_user.id in config.admin_ids:
            await message.answer(
                "Добро пожаловать, администратор!",
                reply_markup=get_admin_menu()
            )
            return
            
        # Если UTM обязателен, блокируем доступ
        if config.require_utm:
            await message.answer(
                "❌ Доступ к боту только по специальной ссылке от администратора.\n"
                "Обратитесь к своему тимлиду за корректной ссылкой."
            )
            return
        
        # Остальная логика для не-админов без UTM
        status = await get_user_status(message.from_user.id)
        
        if status == "active":
            await message.answer(
                f"Добро пожаловать! Меню бота доступно по клавиатуре.",
                reply_markup=get_worker_menu()
            )
            return
        elif status == "pending":
            await message.answer("Ваша заявка на рассмотрении. Ожидайте одобрения.")
            return
        elif status == "banned":
            await message.answer("Ваш аккаунт заблокирован.")
            return

        # Новый пользователь - показываем правила и кнопку подачи заявки
        rules_text = format_rules()
        welcome_text = (
            "ДОБРО ПОЖАЛОВАТЬ!\n\n"
            "Ты находишься в нужном месте и в нужное время. Ознакомься с правилами проекта прежде, чем подать заявку.\n\n"
            f"{rules_text}\n\n"
            "Нажимая **Подать заявку**, ты подтверждаешь своё согласие с правилами."
        )
        
        await send_welcome_image_with_text(
            message,
            welcome_text,
            get_start_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Ошибка в cmd_start_no_utm: {e}")
        await message.answer("Произошла ошибка. Попробуйте позже.")

# Удаляем дублирующий обработчик
# @router.message(CommandStart())
# async def cmd_start(message: Message):
#     ...
