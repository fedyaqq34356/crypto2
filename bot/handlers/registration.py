from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from bot.keyboards.inline import get_confirm_keyboard, get_welcome_keyboard
from bot.keyboards.reply import get_worker_menu
from bot.services.user import save_user_data, send_to_admin, update_user_status, get_user_status
from config import load_config
import logging

router = Router()
logger = logging.getLogger(__name__)

class RegistrationForm(StatesGroup):
    name_age = State()
    experience = State()
    work_hours = State()
    transaction_knowledge = State()
    confirm = State()

@router.callback_query(F.data == "apply")
async def start_registration(callback: CallbackQuery, state: FSMContext):
    """Начало регистрации"""
    try:
        user_status = await get_user_status(callback.from_user.id)
        if user_status in ["active", "pending"]:
            status_text = "одобрен" if user_status == "active" else "на рассмотрении"
            await callback.message.answer(f"Ваш аккаунт уже {status_text}.")
            await callback.answer()
            return
            
        await callback.message.answer(

            f"1. Укажи свое имя и возраст."
        )
        await state.set_state(RegistrationForm.name_age)
        await callback.answer()
    except Exception as e:
        logger.error(f"Ошибка в start_registration: {e}")
        await callback.answer("Ошибка при начале регистрации.")

@router.message(RegistrationForm.name_age)
async def process_name_age(message: Message, state: FSMContext):
    """Обработка имени и возраста"""
    try:
        if len(message.text.strip()) < 3:
            await message.answer("Пожалуйста, укажите имя и возраст более подробно.")
            return
            
        await state.update_data(name_age=message.text.strip())
        await message.answer(
            f"2. Был ли опыт работы на звонках/чатах? (Если был, подробно описать)"
        )
        await state.set_state(RegistrationForm.experience)
    except Exception as e:
        logger.error(f"Ошибка в process_name_age: {e}")
        await message.answer("Произошла ошибка. Попробуйте ещё раз.")

@router.message(RegistrationForm.experience)
async def process_experience(message: Message, state: FSMContext):
    """Обработка опыта работы"""
    try:
        if len(message.text.strip()) < 3:
            await message.answer("Пожалуйста, опишите ваш опыт более подробно.")
            return
            
        await state.update_data(experience=message.text.strip())
        await message.answer(
            f"3. Сколько времени готовы уделять работе?"
        )
        await state.set_state(RegistrationForm.work_hours)
    except Exception as e:
        logger.error(f"Ошибка в process_experience: {e}")
        await message.answer("Произошла ошибка. Попробуйте ещё раз.")

@router.message(RegistrationForm.work_hours)
async def process_work_hours(message: Message, state: FSMContext):
    """Обработка рабочего времени"""
    try:
        if len(message.text.strip()) < 3:
            await message.answer("Пожалуйста, укажите более конкретно.")
            return
            
        await state.update_data(work_hours=message.text.strip())
        await message.answer(
            f"4. Понимаете ли вы, как работает отмена транзакции?"
        )
        await state.set_state(RegistrationForm.transaction_knowledge)
    except Exception as e:
        logger.error(f"Ошибка в process_work_hours: {e}")
        await message.answer("Произошла ошибка. Попробуйте ещё раз.")

@router.message(RegistrationForm.transaction_knowledge)
async def process_transaction_knowledge(message: Message, state: FSMContext):
    """Обработка знаний о транзакциях"""
    try:
        if len(message.text.strip()) < 3:
            await message.answer("Пожалуйста, ответьте более подробно.")
            return
            
        await state.update_data(transaction_knowledge=message.text.strip())
        data = await state.get_data()
        
        summary_text = (
            f"Проверь свою анкету:\n\n"
            f"Имя и возраст: {data['name_age']}\n"
            f"Опыт: {data['experience']}\n"
            f"Время для работы: {data['work_hours']}\n"
            f"Понимание процесса: {data['transaction_knowledge']}"
        )

        
        await message.answer(summary_text, reply_markup=get_confirm_keyboard())
        await state.set_state(RegistrationForm.confirm)
    except Exception as e:
        logger.error(f"Ошибка в process_transaction_knowledge: {e}")
        await message.answer("Произошла ошибка. Попробуйте ещё раз.")

@router.callback_query(RegistrationForm.confirm, F.data == "confirm")
async def confirm_registration(callback: CallbackQuery, state: FSMContext):
    """Подтверждение регистрации"""
    try:
        data = await state.get_data()
        
        await save_user_data(
            callback.from_user.id, 
            callback.from_user.username, 
            data
        )
        
        await send_to_admin(
            callback.bot, 
            data, 
            callback.from_user.id, 
            callback.from_user.username
        )
        
        await callback.message.answer(

            f"Твоя анкета отправлена на рассмотрение."
        )
        
        await state.clear()
        await callback.answer("Анкета отправлена!")
        
    except Exception as e:
        logger.error(f"Ошибка в confirm_registration: {e}")
        await callback.answer("Ошибка при отправке анкеты.")

@router.callback_query(RegistrationForm.confirm, F.data == "edit")
async def edit_registration(callback: CallbackQuery, state: FSMContext):
    """Редактирование анкеты"""
    try:
        await callback.message.answer(

            f"Заполни свою анкету заново:\n"
            f"1. Укажи свое имя и возраст."
        )
        await state.set_state(RegistrationForm.name_age)
        await callback.answer("Начинаем заново...")
    except Exception as e:
        logger.error(f"Ошибка в edit_registration: {e}")
        await callback.answer("Ошибка при редактировании.")

@router.callback_query(F.data.startswith("approve_"))
async def approve_user(callback: CallbackQuery):
    """Одобрение пользователя"""
    try:
        user_id = int(callback.data.split("_")[1])
        config = load_config()
        
        await update_user_status(user_id, "active")
        await callback.message.edit_text(
            f"{callback.message.text}\n\n✅ Пользователь {user_id} одобрен администратором @{callback.from_user.username}"
        )
        
        # Первое сообщение - поздравление с инлайн кнопками (без названия команды и чата команды)
        welcome_text = (

            f"Поздравляем! Ты добавлен(а) в команду\n\n"
            f"Подпишись на наши каналы:"
        )
        
        # Создаем упрощенную клавиатуру без "Чат команды"
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        welcome_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Выплаты", url=config.payment_channel_url)],
            [InlineKeyboardButton(text="Канал", url=config.main_channel)]
        ])
        
        await callback.bot.send_message(
            user_id,
            welcome_text,
            reply_markup=welcome_keyboard
        )
        
        # Второе сообщение - инструкции с обычным меню
        instructions_text = (
            f"Теперь тебе доступна клавиатура бота\n\n"
            f"Чем занимаемся:\n"
            f"[Мануал по Electrum (Для ПК)]({config.electrum_manual})\n"
            f"[Мануал Bluewallet (Android/iOS)]({config.bluewallet_manual})\n"
            f"[Инструкция для менеджера]({config.manager_manual})\n\n"
            f"Если ты изучил мануалы и освоил отмену транзакций между своими кошельками, "
            f"значит, ты готов к практике\n\n"
            f"Пиши сюда, чтобы:\n"
            f"- получить аккаунт телеги\n"
            f"- настроить трафик\n"
            f"- пройти обучение и начать ворк"
        )
        
        await callback.bot.send_message(
            user_id,
            instructions_text,
            reply_markup=get_worker_menu(),
            parse_mode="Markdown"
        )
        
        await callback.answer("Пользователь одобрен!")
        
    except (ValueError, IndexError):
        await callback.answer("Неверный формат данных.")
    except Exception as e:
        logger.error(f"Ошибка в approve_user: {e}")
        await callback.answer("Ошибка при одобрении пользователя.")

@router.callback_query(F.data.startswith("reject_"))
async def reject_user(callback: CallbackQuery):
    """Отклонение пользователя"""
    try:
        user_id = int(callback.data.split("_")[1])
        
        await update_user_status(user_id, "banned")
        await callback.message.edit_text(
            f"{callback.message.text}\n\n❌ Пользователь {user_id} отклонен администратором @{callback.from_user.username}"
        )
        
        reject_text = (

            f"Твоя анкета отклонена. Попробуй подать заявку снова."
        )
        
        await callback.bot.send_message(user_id, reject_text)
        await callback.answer("Пользователь отклонен!")
        
    except (ValueError, IndexError):
        await callback.answer("Неверный формат данных.")
    except Exception as e:
        logger.error(f"Ошибка в reject_user: {e}")
        await callback.answer("Ошибка при отклонении пользователя.")
