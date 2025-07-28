from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from bot.keyboards.inline import get_admin_menu, get_channel_keyboard
from bot.services.user import get_user_status, get_user_list, get_user_info
from bot.services.wallet import add_wallet, delete_wallet, get_user_wallets
from bot.utils.formatting import format_wallets
from config import load_config
import logging

router = Router()
logger = logging.getLogger(__name__)

class PaymentForm(StatesGroup):
    payment_data = State()

async def is_admin(user_id: int) -> bool:
    """Проверка прав администратора"""
    try:
        config = load_config()
        return user_id in config.admin_ids or await get_user_status(user_id) == "admin"
    except Exception as e:
        logger.error(f"Ошибка проверки прав администратора: {e}")
        return False

@router.message(F.text == "Admin Menu")
async def admin_menu(message: Message):
    """Отображение админ-меню"""
    try:
        if not await is_admin(message.from_user.id):
            await message.answer("Доступ только для администраторов.")
            return
        await message.answer("Админ-меню:", reply_markup=get_admin_menu())
    except Exception as e:
        logger.error(f"Ошибка в admin_menu: {e}")
        await message.answer("Произошла ошибка при отображении меню.")

@router.callback_query(F.data == "manage_users")
async def manage_users(callback: CallbackQuery):
    """Управление пользователями"""
    try:
        if not await is_admin(callback.from_user.id):
            await callback.answer("Доступ только для администраторов.")
            return
            
        users = await get_user_list()
        if not users:
            await callback.message.answer("Пользователи не найдены.")
            return
            

        for user in users[:5]:
            user_text = (
                f"CryptoBusinessTeam, []:\n"
                f"ID: {user['telegram_id']}\n"
                f"Username: @{user.get('username', 'Не указан')}\n"
                f"Status: {user['status']}\n"
                f"Referral: {user.get('referral', 'Нет')}\n"
                f"Registration date: {user['registration_date']}\n"
                f"Exchange statistics: {user['profit_total']}$"
            )
            await callback.message.answer(user_text)
            
        await callback.answer()
    except Exception as e:
        logger.error(f"Ошибка в manage_users: {e}")
        await callback.answer("Ошибка при получении списка пользователей.")

@router.callback_query(F.data == "admin_group")
async def admin_group(callback: CallbackQuery):
    """Отображение админ-группы"""
    try:
        if not await is_admin(callback.from_user.id):
            await callback.answer("Доступ только для администраторов.")
            return
            
        config = load_config()
        await callback.message.answer(
            f"Админ-группа: [{config.admin_group_url}]({config.admin_group_url})",
            reply_markup=get_channel_keyboard(config.admin_group_url),
            parse_mode="Markdown"
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Ошибка в admin_group: {e}")
        await callback.answer("Ошибка при отображении админ-группы.")

@router.callback_query(F.data == "post_payment")
async def post_payment(callback: CallbackQuery, state: FSMContext):
    """Публикация выплаты"""
    try:
        if not await is_admin(callback.from_user.id):
            await callback.answer("Доступ только для администраторов.")
            return
            
        await callback.message.answer(
            f"Введите данные для публикации выплаты:"
        )
        await state.set_state(PaymentForm.payment_data)
        await callback.answer()
    except Exception as e:
        logger.error(f"Ошибка в post_payment: {e}")
        await callback.answer("Ошибка при создании формы выплаты.")

@router.message(PaymentForm.payment_data)
async def process_payment_data(message: Message, state: FSMContext):
    """Обработка данных выплаты"""
    try:
        config = load_config()
        payment_text = (
            f"CryptoBusinessTeam,\n"
            f"Выплата опубликована!\n{message.text}"
        )
        
        await message.bot.send_message(config.payment_channel, payment_text)
        await message.answer("Выплата успешно опубликована!")
        await state.clear()
    except Exception as e:
        logger.error(f"Ошибка в process_payment_data: {e}")
        await message.answer("Ошибка при публикации выплаты.")
        await state.clear()

@router.callback_query(F.data == "manage_wallets")
async def manage_wallets(callback: CallbackQuery):
    """Управление кошельками"""
    try:
        if not await is_admin(callback.from_user.id):
            await callback.answer("Доступ только для администраторов.")
            return
            
        wallets = await get_user_wallets(callback.from_user.id)
        wallet_text = (
            f"{format_wallets(wallets)}"
        )
        
        await callback.message.answer(wallet_text, parse_mode="HTML")
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка в manage_wallets: {e}")
        await callback.answer("Ошибка при отображении кошельков.")