import aiohttp
from datetime import datetime

CURRENCY_PAIRS = [
    "USD/RUB", "EUR/RUB", "EUR/USD", "GBP/RUB", "CNY/RUB",
    "USD/EUR", "USD/GBP", "USD/CNY", "EUR/GBP", "GBP/USD"
]


async def get_currency_rates(pair: str):
    base, quote = pair.split("/")

    try:
        url = f"https://open.er-api.com/v6/latest/{base}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get("result") == "success":
                        rates = data.get("rates", {})
                        if quote in rates:
                            rate = rates[quote]
                            reverse_rate = 1 / rate if rate != 0 else 0

                            update_time = data.get('time_last_update_utc', '')
                            try:
                                dt = datetime.strptime(update_time, '%a, %d %b %Y %H:%M:%S %z')
                                time_str = dt.strftime('%H:%M')
                            except:
                                time_str = datetime.now().strftime('%H:%M')

                            result = f"1 {base} = {rate:.2f} {quote}\n"
                            result += f"1 {quote} = {reverse_rate:.3f} {base}\n"
                            result += f"🕒 Обновлено в {time_str}"
                            return result
    except:
        pass

    return f"1 {base} = — {quote}\n1 {quote} = — {base}"