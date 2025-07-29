import os
from dataclasses import dataclass, field
from typing import List



@dataclass
class Config:
    # Основные настройки бота
    bot_token: str
    admin_ids: List[int]
    admin_group: int  # ID группы админов
    admin_group_url: str  # URL группы админов
    
    # Каналы и чаты
    main_channel: str  # URL основного канала
    payment_channel: int  # ID канала выплат
    payment_channel_url: str  # URL канала выплат
    team_chat: str  # URL чата команды (если нужен)
    
    # Мануалы и инструкции
    electrum_manual: str  # URL мануала Electrum
    bluewallet_manual: str  # URL мануала Bluewallet
    manager_manual: str  # URL инструкций для менеджера
    
    require_utm: bool = True  # Обязательный UTM для регистрации
    
    utm_admin_mapping: dict = field(default_factory=lambda: {
        "admin1": 396862984,  
        # Добавьте реальные ID ваших админов
    })
    # Добавьте свои маппинги
    
    # База данных
    db_path: str = "bot.db"

def load_config() -> Config:
    """Загрузка конфигурации из переменных окружения"""
    return Config(
        bot_token=os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN"),
        admin_ids=[int(x) for x in os.getenv("ADMIN_IDS", "123456789").split(",")],
        admin_group=int(os.getenv("ADMIN_GROUP", "-1001234567890")),
        admin_group_url=os.getenv("ADMIN_GROUP_URL", "https://t.me/your_admin_group"),
        
        main_channel=os.getenv("MAIN_CHANNEL", "https://t.me/your_main_channel"),
        payment_channel=int(os.getenv("PAYMENT_CHANNEL", "-1001234567891")),
        payment_channel_url=os.getenv("PAYMENT_CHANNEL_URL", "https://t.me/your_payment_channel"),
        team_chat=os.getenv("TEAM_CHAT", "https://t.me/your_team_chat"),
        
        electrum_manual=os.getenv("ELECTRUM_MANUAL", "https://example.com/electrum"),
        bluewallet_manual=os.getenv("BLUEWALLET_MANUAL", "https://example.com/bluewallet"),
        manager_manual=os.getenv("MANAGER_MANUAL", "https://example.com/manager"),
        
        db_path=os.getenv("DB_PATH", "bot.db")
    )
