import aiohttp
import random


async def get_random_quote():
    try:
        url = "https://api.quotable.io/random"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=5) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    content = data.get("content", "")
                    author = data.get("author", "Unknown")
                    if content:
                        return f"«{content}»\n— {author}"
    except:
        pass

    quotes = [
        ("«Будь собой, все остальные роли уже заняты.»", "Оскар Уайльд"),
        ("«Жизнь — это то, что происходит, пока ты строишь планы.»", "Джон Леннон"),
        ("«Лучшее время посадить дерево было 20 лет назад. Второе лучшее время — сейчас.»", "Китайская пословица"),
        ("«Всё, что вы можете себе представить, реально.»", "Пабло Пикассо"),
        ("«Будьте изменением, которое вы хотите видеть в мире.»", "Махатма Ганди"),
        ("«Не считай дни, пусть дни считаются.»", "Мухаммед Али"),
        ("«Лучший способ предсказать будущее — создать его.»", "Питер Друкер")
    ]

    quote, author = random.choice(quotes)
    return f"{quote}\n— {author}"