from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String(255))
    status = Column(String(50), default="pending") 
    referral = Column(String(255))
    registration_date = Column(DateTime, default=datetime.utcnow)
    name_age = Column(Text)
    experience = Column(Text)
    work_hours = Column(Text)
    transaction_knowledge = Column(Text)
    profit_total = Column(Float, default=0.0)
    profit_week = Column(Float, default=0.0)
    rank = Column(String(50), default="Freshman")
    
    utm_source = Column(String(255))  # UTM источник
    assigned_admin = Column(Integer)

    def __repr__(self):
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, username='{self.username}', status='{self.status}')>"

class UTMCode(Base):
    __tablename__ = "utm_codes"
    id = Column(Integer, primary_key=True, autoincrement=True)
    utm_code = Column(String(255), unique=True, nullable=False)
    assigned_admin = Column(Integer, nullable=False)
    created_by_user = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<UTMCode(utm_code='{self.utm_code}', assigned_admin={self.assigned_admin})>"


class Wallet(Base):
    __tablename__ = "wallets"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    erc20_address = Column(String(255))
    trc20_address = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Wallet(id={self.id}, user_id={self.user_id})>"

class Exchange(Base):
    __tablename__ = "exchanges"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    amount_btc = Column(Float, nullable=False)
    status = Column(String(50), default="pending") 
    admin_id = Column(Integer, nullable=True)
    assigned_admin = Column(Integer, nullable=True)  # Добавить это поле
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Exchange(id={self.id}, user_id={self.user_id}, amount_btc={self.amount_btc}, status='{self.status}')>"


# В файле database.py добавить после других моделей:
class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    manager_name = Column(String(255), nullable=False)
    payment_amount = Column(Float, nullable=False)
    manager_profit = Column(Float, nullable=False)
    tx_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Payment(id={self.id}, manager_name='{self.manager_name}', amount={self.payment_amount})>"
    


async def init_db(config):
    """Инициализация базы данных"""
    try:
        db_url = f"sqlite:///{config.db_path}"
        engine = create_engine(
            db_url, 
            echo=False,  
            pool_pre_ping=True,  
            connect_args={"check_same_thread": False}  
        )
        
        Base.metadata.create_all(engine)
        logger.info("База данных инициализирована успешно")
        
        Session = sessionmaker(bind=engine)
        return Session
        
    except Exception as e:
        logger.error(f"Ошибка инициализации базы данных: {e}")
        raise

def get_session(config):
    """Получение сессии базы данных (синхронная версия)"""
    try:
        db_url = f"sqlite:///{config.db_path}"
        engine = create_engine(
            db_url, 
            echo=False,
            pool_pre_ping=True,
            connect_args={"check_same_thread": False}
        )
        
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        return Session
        
    except Exception as e:
        logger.error(f"Ошибка получения сессии БД: {e}")
        raise
