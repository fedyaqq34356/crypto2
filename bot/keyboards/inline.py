from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_start_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Подать заявку", callback_data="apply")]
    ])

def get_confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Подтвердить", callback_data="confirm"),
            InlineKeyboardButton(text="Редактировать", callback_data="edit")
        ]
    ])

def get_welcome_keyboard() -> InlineKeyboardMarkup:
    """Упрощенная клавиатура приветствия без чата команды"""
    from config import load_config
    config = load_config()
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Выплаты", url=config.payment_channel_url)],
        [InlineKeyboardButton(text="Канал", url=config.main_channel)]
    ])

def get_channel_keyboard(url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Перейти", url=url)]
    ])

def get_invite_keyboard(url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Поделиться", url=url)]
    ])

def get_admin_approval_keyboard(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Подтвердить", callback_data=f"approve_{user_id}"),
            InlineKeyboardButton(text="Отклонить", callback_data=f"reject_{user_id}")
        ]
    ])

def get_exchange_keyboard(exchange_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Начать обмен", callback_data=f"start_exchange_{exchange_id}")]
    ])

# В файле inline.py заменить функцию get_admin_menu:
# Заменить функцию get_admin_menu в inline.py:

def get_admin_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Управление пользователями", callback_data="manage_users_1")],
        [InlineKeyboardButton(text="Админ группа", callback_data="admin_group")],
        [InlineKeyboardButton(text="Опубликовать выплату", callback_data="post_payment")],
        [InlineKeyboardButton(text="Сгенерировать UTM ссылку", callback_data="generate_utm")],
        [InlineKeyboardButton(text="Мои воркеры", callback_data="show_workers")]
    ])

def get_admin_exchange_keyboard(exchange_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для админа при работе с обменом"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Начать обмен", callback_data=f"admin_start_exchange_{exchange_id}")]
    ])

def get_worker_confirmation_keyboard(exchange_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для подтверждения отправки BTC"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Подтвердить отправку BTC", callback_data=f"confirm_transaction_{exchange_id}")]
    ])

def get_usdt_wallet_keyboard(exchange_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для генерации USDT кошелька"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Сгенерировать USDT кошелек", callback_data=f"generate_usdt_{exchange_id}")]
    ])

def get_admin_approval_keyboard_with_admin(user_id: int, assigned_admin: int) -> InlineKeyboardMarkup:
    """Клавиатура одобрения с информацией об админе"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Подтвердить", callback_data=f"approve_{user_id}_{assigned_admin}"),
            InlineKeyboardButton(text="Отклонить", callback_data=f"reject_{user_id}_{assigned_admin}")
        ]
    ])

def get_exchange_keyboard_with_admin(exchange_id: int, assigned_admin: int) -> InlineKeyboardMarkup:
    """Клавиатура обмена с проверкой админа"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Начать обмен", callback_data=f"start_exchange_{exchange_id}_{assigned_admin}")]
    ])

def get_close_exchange_keyboard(exchange_id: int, assigned_admin: int) -> InlineKeyboardMarkup:
    """Клавиатура закрытия обмена"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Закрыть обмен", callback_data=f"close_exchange_{exchange_id}_{assigned_admin}")]
    ])
