from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from bot.models.database import User, init_db
from config import load_config
import logging

logger = logging.getLogger(__name__)

async def get_top_week() -> list:
    """Получение реального топа недели из базы данных"""
    try:
        config = load_config()
        Session = await init_db(config)
        
        with Session() as session:
            
            top_users = (
                session.query(User)
                .filter(User.status == "active")  
                .filter(User.profit_week > 0)    
                .order_by(desc(User.profit_week))
                .limit(10) 
                .all()
            )
            
            result = []
            for user in top_users:
               
                profit_count = max(1, int(user.profit_week / 500)) if user.profit_week > 0 else 0
                
                result.append({
                    "username": user.username or f"User{user.telegram_id}",
                    "profit": int(user.profit_week) if user.profit_week else 0,
                    "count": profit_count
                })
            
            logger.info(f"Получен топ недели: {len(result)} пользователей")
            return result
            
    except Exception as e:
        logger.error(f"Ошибка при получении топа недели: {e}")
        
        return []



async def get_admin_workers_stats() -> dict:
    """Получение статистики работников для админа"""
    try:
        config = load_config()
        Session = await init_db(config)
        
        with Session() as session:
            # Получаем общую статистику пользователей
            total_users = session.query(User).count()
            active_users = session.query(User).filter(User.status == "active").count()
            
            # Получаем статистику по профиту
            total_profit = session.query(func.sum(User.profit_total)).scalar() or 0
            weekly_profit = session.query(func.sum(User.profit_week)).scalar() or 0
            
            # Получаем топ работников по недельному профиту
            top_workers = (
                session.query(User)
                .filter(User.status == "active")
                .filter(User.profit_week > 0)
                .order_by(desc(User.profit_week))
                .limit(5)
                .all()
            )
            
            # Получаем статистику по командам
            team_count = (
                session.query(User.referral)
                .filter(User.referral.isnot(None))
                .filter(User.referral != "")
                .distinct()
                .count()
            )
            
            result = {
                "total_users": total_users,
                "active_users": active_users,
                "total_profit": int(total_profit),
                "weekly_profit": int(weekly_profit),
                "team_count": team_count,
                "top_workers": [
                    {
                        "username": worker.username or f"User{worker.telegram_id}",
                        "profit_week": int(worker.profit_week) if worker.profit_week else 0,
                        "profit_total": int(worker.profit_total) if worker.profit_total else 0
                    }
                    for worker in top_workers
                ]
            }
            
            logger.info(f"Получена статистика для админа: {result}")
            return result
            
    except Exception as e:
        logger.error(f"Ошибка при получении статистики для админа: {e}")
        return {
            "total_users": 0,
            "active_users": 0,
            "total_profit": 0,
            "weekly_profit": 0,
            "team_count": 0,
            "top_workers": []
        }

async def add_test_data_for_top():
    """Добавление тестовых данных для демонстрации топа"""
    try:
        config = load_config()
        Session = await init_db(config)
        
        with Session() as session:
          
            users = session.query(User).filter(User.status == "active").limit(5).all()
            
            test_profits = [2500, 1800, 1200, 800, 400]
            
            for i, user in enumerate(users):
                if i < len(test_profits):
                    user.profit_week = test_profits[i]
                    user.profit_total = (user.profit_total or 0) + test_profits[i]
                    logger.info(f"Добавлен тестовый профит {test_profits[i]} пользователю {user.username}")
            
            session.commit()
            logger.info("Тестовые данные для топа добавлены")
            
    except Exception as e:
        logger.error(f"Ошибка при добавлении тестовых данных: {e}")
        raise

async def reset_weekly_stats():
    """Сброс недельной статистики"""
    try:
        config = load_config()
        Session = await init_db(config)
        
        with Session() as session:
            session.query(User).update({User.profit_week: 0.0})
            session.commit()
            logger.info("Недельная статистика сброшена")
            
    except Exception as e:
        logger.error(f"Ошибка при сбросе недельной статистики: {e}")
        raise
