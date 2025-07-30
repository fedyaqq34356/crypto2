from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# В файле reply.py заменить функцию get_worker_menu:
def get_worker_menu() -> ReplyKeyboardMarkup:
    """Создание клавиатуры для воркеров"""
    kb = [
        [KeyboardButton(text="Моя статистика")],
        [
            KeyboardButton(text="Топ недели"),
            KeyboardButton(text="Мануалы")
        ],
        [
            KeyboardButton(text="Канал"),
            KeyboardButton(text="Выплаты")
        ],
        [
            KeyboardButton(text="Сгенерировать инвайт"),
            KeyboardButton(text="Обменник")
        ]
    ]
    return ReplyKeyboardMarkup(
        keyboard=kb, 
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Выберите действие..."
    )


def get_admin_menu() -> ReplyKeyboardMarkup:
    """Создание клавиатуры для администраторов - только админские функции"""
    kb = [
        [KeyboardButton(text="Admin Menu")]
    ]
    return ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Админ-панель..."
    )
