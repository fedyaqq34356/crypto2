def format_rules() -> str:
    return (
        "⛔ Размещение 18+ медиа любого формата — БАН.\n"
        "⛔ Реклама других проектов/услуг без согласования с администрацией — БАН.\n"
        "⛔ Попрошайничество — мут на сутки.\n"
        "⛔ Срачи на политические темы — БАН моментально.\n"
        "⛔ Саботировать/подставлять/провоцировать других участников — БАН.\n"
        "⛔ Прием платежей на свои кошельки — БАН."
    )

def format_stats(stats: dict) -> str:
    ranks = {
        "Freshman": (0, 2000),
        "Grinder": (2000, 5000),
        "Rank3": (5000, 10000),
        "Rank4": (10000, 20000),
        "Rank5": (20000, float("inf"))
    }
    current_rank = stats["rank"]
    next_rank = next((r for r, (low, high) in ranks.items() if low > stats["profit_total"]), "Rank5")
    to_next = ranks[next_rank][0] - stats["profit_total"] if next_rank != "Rank5" else 0
    return (
        f"Профит за все время: {stats['profit_total']}$\n"
        f"Профит за неделю: {stats['profit_week']}$\n"
        f"Текущий ранг: {current_rank}\n"
        f"До звания {next_rank} осталось {to_next}$\n"
        f"Недельная выплата: {stats['profit_week']}$"
    )

def format_wallets(wallets: list) -> str:
    if not wallets:
        return "Кошельки не найдены. Обратитесь к администратору."
    
    result = "Кошельки для пополнений\n\n"
    for i, wallet in enumerate(wallets, 1):
        result += (
            f"Связка #{i}\n"
            f"ERC20: `{wallet['erc20_address']}`\n"
            f"TRC20: `{wallet['trc20_address']}`\n\n"
        )
    result += (
        "!! ВАЖНО:\n"
        "Ethereum адреса выдаем для всех EVM-совместимых сетей (Ethereum, BSC, Polygon, Avalanche, Base, Arbitrum, Optimism и т.д.)\n"
        "!! Используйте только эти адреса для получения платежей в нашей команде"
    )
    return result

def format_top_week(top: list) -> str:
    """Форматирование топа недели по людям"""
    if not top:
        return "Топ недели пуст.\nНикто еще не заработал профит на этой неделе.\n\nДля добавления тестовых данных используйте команду /add_test_data"
    
    result = "Топ недели по людям:\n\n"
    for i, entry in enumerate(top, 1):
        username = entry['username'] if entry['username'] and entry['username'] != 'None' else f"Воркер{i}"
        profit = entry['profit']
        count = entry['count']
        result += f"{i}. **{username}**, Total: **{profit}$** | профитов: {count}\n"
    return result

