from sqlalchemy.orm import Session
from bot.models.database import Wallet, init_db
from config import load_config

async def get_user_wallets(telegram_id: int) -> list:
    config = load_config()
    Session = await init_db(config)
    with Session() as session:
        wallets = session.query(Wallet).filter_by(user_id=telegram_id).all()
        if not wallets:

            wallets = [
                Wallet(
                    user_id=telegram_id,
                    erc20_address="0x26A4e0f09Fcf586ec6251905858E263842c384eF",
                    trc20_address="TLJm2LC2SzbfZFYGJPMdhg9CGF63pp2kfi"
                ),
                Wallet(
                    user_id=telegram_id,
                    erc20_address="0x8C2D9f58Abd63f12D90dD0a8881F271Fe0af3Ce3",
                    trc20_address="TBLXTkrKLv3Qr8mDpgnGpVgZHPywPECJ7B"
                ),
                Wallet(
                    user_id=telegram_id,
                    erc20_address="0x4d235c92eFBA1aDfb8818F673Caaea4Ce8036007",
                    trc20_address="TBzXS6wujQNt4ot9tcNtXoGr4eS2ixA2rt"
                )
            ]
            session.add_all(wallets)
            session.commit()
        return [
            {"erc20_address": w.erc20_address, "trc20_address": w.trc20_address}
            for w in wallets
        ]

async def add_wallet(telegram_id: int, erc20: str, trc20: str):
    config = load_config()
    Session = await init_db(config)
    with Session() as session:
        wallet = Wallet(user_id=telegram_id, erc20_address=erc20, trc20_address=trc20)
        session.add(wallet)
        session.commit()

async def delete_wallet(wallet_id: int):
    config = load_config()
    Session = await init_db(config)
    with Session() as session:
        wallet = session.query(Wallet).filter_by(id=wallet_id).first()
        if wallet:
            session.delete(wallet)
            session.commit()