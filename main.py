import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import load_config
from bot.handlers import start, registration, worker, admin, exchange
from bot.utils.logging import setup_logging

async def main():
    """Основная функция запуска бота"""
    # Настройка логирования
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Загрузка конфигурации
        config = load_config()
        logger.info("Конфигурация загружена")
        
        # Инициализация бота и диспетчера
        bot = Bot(token=config.bot_token)
        storage = MemoryStorage()
        dp = Dispatcher(storage=storage)
        
        # Регистрация роутеров в правильном порядке
        dp.include_router(start.router)
        dp.include_router(registration.router)
        dp.include_router(admin.router)
        dp.include_router(exchange.router)
        dp.include_router(worker.router)  # worker должен быть последним
        
        logger.info("Роутеры зарегистрированы")
        
        # Инициализация базы данных
        from bot.models.database import init_db
        await init_db(config)
        logger.info("База данных инициализирована")
        
        # Запуск бота
        logger.info("Запуск бота...")
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"Критическая ошибка при запуске бота: {e}")
        raise
    finally:
        if 'bot' in locals():
            await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен пользователем")
    except Exception as e:
        print(f"Критическая ошибка: {e}")
        logging.error(f"Критическая ошибка: {e}")