from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from bot.keyboards.inline import get_admin_menu, get_channel_keyboard
from bot.services.user import get_user_status, get_user_list, get_user_info, update_user_status
from bot.services.stats import get_admin_workers_stats
from bot.models.database import init_db, User, Payment
from config import load_config
from datetime import datetime
import logging
from sqlalchemy.sql import func

router = Router()
logger = logging.getLogger(__name__)

class PaymentForm(StatesGroup):
    manager_name = State()
    payment_amount = State()
    tx_hash = State()



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

# Заменить функцию manage_users в admin.py:

@router.callback_query(F.data.startswith("manage_users"))
async def manage_users(callback: CallbackQuery, state: FSMContext):
    """Управление пользователями с пагинацией и блокировкой"""
    try:
        if not await is_admin(callback.from_user.id):
            await callback.answer("Доступ только для администраторов.")
            return

        # Исправленная логика парсинга страницы
        parts = callback.data.split("_")
        if len(parts) > 2 and parts[2].isdigit():
            page = int(parts[2])
        else:
            page = 1
            
        per_page = 5
        admin_id = callback.from_user.id

        config = load_config()
        Session = await init_db(config)
        with Session() as session:
            users = session.query(User).filter_by(assigned_admin=admin_id).order_by(User.registration_date.desc()).offset((page - 1) * per_page).limit(per_page).all()
            total_users = session.query(User).filter_by(assigned_admin=admin_id).count()

        if not users:
            await callback.message.answer("Пользователи не найдены.")
            return

        for user in users:
            user_text = (
                f"ID: {user.telegram_id}\n"
                f"Username: @{user.username or 'Не указан'}\n"
                f"Status: {user.status}\n"
                f"Registration date: {user.registration_date.strftime('%Y-%m-%d %H:%M') if user.registration_date else 'Не указано'}\n"
                f"Profit total: {user.profit_total or 0}$"
            )
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Заблокировать", callback_data=f"block_user_{user.telegram_id}")]
            ])
            await callback.message.answer(user_text, reply_markup=keyboard)

        # Пагинация
        total_pages = (total_users + per_page - 1) // per_page
        pagination_buttons = []
        if page > 1:
            pagination_buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"manage_users_{page-1}"))
        if page < total_pages:
            pagination_buttons.append(InlineKeyboardButton(text="Вперед ➡️", callback_data=f"manage_users_{page+1}"))

        if pagination_buttons:
            await callback.message.answer(f"Страница {page} из {total_pages}", reply_markup=InlineKeyboardMarkup(inline_keyboard=[pagination_buttons]))

        await callback.answer()
    except Exception as e:
        logger.error(f"Ошибка в manage_users: {e}")
        await callback.answer("Ошибка при получении списка пользователей.")

# В файле admin.py заменить функцию show_my_workers:
@router.message(F.text == "My Workers")
async def show_my_workers(message: Message):
    """Показать воркеров админа с их статистикой по выплатам"""
    try:
        config = load_config()
        
        if message.from_user.id not in config.admin_ids:
            await message.answer("Только для администраторов.")
            return
        
        Session = await init_db(config)
        with Session() as session:
            # Получаем всех воркеров, привязанных к этому админу
            workers = session.query(User).filter_by(
                assigned_admin=message.from_user.id,
                status="active"
            ).all()
            
            if not workers:
                await message.answer("У вас пока нет активных воркеров.")
                return
            
            # Получаем статистику по выплатам за неделю
            from datetime import datetime, timedelta
            week_ago = datetime.utcnow() - timedelta(days=7)
            
            total_profit = 0
            week_profit = 0
            
            workers_text = f"👥 Ваши воркеры ({len(workers)} чел.)\n\n"
            
            for worker in workers:
                # Получаем профит воркера по имени из таблицы выплат
                worker_payments = session.query(func.sum(Payment.manager_profit)).filter(
                    Payment.manager_name == (worker.username or f"User{worker.telegram_id}")
                ).scalar() or 0
                
                week_payments = session.query(func.sum(Payment.manager_profit)).filter(
                    Payment.manager_name == (worker.username or f"User{worker.telegram_id}"),
                    Payment.created_at >= week_ago
                ).scalar() or 0
                
                total_profit += worker_payments
                week_profit += week_payments
                
                workers_text += (
                    f"• @{worker.username or f'User{worker.telegram_id}'}: "
                    f"{worker_payments}$ (неделя: {week_payments}$)\n"
                )
            
            workers_text = (
                f"👥 Ваши воркеры ({len(workers)} чел.)\n\n"
                f"💰 Общий профит: {total_profit}$\n"
                f"📊 Профит за неделю: {week_profit}$\n\n"
                f"👤 Список воркеров:\n" + workers_text.split("👤 Список воркеров:\n")[0] if "👤 Список воркеров:\n" in workers_text else workers_text
            )
        
        await message.answer(workers_text)
        
    except Exception as e:
        logger.error(f"Ошибка в show_my_workers: {e}")
        await message.answer("Ошибка при получении списка воркеров.")

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
    """Начало публикации выплаты"""
    try:
        if not await is_admin(callback.from_user.id):
            await callback.answer("Доступ только для администраторов.")
            return
            
        await callback.message.answer("Введите имя менеджера:")
        await state.set_state(PaymentForm.manager_name)
        await callback.answer()
    except Exception as e:
        logger.error(f"Ошибка в post_payment: {e}")
        await callback.answer("Ошибка при создании формы выплаты.")

@router.message(PaymentForm.manager_name)
async def process_manager_name(message: Message, state: FSMContext):
    """Обработка имени менеджера"""
    try:
        manager_name = message.text.strip()
        if len(manager_name) < 2:
            await message.answer("Имя менеджера должно быть длиннее.")
            return
        await state.update_data(manager_name=manager_name)
        await message.answer("Введите сумму платежа в USDT:")
        await state.set_state(PaymentForm.payment_amount)
    except Exception as e:
        logger.error(f"Ошибка в process_manager_name: {e}")
        await message.answer("Ошибка при вводе имени менеджера.")

@router.message(PaymentForm.payment_amount)
async def process_payment_amount(message: Message, state: FSMContext):
    """Обработка суммы платежа"""
    try:
        amount = float(message.text.replace(',', '.'))
        if amount <= 0:
            await message.answer("Сумма должна быть больше нуля.")
            return
        await state.update_data(payment_amount=amount)
        await message.answer("Введите хэш транзакции (TxID):")
        await state.set_state(PaymentForm.tx_hash)
    except ValueError:
        await message.answer("Укажите корректную сумму (например, 520.50).")
    except Exception as e:
        logger.error(f"Ошибка в process_payment_amount: {e}")
        await message.answer("Ошибка при вводе суммы.")

@router.message(PaymentForm.tx_hash)
async def process_tx_hash(message: Message, state: FSMContext):
    """Обработка хэша транзакции и публикация поста"""
    try:
        config = load_config()
        data = await state.get_data()
        manager_name = data['manager_name']
        payment_amount = data['payment_amount']
        tx_hash = message.text.strip()
        manager_profit = payment_amount * 0.5

        payment_text = (
            f"👤 Закрытие клиента от менеджера: {manager_name}\n\n"
            f"💰 Сумма платежа клиента: {payment_amount} USDT\n"
            f"📊 Процент менеджера: {manager_profit} USDT\n"
            f"🔗 Хэш транзакции: [{tx_hash}](https://tronscan.org/#/transaction/{tx_hash})"
        )

        # Сохраняем данные о выплате в базу
        Session = await init_db(config)
        with Session() as session:
            payment = Payment(
                manager_name=manager_name,
                payment_amount=payment_amount,
                manager_profit=manager_profit,
                tx_hash=tx_hash,
                created_at=datetime.utcnow()
            )
            session.add(payment)
            session.commit()

        await message.bot.send_message(config.payment_channel, payment_text, parse_mode="Markdown")
        await message.answer("Выплата успешно опубликована!")
        await state.clear()
    except Exception as e:
        logger.error(f"Ошибка в process_tx_hash: {e}")
        await message.answer("Ошибка при публикации выплаты.")
        await state.clear()


@router.callback_query(F.data.startswith("block_user_"))
async def block_user(callback: CallbackQuery):
    """Блокировка пользователя"""
    try:
        if not await is_admin(callback.from_user.id):
            await callback.answer("Доступ только для администраторов.")
            return

        user_id = int(callback.data.split("_")[2])
        await update_user_status(user_id, "banned")
        await callback.message.edit_text(f"{callback.message.text}\n\n❌ Пользователь {user_id} заблокирован администратором @{callback.from_user.username}")
        await callback.bot.send_message(user_id, "Ваш аккаунт заблокирован.")
        await callback.answer("Пользователь заблокирован!")
    except Exception as e:
        logger.error(f"Ошибка в block_user: {e}")
        await callback.answer("Ошибка при блокировке пользователя.")

# Добавить в admin.py после функции show_my_workers:

@router.callback_query(F.data == "show_workers")
async def show_workers_callback(callback: CallbackQuery):
    """Показать воркеров админа через callback"""
    try:
        config = load_config()
        
        if callback.from_user.id not in config.admin_ids:
            await callback.answer("Только для администраторов.")
            return
        
        Session = await init_db(config)
        with Session() as session:
            # Получаем всех воркеров, привязанных к этому админу
            workers = session.query(User).filter_by(
                assigned_admin=callback.from_user.id,
                status="active"
            ).all()
            
            if not workers:
                await callback.message.answer("У вас пока нет активных воркеров.")
                await callback.answer()
                return
            
            # Получаем статистику по выплатам за неделю
            from datetime import datetime, timedelta
            week_ago = datetime.utcnow() - timedelta(days=7)
            
            total_profit = 0
            week_profit = 0
            
            workers_text = f"👥 Ваши воркеры ({len(workers)} чел.)\n\n"
            
            for worker in workers:
                # Получаем профит воркера по имени из таблицы выплат
                worker_payments = session.query(func.sum(Payment.manager_profit)).filter(
                    Payment.manager_name == (worker.username or f"User{worker.telegram_id}")
                ).scalar() or 0
                
                week_payments = session.query(func.sum(Payment.manager_profit)).filter(
                    Payment.manager_name == (worker.username or f"User{worker.telegram_id}"),
                    Payment.created_at >= week_ago
                ).scalar() or 0
                
                total_profit += worker_payments
                week_profit += week_payments
                
                workers_text += (
                    f"• @{worker.username or f'User{worker.telegram_id}'}: "
                    f"{worker_payments}$ (неделя: {week_payments}$)\n"
                )
            
            workers_text = (
                f"👥 Ваши воркеры ({len(workers)} чел.)\n\n"
                f"💰 Общий профит: {total_profit}$\n"
                f"📊 Профит за неделю: {week_profit}$\n\n"
                f"👤 Список воркеров:\n" + workers_text.split("👤 Список воркеров:\n")[0] if "👤 Список воркеров:\n" in workers_text else workers_text
            )
        
        await callback.message.answer(workers_text)
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в show_workers_callback: {e}")
        await callback.answer("Ошибка при получении списка воркеров.")
