# bot/services/exchange_wallet.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import random
import string

def generate_usdt_wallet() -> dict:
    """Генерация USDT кошелька для обмена"""
    
    # Генерируем случайные адреса (в реальном проекте используйте настоящие кошельки)
    erc20_chars = "0123456789abcdef"
    trc20_chars = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    
    erc20_address = "0x" + ''.join(random.choices(erc20_chars, k=40))
    trc20_address = "T" + ''.join(random.choices(trc20_chars, k=33))
    
    return {
        "erc20": erc20_address,
        "trc20": trc20_address
    }

def get_usdt_wallet_keyboard(exchange_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для генерации USDT кошелька"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Сгенерировать USDT кошелек", callback_data=f"generate_usdt_{exchange_id}")]
    ])

def format_usdt_wallet_message(wallet: dict) -> str:
    """Форматирование сообщения с USDT кошельком"""
    return f"""CryptoBusinessTeam,

Ваш USDT кошелек для получения средств:

ERC20 (Ethereum, BSC, Polygon, etc.): 
`{wallet['erc20']}`

TRC20 (Tron): 
`{wallet['trc20']}`

⚠️ ВАЖНО:
- Используйте соответствующую сеть при отправке
- ERC20 адрес подходит для всех EVM-совместимых сетей
- Проверьте адрес перед отправкой средств"""