import aiohttp
import random


async def get_random_fact(category: str = None):
    try:
        url = "https://randstuff.ru/fact/generate/"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    fact = data.get("fact", {}).get("text", "")
                    if fact:
                        return fact
    except:
        pass

    facts = [
        "Вода может кипеть и замерзать одновременно при определённом давлении.",
        "Свет от Солнца до Земли идёт около 8 минут 20 секунд.",
        "Самая короткая война в истории длилась 38 минут.",
        "На Венере день длится дольше, чем год.",
        "Осьминоги имеют три сердца и голубую кровь.",
        "Первый компьютерный вирус был создан в 1983 году.",
        "Человек — единственное животное, которое краснеет.",
        "Слоны — единственные животные, которые не могут прыгать.",
        "Ваш нос может различать более триллиона запахов.",
        "Улитки могут спать до трёх лет."
    ]

    return random.choice(facts)