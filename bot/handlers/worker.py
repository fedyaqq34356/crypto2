from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from bot.keyboards.reply import get_worker_menu
from bot.keyboards.inline import get_channel_keyboard
from bot.services.user import get_user_status, get_user_stats, get_user_assigned_admin, get_admin_username
from bot.models.database import init_db, Payment
from bot.utils.formatting import format_stats
from config import load_config
from sqlalchemy.sql import func
from sqlalchemy import desc
import logging
import random
import string

router = Router()
logger = logging.getLogger(__name__)

router = Router()
logger = logging.getLogger(__name__)

async def check_user_access(user_id: int) -> bool:
    """Проверка доступа пользователя"""
    try:
        return await get_user_status(user_id) == "active"
    except Exception as e:
        logger.error(f"Ошибка проверки доступа: {e}")
        return False



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
    """Отображение топа недели на основе реальных выплат"""
    try:
        if not await check_user_access(message.from_user.id):
            await message.answer("Только одобренные пользователи имеют доступ к топу.")
            return
            
        config = load_config()
        Session = await init_db(config)
        with Session() as session:
            # Получаем топ менеджеров по выплатам за неделю
            from datetime import datetime, timedelta
            week_ago = datetime.utcnow() - timedelta(days=7)
            
            top_managers = session.query(
                Payment.manager_name,
                func.sum(Payment.manager_profit).label('total_profit'),
                func.count(Payment.id).label('payment_count')
            ).filter(
                Payment.created_at >= week_ago
            ).group_by(Payment.manager_name).order_by(desc('total_profit')).limit(10).all()

        if not top_managers:
            await message.answer("Топ недели пуст.\nЕще нет выплат за текущую неделю.")
            return

        top_text = "🏆 Топ недели по менеджерам:\n\n"
        for i, (manager_name, total_profit, count) in enumerate(top_managers, 1):
            top_text += f"{i}. **{manager_name}**: {total_profit}$ | профитов: {count}\n"

        await message.answer(top_text, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Ошибка в show_top_week: {e}")
        await message.answer("Ошибка при получении топа недели.")



@router.message(F.text == "Выплаты")
async def show_payments(message: Message):
    """Отображение информации о выплатах"""
    try:
        if not await check_user_access(message.from_user.id):
            await message.answer("Только одобренные пользователи имеют доступ к выплатам.")
            return
            
        config = load_config()
        payments_text = (
            f"💰 История профитов публикуется в канале выплат.\n\n"
            f"📊 Для просмотра топа недели используйте кнопку 'Топ недели'"
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



@router.message(F.text == "Сгенерировать инвайт")
async def generate_user_utm(message: Message):
    """Генерация UTM ссылки для пользователя"""
    try:
        if not await check_user_access(message.from_user.id):
            await message.answer("Только одобренные пользователи могут генерировать инвайт-ссылки.")
            return
        
        assigned_admin = await get_user_assigned_admin(message.from_user.id)
        if not assigned_admin:
            await message.answer("Ошибка: к вам не привязан администратор.")
            return
        
        # Генерируем случайный UTM код из 12 символов
        utm_code = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
        
        # Сохраняем маппинг UTM к админу (не к пользователю!)
        config = load_config()
        config.utm_admin_mapping[utm_code] = assigned_admin
        
        bot_username = (await message.bot.get_me()).username
        utm_link = f"https://t.me/{bot_username}?start={utm_code}"
        
        admin_username = await get_admin_username(assigned_admin)
        utm_text = (
            f"🔗 Ваша инвайт-ссылка:\n\n"
            f"`{utm_link}`\n\n"
            f"📝 Новые пользователи будут привязаны к админу @{admin_username}."
        )
        
        await message.answer(utm_text, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Ошибка генерации UTM пользователем: {e}")
        await message.answer("Ошибка при генерации ссылки.")




@router.message(F.text == "Обменник")
async def exchange_redirect(message: Message, state: FSMContext):
    """Перенаправление на создание обмена"""
    try:
        if not await check_user_access(message.from_user.id):
            await message.answer("Только одобренные пользователи могут использовать обменник.")
            return
            
        from bot.handlers.exchange import start_exchange
        await start_exchange(message, state)
    except Exception as e:
        logger.error(f"Ошибка в exchange_redirect: {e}")
        await message.answer("Ошибка при создании обмена.")


@router.message(F.text == "Мануалы")
async def show_manuals(message: Message):
    """Отображение мануалов"""
    try:
        if not await check_user_access(message.from_user.id):
            await message.answer("Только одобренные пользователи имеют доступ к мануалам.")
            return
            
        config = load_config()
        assigned_admin = await get_user_assigned_admin(message.from_user.id)
        admin_username = await get_admin_username(assigned_admin) if assigned_admin else "админ"
        
        manuals_text = (
            f"Основная инфа по нашему направлению:\n\n"
            f"Чем занимаемся:\n"
            f"[Мануал по Electrum (Для ПК)]({config.electrum_manual})\n"
            f"[Мануал Bluewallet (Android/iOS)]({config.bluewallet_manual})\n"
            f"[Инструкция для менеджера]({config.manager_manual})\n\n"
            f"Если ты изучил мануалы и освоил отмену транзакций между своими кошельками - значит, ты готов к практике\n\n"
            f"Пиши @{admin_username}, чтобы:\n"
            f"• получить аккаунт телеги\n"
            f"• настроить трафик\n"
            f"• пройти обучение и начать ворк"
        )
        
        await message.answer(manuals_text, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Ошибка в show_manuals: {e}")
        await message.answer("Ошибка при получении мануалов.")
