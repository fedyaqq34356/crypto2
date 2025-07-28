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

async def get_top_week_teams() -> list:
    """Получение топа команд недели (по рефералам)"""
    try:
        config = load_config()
        Session = await init_db(config)
        
        with Session() as session:
           
            team_stats = (
                session.query(
                    User.referral,
                    func.sum(User.profit_week).label('total_profit'),
                    func.count(User.id).label('member_count')
                )
                .filter(User.status == "active")
                .filter(User.referral.isnot(None))
                .filter(User.referral != "")
                .filter(User.profit_week > 0)
                .group_by(User.referral)
                .order_by(desc('total_profit'))
                .limit(10)
                .all()
            )
            
            result = []
            for team in team_stats:
                result.append({
                    "team_name": team.referral,
                    "total_profit": int(team.total_profit) if team.total_profit else 0,
                    "member_count": team.member_count or 0
                })
                
            logger.info(f"Получен топ команд: {len(result)} команд")
            return result
            
    except Exception as e:
        logger.error(f"Ошибка при получении топа команд: {e}")
        return []

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