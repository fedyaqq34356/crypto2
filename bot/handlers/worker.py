from aiogram import Router, F
from aiogram.types import Message, FSInputFile
from aiogram.fsm.context import FSMContext
from bot.keyboards.reply import get_worker_menu
from bot.keyboards.inline import get_channel_keyboard, get_invite_keyboard
from bot.services.user import get_user_status, get_user_stats
from bot.services.wallet import get_user_wallets
from bot.services.stats import get_top_week
from bot.services.referral import generate_invite_link
from bot.utils.formatting import format_stats, format_wallets, format_top_week
from config import load_config
import logging
import os

router = Router()
logger = logging.getLogger(__name__)

async def check_user_access(user_id: int) -> bool:
    """Проверка доступа пользователя"""
    try:
        return await get_user_status(user_id) == "active"
    except Exception as e:
        logger.error(f"Ошибка проверки доступа: {e}")
        return False

async def send_wallets_with_image(message: Message, wallets_text: str, reply_markup=None):
    """Отправка сообщения с кошельками и изображением"""
    possible_paths = [
        "images/wallets.jpg",
        "assets/wallets.jpg", 
        "wallets.jpg",
        "bot/images/wallets.jpg",
        "static/wallets.jpg"
    ]
    
    image_found = False
    
    for image_path in possible_paths:
        if os.path.exists(image_path):
            try:
                photo = FSInputFile(image_path)
                await message.answer_photo(
                    photo=photo,
                    caption=wallets_text,
                    reply_markup=reply_markup,
                    parse_mode="HTML"
                )
                image_found = True
                logger.info(f"Кошельки отправлены с изображением: {image_path}")
                break
            except Exception as e:
                logger.error(f"Ошибка при отправке изображения {image_path}: {e}")
                continue
    
    if not image_found:
        logger.warning("Изображение wallets.jpg не найдено, отправляем только текст")
        await message.answer(
            wallets_text,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )

@router.message(F.text == "Моя статистика")
async def show_stats(message: Message):
    """Отображение статистики пользователя"""
    try:
        if not await check_user_access(message.from_user.id):
            await message.answer("Только одобренные пользователи имеют доступ к статистике.")
            return
            
        stats = await get_user_stats(message.from_user.id)
        stats_text = (
            f"{format_stats(stats)}"
        )
        
        await message.answer(
            stats_text,
            reply_markup=get_worker_menu(),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Ошибка в show_stats: {e}")
        await message.answer("Ошибка при получении статистики.")

@router.message(F.text == "Топ недели")
async def show_top_week(message: Message):
    """Отображение топа недели"""
    try:
        if not await check_user_access(message.from_user.id):
            await message.answer("Только одобренные пользователи имеют доступ к топу.")
            return
            
        top = await get_top_week()
        config = load_config()
        
        top_text = (
            f"{format_top_week(top)}"
        )
        
        await message.answer(
            top_text,
            reply_markup=get_channel_keyboard(config.payment_channel_url),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Ошибка в show_top_week: {e}")
        await message.answer("Ошибка при получении топа недели.")

@router.message(F.text == "Сгенерировать ключи")
async def generate_wallets(message: Message):
    """Генерация кошельков"""
    try:
        if not await check_user_access(message.from_user.id):
            await message.answer("Только одобренные пользователи могут генерировать ключи.")
            return
            
        wallets = await get_user_wallets(message.from_user.id)
        wallets_text = (
            f"{format_wallets(wallets)}"
        )
        
        await send_wallets_with_image(message, wallets_text, get_worker_menu())
    except Exception as e:
        logger.error(f"Ошибка в generate_wallets: {e}")
        await message.answer("Ошибка при генерации кошельков.")

@router.message(F.text == "Выплаты")
async def show_payments(message: Message):
    """Отображение информации о выплатах"""
    try:
        if not await check_user_access(message.from_user.id):
            await message.answer("Только одобренные пользователи имеют доступ к выплатам.")
            return
            
        config = load_config()
        payments_text = (
            f"История профитов публикуется в [{config.payment_channel_url}]({config.payment_channel_url}).\n"
            f"Статистика за неделю\n"
            f"Топ воркеров: /topweek\n"
            f"Топ команд: /topweekteam"
        )
        
        await message.answer(
            payments_text,
            reply_markup=get_channel_keyboard(config.payment_channel_url),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Ошибка в show_payments: {e}")
        await message.answer("Ошибка при получении информации о выплатах.")

@router.message(F.text == "Канал")
async def show_channel(message: Message):
    """Отображение информации о каналах"""
    try:
        if not await check_user_access(message.from_user.id):
            await message.answer("Только одобренные пользователи имеют доступ к каналам.")
            return
            
        config = load_config()
        channel_text = (
            f"Подпишись на [{config.main_channel}]({config.main_channel}), "
            f"чтобы быть в курсе всех обновлений и новостей проекта.\n"
            f"На случай очередного удаления канала, "
            f"резервным будет [{config.payment_channel_url}]({config.payment_channel_url})."
        )
        
        await message.answer(
            channel_text,
            reply_markup=get_channel_keyboard(config.main_channel),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Ошибка в show_channel: {e}")
        await message.answer("Ошибка при получении информации о каналах.")

@router.message(F.text == "Инвайт")
async def show_invite(message: Message):
    """Генерация и отображение инвайт-ссылки"""
    try:
        if not await check_user_access(message.from_user.id):
            await message.answer("Только одобренные пользователи могут генерировать инвайт-ссылки.")
            return
            
        invite_link = await generate_invite_link(message.from_user.username)
        invite_text = (
            f"Твоя пригласительная ссылка\n"
            f"[{invite_link}]({invite_link})\n"
            f"```Нажми для перехода```"
        )
        
        await message.answer(
            invite_text,
            reply_markup=get_invite_keyboard(invite_link),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Ошибка в show_invite: {e}")
        await message.answer("Ошибка при генерации инвайт-ссылки.")


@router.message(F.text == "UTM ссылка")
async def generate_user_utm(message: Message):
    """Генерация UTM ссылки пользователем"""
    try:
        if not await check_user_access(message.from_user.id):
            await message.answer("Только одобренные пользователи могут генерировать UTM ссылки.")
            return
        
        # Получаем привязанного админа пользователя
        from bot.services.user import get_user_assigned_admin, get_admin_username
        assigned_admin = await get_user_assigned_admin(message.from_user.id)
        
        if not assigned_admin:
            await message.answer("Ошибка: к вам не привязан администратор.")
            return
        
        # Создаем уникальный UTM код для пользователя
        user_utm = f"user_{message.from_user.id}"
        
        bot_username = (await message.bot.get_me()).username
        utm_link = f"https://t.me/{bot_username}?start={user_utm}"
        
        admin_username = await get_admin_username(assigned_admin)
        
        utm_text = (
            f"🔗 Ваша UTM ссылка для друзей:\n\n"
            f"`{utm_link}`\n\n"
            f"📝 Все ваши друзья, перешедшие по этой ссылке, "
            f"будут привязаны к вашему админу @{admin_username} "
            f"и вы получите бонус с их профита."
        )
        
        await message.answer(utm_text, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Ошибка генерации UTM пользователем: {e}")
        await message.answer("Ошибка при генерации ссылки.")

@router.message(F.text == "Команды")
async def show_commands(message: Message):
    """Отображение доступных команд"""
    try:
        if not await check_user_access(message.from_user.id):
            await message.answer("Только одобренные пользователи имеют доступ к командам.")
            return
            
        commands_text = (
            f"Доступные команды:\n"
            f"/start - Перезапустить бота\n"
            f"/topweek - Топ воркеров недели\n"
            f"/topweekteam - Топ команд недели"
        )
        
        await message.answer(
            commands_text,
            reply_markup=get_worker_menu()
        )
    except Exception as e:
        logger.error(f"Ошибка в show_commands: {e}")
        await message.answer("Ошибка при получении списка команд.")

@router.message(F.text == "Мои кошельки")
async def show_wallets(message: Message):
    """Отображение кошельков пользователя"""
    try:
        if not await check_user_access(message.from_user.id):
            await message.answer("Только одобренные пользователи имеют доступ к кошелькам.")
            return
            
        wallets = await get_user_wallets(message.from_user.id)
        wallets_text = (
            f"{format_wallets(wallets)}"
        )
        
        await send_wallets_with_image(message, wallets_text, get_worker_menu())
    except Exception as e:
        logger.error(f"Ошибка в show_wallets: {e}")
        await message.answer("Ошибка при получении кошельков.")

@router.message(F.text == "Place Order")
async def place_order_redirect(message: Message, state: FSMContext):
    """Перенаправление на создание заказа"""
    try:
        if not await check_user_access(message.from_user.id):
            await message.answer("Только одобренные пользователи могут размещать заказы.")
            return
            

        from bot.handlers.exchange import start_exchange
        await start_exchange(message, state)
    except Exception as e:
        logger.error(f"Ошибка в place_order_redirect: {e}")
        await message.answer("Ошибка при создании заказа.")
