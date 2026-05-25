import aiohttp
import asyncio
from datetime import datetime
from config import WEATHER_API_KEY

CITY_COORDS_CACHE = {}


async def get_city_coordinates(city: str):
    if city in CITY_COORDS_CACHE:
        return CITY_COORDS_CACHE[city]

    url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=ru&format=json"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("results"):
                        coords = (data["results"][0]["latitude"], data["results"][0]["longitude"])
                        CITY_COORDS_CACHE[city] = coords
                        return coords
    except:
        pass
    return None


async def get_weather_aggregated(city: str):
    coords = await get_city_coordinates(city)
    if not coords:
        return None

    lat, lon = coords

    async def get_openmeteo():
        try:
            url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m&timezone=auto&forecast_days=1"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("hourly", {})
        except:
            pass
        return None

    async def get_openweather():
        try:
            url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={WEATHER_API_KEY}&units=metric&lang=ru"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("list", [])
        except:
            pass
        return None

    openmeteo_data, openweather_data = await asyncio.gather(get_openmeteo(), get_openweather())

    time_slots = [
        ("🌅 Утро", 8),
        ("☀️ День", 14),
        ("🌆 Вечер", 20),
        ("🌙 Ночь", 2)
    ]

    today = datetime.now().strftime('%Y-%m-%d')

    weather_text = f"🌤 {city}\n\n"

    if openmeteo_data:
        times = openmeteo_data.get("time", [])
        temps = openmeteo_data.get("temperature_2m", [])
        humidities = openmeteo_data.get("relative_humidity_2m", [])
        winds = openmeteo_data.get("wind_speed_10m", [])
        codes = openmeteo_data.get("weather_code", [])

        for slot_name, hour in time_slots:
            target_time = f"{today}T{hour:02d}:00"
            try:
                idx = times.index(target_time)
                temp = temps[idx]
                humidity = humidities[idx]
                wind = winds[idx]
                code = codes[idx]
                desc = interpret_openmeteo_code(code)
                weather_text += f"{slot_name} · {temp:.0f}°C\n{desc} · Влажность {humidity}% · Ветер {wind} м/с\n\n"
            except ValueError:
                weather_text += f"{slot_name} · —\nНет данных\n\n"

    elif openweather_data:
        for slot_name, hour in time_slots:
            closest = None
            min_diff = float('inf')
            for item in openweather_data:
                item_hour = int(item['dt_txt'].split()[1].split(':')[0])
                diff = abs(item_hour - hour)
                if diff < min_diff:
                    min_diff = diff
                    closest = item

            if closest:
                temp = closest['main']['temp']
                humidity = closest['main']['humidity']
                wind = closest['wind']['speed']
                desc = closest['weather'][0]['description'].capitalize()
                weather_text += f"{slot_name} · {temp:.0f}°C\n{desc} · Влажность {humidity}% · Ветер {wind} м/с\n\n"
            else:
                weather_text += f"{slot_name} · —\nНет данных\n\n"
    else:
        return None

    return weather_text.strip()


def interpret_openmeteo_code(code: int) -> str:
    weather_map = {
        0: "Ясно", 1: "Преимущественно ясно", 2: "Переменная облачность",
        3: "Пасмурно", 45: "Туман", 48: "Иней",
        51: "Лёгкая морось", 53: "Морось", 55: "Сильная морось",
        61: "Небольшой дождь", 63: "Дождь", 65: "Сильный дождь",
        71: "Небольшой снег", 73: "Снег", 75: "Сильный снег",
        80: "Ливень", 81: "Сильный ливень", 82: "Очень сильный ливень",
        95: "Гроза", 96: "Гроза с градом", 99: "Сильная гроза с градом"
    }
    return weather_map.get(code, "Неизвестно")