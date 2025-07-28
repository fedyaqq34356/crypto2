from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from bot.models.database import User, init_db
from bot.keyboards.inline import get_admin_approval_keyboard
from config import load_config
import logging

logger = logging.getLogger(__name__)

async def save_user_data(telegram_id: int, username: str, data: dict):
    """Сохранение данных пользователя в базе"""
    try:
        config = load_config()
        Session = await init_db(config)
        
        with Session() as session:
 
            existing_user = session.query(User).filter_by(telegram_id=telegram_id).first()
            
            if existing_user:

                existing_user.username = username
                existing_user.name_age = data.get("name_age", "")
                existing_user.experience = data.get("experience", "")
                existing_user.work_hours = data.get("work_hours", "")
                existing_user.transaction_knowledge = data.get("transaction_knowledge", "")
                existing_user.referral = data.get("referral", "")
                existing_user.status = "pending" 
                logger.info(f"Обновлены данные пользователя {telegram_id}")
            else:

                user = User(
                    telegram_id=telegram_id,
                    username=username,
                    name_age=data.get("name_age", ""),
                    experience=data.get("experience", ""),
                    work_hours=data.get("work_hours", ""),
                    transaction_knowledge=data.get("transaction_knowledge", ""),
                    referral=data.get("referral", ""),
                    status="pending"
                )
                session.add(user)
                logger.info(f"Создан новый пользователь {telegram_id}")
            
            session.commit()
            
    except IntegrityError as e:
        logger.error(f"Ошибка целостности данных при сохранении пользователя {telegram_id}: {e}")
        raise
    except SQLAlchemyError as e:
        logger.error(f"Ошибка SQLAlchemy при сохранении пользователя {telegram_id}: {e}")
        raise
    except Exception as e:
        logger.error(f"Неожиданная ошибка при сохранении пользователя {telegram_id}: {e}")
        raise

async def get_user_status(telegram_id: int) -> str:
    """Получение статуса пользователя"""
    try:
        config = load_config()
        Session = await init_db(config)
        
        with Session() as session:
            user = session.query(User).filter_by(telegram_id=telegram_id).first()
            return user.status if user else "new"
            
    except SQLAlchemyError as e:
        logger.error(f"Ошибка SQLAlchemy при получении статуса пользователя {telegram_id}: {e}")
        return "new"
    except Exception as e:
        logger.error(f"Неожиданная ошибка при получении статуса пользователя {telegram_id}: {e}")
        return "new"

async def update_user_status(telegram_id: int, status: str):
    """Обновление статуса пользователя"""
    try:
        config = load_config()
        Session = await init_db(config)
        
        with Session() as session:
            user = session.query(User).filter_by(telegram_id=telegram_id).first()
            if user:
                user.status = status
                session.commit()
                logger.info(f"Обновлен статус пользователя {telegram_id} на {status}")
            else:
                logger.warning(f"Пользователь {telegram_id} не найден для обновления статуса")
                
    except SQLAlchemyError as e:
        logger.error(f"Ошибка SQLAlchemy при обновлении статуса пользователя {telegram_id}: {e}")
        raise
    except Exception as e:
        logger.error(f"Неожиданная ошибка при обновлении статуса пользователя {telegram_id}: {e}")
        raise

async def get_user_stats(telegram_id: int) -> dict:
    """Получение статистики пользователя"""
    try:
        config = load_config()
        Session = await init_db(config)
        
        with Session() as session:
            user = session.query(User).filter_by(telegram_id=telegram_id).first()
            if user:
                return {
                    "profit_total": user.profit_total or 0.0,
                    "profit_week": user.profit_week or 0.0,
                    "rank": user.rank or "Freshman"
                }
            else:

                return {
                    "profit_total": 0.0,
                    "profit_week": 0.0,
                    "rank": "Freshman"
                }
                
    except SQLAlchemyError as e:
        logger.error(f"Ошибка SQLAlchemy при получении статистики пользователя {telegram_id}: {e}")
        return {"profit_total": 0.0, "profit_week": 0.0, "rank": "Freshman"}
    except Exception as e:
        logger.error(f"Неожиданная ошибка при получении статистики пользователя {telegram_id}: {e}")
        return {"profit_total": 0.0, "profit_week": 0.0, "rank": "Freshman"}

async def get_user_list() -> list:
    """Получение списка всех пользователей"""
    try:
        config = load_config()
        Session = await init_db(config)
        
        with Session() as session:
            users = session.query(User).order_by(User.registration_date.desc()).all()
            result = []
            
            for user in users:
                result.append({
                    "telegram_id": user.telegram_id,
                    "username": user.username or "Не указан",
                    "status": user.status,
                    "referral": user.referral or "Нет",
                    "registration_date": user.registration_date.strftime("%Y-%m-%d %H:%M") if user.registration_date else "Не указана",
                    "profit_total": user.profit_total or 0.0
                })
                
            return result
            
    except SQLAlchemyError as e:
        logger.error(f"Ошибка SQLAlchemy при получении списка пользователей: {e}")
        return []
    except Exception as e:
        logger.error(f"Неожиданная ошибка при получении списка пользователей: {e}")
        return []

async def get_user_info(telegram_id: int) -> dict:
    """Получение информации о конкретном пользователе"""
    try:
        config = load_config()
        Session = await init_db(config)
        
        with Session() as session:
            user = session.query(User).filter_by(telegram_id=telegram_id).first()
            if user:
                return {
                    "telegram_id": user.telegram_id,
                    "username": user.username or "Не указан",
                    "status": user.status,
                    "referral": user.referral or "Нет",
                    "registration_date": user.registration_date.strftime("%Y-%m-%d %H:%M") if user.registration_date else "Не указана",
                    "profit_total": user.profit_total or 0.0,
                    "profit_week": user.profit_week or 0.0,
                    "rank": user.rank or "Freshman"
                }
            else:
                return {}
                
    except SQLAlchemyError as e:
        logger.error(f"Ошибка SQLAlchemy при получении информации о пользователе {telegram_id}: {e}")
        return {}
    except Exception as e:
        logger.error(f"Неожиданная ошибка при получении информации о пользователе {telegram_id}: {e}")
        return {}

async def send_to_admin(bot, data: dict, user_id: int, username: str):
    """Отправка анкеты администратору"""
    try:
        config = load_config()
        
        admin_message = (
            f"Новая анкета:\n"
            f"ID: {user_id}\n"
            f"Username: @{username or 'Не указан'}\n"
            f"Имя и возраст: {data.get('name_age', 'Не указано')}\n"
            f"Опыт: {data.get('experience', 'Не указано')}\n"
            f"Время для работы: {data.get('work_hours', 'Не указано')}\n"
            f"Понимание процесса: {data.get('transaction_knowledge', 'Не указано')}"
        )
        
        await bot.send_message(
            config.admin_group,
            admin_message,
            reply_markup=get_admin_approval_keyboard(user_id)
        )
        
        logger.info(f"Анкета пользователя {user_id} отправлена администратору")
        
    except Exception as e:
        logger.error(f"Ошибка при отправке анкеты администратору для пользователя {user_id}: {e}")
        raise

async def update_user_profit(telegram_id: int, profit_total: float = None, profit_week: float = None):
    """Обновление профита пользователя"""
    try:
        config = load_config()
        Session = await init_db(config)
        
        with Session() as session:
            user = session.query(User).filter_by(telegram_id=telegram_id).first()
            if user:
                if profit_total is not None:
                    user.profit_total = profit_total
                if profit_week is not None:
                    user.profit_week = profit_week
                    
                session.commit()
                logger.info(f"Обновлен профит пользователя {telegram_id}")
            else:
                logger.warning(f"Пользователь {telegram_id} не найден для обновления профита")
                
    except SQLAlchemyError as e:
        logger.error(f"Ошибка SQLAlchemy при обновлении профита пользователя {telegram_id}: {e}")
        raise
    except Exception as e:
        logger.error(f"Неожиданная ошибка при обновлении профита пользователя {telegram_id}: {e}")
        raise