from sqlalchemy.orm import Session
from bot.models.database import User, init_db
from config import load_config

async def validate_referral(referral: str) -> bool:
    config = load_config()
    Session = await init_db(config)
    with Session() as session:
        user = session.query(User).filter_by(username=referral).first()
        return user is not None

async def generate_invite_link(username: str) -> str:
    config = load_config()
    return f"https://t.me/CryptoBusinessTeamBot8888_bot?start={username}"