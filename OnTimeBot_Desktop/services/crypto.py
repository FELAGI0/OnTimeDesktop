import aiohttp

CRYPTO_COINS = {
    "bitcoin": "Bitcoin (BTC)",
    "ethereum": "Ethereum (ETH)",
    "toncoin": "Toncoin (TON)",
    "solana": "Solana (SOL)",
    "ripple": "Ripple (XRP)",
    "cardano": "Cardano (ADA)",
    "dogecoin": "Dogecoin (DOGE)",
    "polkadot": "Polkadot (DOT)",
    "litecoin": "Litecoin (LTC)",
    "binancecoin": "BNB"
}


async def get_crypto_rates(coin: str):
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin}&vs_currencies=usd,rub&include_24hr_change=true"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if coin in data:
                        coin_data = data[coin]
                        result = ""

                        if "usd" in coin_data:
                            result += f"💵 ${coin_data['usd']:,.2f}\n"
                        if "rub" in coin_data:
                            result += f"💰 {coin_data['rub']:,.2f} ₽\n"
                        if "usd_24h_change" in coin_data:
                            change = coin_data['usd_24h_change']
                            emoji = "📈" if change > 0 else "📉"
                            result += f"{emoji} Изм. 24ч: {change:.2f}%"

                        return result
    except:
        pass

    return "Не удалось получить курс"