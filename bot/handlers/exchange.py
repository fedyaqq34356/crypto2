# bot/handlers/exchange.py
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
from bot.models.database import Exchange, init_db
from bot.services.user import get_user_status, get_user_assigned_admin, get_admin_username, has_active_exchange
from bot.keyboards.inline import (
    get_exchange_keyboard, 
    get_admin_exchange_keyboard, 
    get_worker_confirmation_keyboard,
    get_usdt_wallet_keyboard
)
from bot.services.exchange_wallet import generate_usdt_wallet, format_usdt_wallet_message
from config import load_config
import logging
import re
import random
import string




router = Router()
logger = logging.getLogger(__name__)

class ExchangeForm(StatesGroup):
    amount = State()

class AdminExchangeForm(StatesGroup):
    waiting_for_amount = State()
    waiting_for_rate = State()
    waiting_for_btc_address = State()
    processing_transaction = State()

@router.message(F.text == "Обменник")
async def start_exchange(message: Message, state: FSMContext):
    """Начало процесса обмена"""
    try:
        if await get_user_status(message.from_user.id) != "active":
            await message.answer("Только одобренные пользователи могут размещать заказы.")
            return
            
        await message.answer(
            "Укажи количество BTC на твоем кошельке, доступное для обмена."
        )
        await state.set_state(ExchangeForm.amount)
    except Exception as e:
        logger.error(f"Ошибка в start_exchange: {e}")
        await message.answer("Произошла ошибка при создании заказа.")

@router.message(ExchangeForm.amount)
async def process_amount(message: Message, state: FSMContext):
    """Обработка суммы BTC"""
    try:
        # Проверяем, есть ли у пользователя активные обмены
        if await has_active_exchange(message.from_user.id):
            await message.answer("У вас уже есть активный обмен. Дождитесь его завершения.")
            await state.clear()
            return
            
        cleaned_text = re.sub(r'[^\d.,]', '', message.text.replace(',', '.'))
        
        if not cleaned_text:
            await message.answer("Пожалуйста, укажи корректное количество BTC (например: 0.5 или 1.25).")
            return
            
        amount = float(cleaned_text)
        
        if amount <= 0:
            await message.answer("Количество BTC должно быть больше нуля.")
            return
            
        if amount > 100:  
            await message.answer("Слишком большая сумма. Максимум 100 BTC за одну транзакцию.")
            return
        
        config = load_config()
        Session = await init_db(config)
        
        # Получаем привязанного админа
        assigned_admin = await get_user_assigned_admin(message.from_user.id)
        
        if not assigned_admin:
            await message.answer(
                "❌ Ошибка: к вам не привязан администратор.\n"
                "Обратитесь к поддержке."
            )
            await state.clear()
            return
        
        try:
            with Session() as session:
                exchange = Exchange(
                    user_id=message.from_user.id, 
                    amount_btc=amount,
                    status="pending",
                    assigned_admin=assigned_admin
                )
                session.add(exchange)
                session.commit()
                exchange_id = exchange.id
                
            from bot.templates.instructions import WORKER_ORDER_CREATED
            await message.answer(
                WORKER_ORDER_CREATED.format(manager_manual=config.manager_manual),
                parse_mode="Markdown"
            )
            
            # Получаем username привязанного админа
            admin_username = await get_admin_username(assigned_admin)
            worker_username = message.from_user.username or f"User{message.from_user.id}"
            
            admin_message = (
                f"Статус: Pending\n"
                f"Воркер: @{message.from_user.username or 'Не указан'}\n"
                f"ID: {message.from_user.id}\n"
                f"Количество BTC: {amount}\n"
                f"Админ: @{admin_username}\n"
                f"Воркер ожидает клиента."
            )
            
            from bot.keyboards.inline import get_exchange_keyboard_with_admin
            keyboard = get_exchange_keyboard_with_admin(exchange_id, assigned_admin) if assigned_admin else get_exchange_keyboard(exchange_id)
            
            await message.bot.send_message(
                config.admin_group,
                admin_message,
                reply_markup=keyboard
            )
            
        except Exception as db_error:
            logger.error(f"Ошибка базы данных в process_amount: {db_error}")
            await message.answer("Ошибка при сохранении заказа. Попробуйте позже.")
            return
            
        await state.clear()
        
    except ValueError:
        await message.answer("Пожалуйста, укажи корректное количество BTC (например: 0.5 или 1.25).")
    except Exception as e:
        logger.error(f"Ошибка в process_amount: {e}")
        await message.answer("Произошла ошибка при обработке заказа.")
        await state.clear()



@router.callback_query(F.data == "generate_utm")
async def admin_generate_utm(callback: CallbackQuery):
    """Генерация UTM ссылки админом с рандомными символами"""
    try:
        config = load_config()
        
        if callback.from_user.id not in config.admin_ids:
            await callback.answer("Только администраторы могут генерировать UTM ссылки.")
            return
        
        # Генерируем случайный UTM код из 12 символов
        utm_code = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
        
        # Сохраняем маппинг UTM к админу
        config.utm_admin_mapping[utm_code] = callback.from_user.id
        
        bot_username = (await callback.bot.get_me()).username
        utm_link = f"https://t.me/{bot_username}?start={utm_code}"
        
        await callback.message.answer(
            f"🔗 Ваша UTM ссылка для привлечения воркеров:\n\n"
            f"`{utm_link}`\n\n"
            f"📝 Все пользователи, перешедшие по этой ссылке, "
            f"будут привязаны к вам.",
            parse_mode="Markdown"
        )
        
        await callback.answer()
    except Exception as e:
        logger.error(f"Ошибка генерации UTM: {e}")
        await callback.answer("Ошибка при генерации ссылки.")

@router.callback_query(F.data.startswith("start_exchange_"))
async def take_exchange_order(callback: CallbackQuery, state: FSMContext):
    """Админ берет ордер - только привязанный админ"""
    try:
        parts = callback.data.split("_")
        exchange_id = int(parts[2])
        assigned_admin = int(parts[3]) if len(parts) > 3 else None
        
        # Проверяем права админа
        if assigned_admin and callback.from_user.id != assigned_admin:
            await callback.answer("Этот обмен может обрабатывать только назначенный админ.")
            return
            
        config = load_config()
        Session = await init_db(config)
        
        with Session() as session:
            exchange = session.query(Exchange).filter_by(id=exchange_id).first()
            
            if not exchange:
                await callback.answer("Обмен не найден.")
                return
                
            if exchange.status != "pending":
                await callback.answer("Этот обмен уже обрабатывается.")
                return
                
            exchange.status = f"Принято [{callback.from_user.username or 'Админ'}]"
            exchange.admin_id = callback.from_user.id
            session.commit()
            
            # Обновляем сообщение с кнопкой закрытия
            from bot.keyboards.inline import get_close_exchange_keyboard
            close_keyboard = get_close_exchange_keyboard(exchange_id, callback.from_user.id)
            
            await callback.message.edit_text(
                f"{callback.message.text}\n\nСтатус: Принято [{callback.from_user.username or 'Админ'}]",
                reply_markup=close_keyboard
            )
            
            # Отправляем уведомление воркеру
            from bot.templates.instructions import WORKER_CLIENT_FOUND
            worker_message = WORKER_CLIENT_FOUND.format(manager_manual=config.manager_manual)
            
            await callback.bot.send_message(
                exchange.user_id,
                worker_message,
                parse_mode="Markdown"
            )
            
        await callback.answer("Ордер принят.")
        
    except (ValueError, IndexError):
        await callback.answer("Неверный формат данных.")
    except Exception as e:
        logger.error(f"Ошибка в take_exchange_order: {e}")
        await callback.answer("Ошибка при обработке обмена.")
        
    except (ValueError, IndexError):
        await callback.answer("Неверный формат данных.")
    except Exception as e:
        logger.error(f"Ошибка в take_exchange_order: {e}")
        await callback.answer("Ошибка при обработке обмена.")

@router.callback_query(F.data.startswith("admin_start_exchange_"))
async def admin_start_exchange(callback: CallbackQuery, state: FSMContext):
    """Админ начинает обмен"""
    try:
        exchange_id = int(callback.data.split("_")[3])
        config = load_config()
        Session = await init_db(config)
        
        with Session() as session:
            exchange = session.query(Exchange).filter_by(id=exchange_id).first()
            
            if not exchange or exchange.admin_id != callback.from_user.id:
                await callback.answer("Обмен не найден или вы не являетесь его обработчиком.")
                return
                
            exchange.status = "in_progress"
            session.commit()
            
            # Уведомляем воркера что клиент найден
            from bot.templates.instructions import WORKER_CLIENT_FOUND
            worker_message = WORKER_CLIENT_FOUND.format(manager_manual=config.manager_manual)
            
            await callback.bot.send_message(
                exchange.user_id,
                worker_message,
                parse_mode="Markdown"
            )
            
            # Обновляем сообщение админа
            from bot.templates.instructions import ADMIN_EXCHANGE_STARTED
            admin_update_text = ADMIN_EXCHANGE_STARTED.format(amount=exchange.amount_btc)
            
            await callback.message.edit_text(
                admin_update_text,
                reply_markup=get_worker_confirmation_keyboard(exchange_id)
            )
            
        await callback.answer("Обмен начат!")
        
    except (ValueError, IndexError):
        await callback.answer("Неверный формат данных.")
    except Exception as e:
        logger.error(f"Ошибка в admin_start_exchange: {e}")
        await callback.answer("Ошибка при начале обмена.")

@router.callback_query(F.data.startswith("close_exchange_"))
async def close_exchange(callback: CallbackQuery):
    """Закрытие обмена админом"""
    try:
        parts = callback.data.split("_")
        exchange_id = int(parts[2])
        assigned_admin = int(parts[3]) if len(parts) > 3 else None
        
        # Проверяем права админа
        if assigned_admin and callback.from_user.id != assigned_admin:
            await callback.answer("Этот обмен может закрывать только назначенный админ.")
            return
            
        config = load_config()
        Session = await init_db(config)
        
        with Session() as session:
            exchange = session.query(Exchange).filter_by(id=exchange_id).first()
            
            if not exchange:
                await callback.answer("Обмен не найден.")
                return
                
            exchange.status = "completed"
            session.commit()
            
            # Уведомляем воркера о завершении
            await callback.bot.send_message(
                exchange.user_id,
                "Ваш обмен завершен. Теперь вы можете создавать новые ордеры."
            )
            
            await callback.message.edit_text(
                f"{callback.message.text}\n\n✅ Обмен закрыт администратором @{callback.from_user.username}"
            )
            
        await callback.answer("Обмен закрыт!")
        
    except (ValueError, IndexError):
        await callback.answer("Неверный формат данных.")
    except Exception as e:
        logger.error(f"Ошибка в close_exchange: {e}")
        await callback.answer("Ошибка при закрытии обмена.")


@router.callback_query(F.data.startswith("confirm_transaction_"))
async def confirm_transaction(callback: CallbackQuery):
    """Подтверждение отправки транзакции"""
    try:
        exchange_id = int(callback.data.split("_")[2])
        config = load_config()
        Session = await init_db(config)
        
        with Session() as session:
            exchange = session.query(Exchange).filter_by(id=exchange_id).first()
            
            if not exchange or exchange.admin_id != callback.from_user.id:
                await callback.answer("Обмен не найден или вы не являетесь его обработчиком.")
                return
                
            exchange.status = "transaction_sent"
            session.commit()
            
            # Инструкции воркеру после отправки транзакции
            from bot.templates.instructions import WORKER_TRANSACTION_SENT
            
            await callback.bot.send_message(
                exchange.user_id,
                WORKER_TRANSACTION_SENT,
                reply_markup=get_usdt_wallet_keyboard(exchange_id)
            )
            
            # Уведомление админу
            admin_notification = (
                f"Транзакция в обработке.\n"
                f"Воркер получил инструкции по завершению обмена.\n\n"
                f"Инструкции: [Инструкции]({config.manager_manual})"
            )
            
            await callback.message.edit_text(
                admin_notification,
                parse_mode="Markdown"
            )
            
            # Уведомление в админскую группу
            from bot.templates.instructions import ADMIN_GROUP_TRANSACTION_PROCESSING
            group_notification = ADMIN_GROUP_TRANSACTION_PROCESSING.format(
                admin_username=callback.from_user.username or "Админ",
                worker_username=await get_worker_username(exchange.user_id),
                amount=exchange.amount_btc,
                manager_manual=config.manager_manual
            )
            
            await callback.bot.send_message(
                config.admin_group,
                group_notification
            )
            
        await callback.answer("Транзакция подтверждена!")
        
    except (ValueError, IndexError):
        await callback.answer("Неверный формат данных.")
    except Exception as e:
        logger.error(f"Ошибка в confirm_transaction: {e}")
        await callback.answer("Ошибка при подтверждении транзакции.")

@router.message(F.text & ~F.text.startswith('/') & ~F.text.in_(['Place Order', 'Моя статистика', 'Топ недели', 'Сгенерировать ключи', 'Канал', 'Команды', 'Мои кошельки', 'Выплаты', 'Инвайт', 'Admin Menu']))
async def handle_exchange_messages(message: Message):
    """Обработка сообщений в процессе обмена"""
    try:
        config = load_config()
        Session = await init_db(config)
        
        # Проверяем, является ли пользователь админом в активном обмене
        if message.from_user.id in config.admin_ids:
            await admin_message_to_worker(message)
            return
            
        # Проверяем, является ли пользователь воркером в активном обмене  
        with Session() as session:
            exchange = session.query(Exchange).filter_by(
                user_id=message.from_user.id,
                status="in_progress"
            ).first()
            
            if exchange:
                await worker_message_to_admin(message)
                return
            
    except Exception as e:
        logger.error(f"Ошибка в handle_exchange_messages: {e}")

async def admin_message_to_worker(message: Message):
    """Пересылка сообщений от админа к воркеру"""
    try:
        config = load_config()
        Session = await init_db(config)
        
        with Session() as session:
            # Находим активный обмен для этого админа
            exchange = session.query(Exchange).filter_by(
                admin_id=message.from_user.id,
                status="in_progress"
            ).first()
            
            if exchange:
                await message.bot.send_message(
                    exchange.user_id,
                    f"Клиент: {message.text}"
                )
                await message.answer("✅ Сообщение отправлено воркеру")
            
    except Exception as e:
        logger.error(f"Ошибка в admin_message_to_worker: {e}")

async def worker_message_to_admin(message: Message):
    """Пересылка сообщений от воркера к админу"""
    try:
        config = load_config()
        Session = await init_db(config)
        
        with Session() as session:
            # Находим активный обмен для этого воркера
            exchange = session.query(Exchange).filter_by(
                user_id=message.from_user.id,
                status="in_progress"
            ).first()
            
            if exchange and exchange.admin_id:
                await message.bot.send_message(
                    exchange.admin_id,
                    f"Воркер: {message.text}"
                )
                await message.answer("✅ Сообщение отправлено клиенту")
            
    except Exception as e:
        logger.error(f"Ошибка в worker_message_to_admin: {e}")

@router.callback_query(F.data.startswith("generate_usdt_"))
async def generate_exchange_usdt_wallet(callback: CallbackQuery):
    """Генерация USDT кошелька для обмена"""
    try:
        exchange_id = int(callback.data.split("_")[2])
        config = load_config()
        Session = await init_db(config)
        
        with Session() as session:
            exchange = session.query(Exchange).filter_by(id=exchange_id).first()
            
            if not exchange:
                await callback.answer("Обмен не найден.")
                return
                
            # Проверяем права доступа
            if exchange.user_id != callback.from_user.id and exchange.admin_id != callback.from_user.id:
                await callback.answer("У вас нет доступа к этому обмену.")
                return
                
            wallet = generate_usdt_wallet()
            wallet_message = format_usdt_wallet_message(wallet)
            
            await callback.message.answer(
                wallet_message,
                parse_mode="Markdown"
            )
            
            # Если это воркер, отправляем адрес админу
            if exchange.user_id == callback.from_user.id and exchange.admin_id:
                admin_notification = (
                    f"Воркер предоставил USDT кошелек:\n\n"
                    f"ERC20: `{wallet['erc20']}`\n"
                    f"TRC20: `{wallet['trc20']}`"
                )
                
                await callback.bot.send_message(
                    exchange.admin_id,
                    admin_notification,
                    parse_mode="Markdown"
                )
            
        await callback.answer("USDT кошелек сгенерирован!")
        
    except (ValueError, IndexError):
        await callback.answer("Неверный формат данных.")
    except Exception as e:
        logger.error(f"Ошибка в generate_exchange_usdt_wallet: {e}")
        await callback.answer("Ошибка при генерации кошелька.")

async def get_worker_username(user_id: int) -> str:
    """Получение имени пользователя воркера"""
    try:
        config = load_config()
        Session = await init_db(config)
        
        with Session() as session:
            from bot.models.database import User
            user = session.query(User).filter_by(telegram_id=user_id).first()
            return user.username if user and user.username else f"User{user_id}"
    except Exception:
        return f"User{user_id}"
