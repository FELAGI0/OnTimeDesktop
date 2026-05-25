from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QComboBox, QTimeEdit,
    QTextEdit, QSystemTrayIcon, QMenu
)
from PyQt6.QtCore import Qt, QTime, pyqtSignal
from PyQt6.QtGui import QIcon, QAction
import asyncio
from datetime import datetime

from database import save_subscription, delete_subscription, get_all_subscriptions
from services.weather import get_weather_aggregated
from services.currency import get_currency_rates, CURRENCY_PAIRS
from services.crypto import get_crypto_rates, CRYPTO_COINS
from services.horoscope import get_horoscope, ZODIAC_SIGNS
from services.fact import get_random_fact
from services.quote import get_random_quote


class MainWindow(QMainWindow):
    show_notification_signal = pyqtSignal(str, str)

    def __init__(self, scheduler):
        super().__init__()
        self.scheduler = scheduler
        self.init_ui()
        self.load_subscriptions()

    def init_ui(self):
        self.setWindowTitle("OnTimeBot Desktop")
        self.setFixedSize(500, 450)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()

        title = QLabel("⏰ OnTimeBot Desktop")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)

        self.category_combo = QComboBox()
        self.category_combo.addItems([
            "🌤️ Погода",
            "💱 Валюты",
            "₿ Крипта",
            "🔮 Гороскоп",
            "📚 Факты",
            "📝 Цитаты"
        ])
        self.category_combo.currentTextChanged.connect(self.on_category_changed)
        layout.addWidget(self.category_combo)

        self.param_combo = QComboBox()
        layout.addWidget(self.param_combo)

        time_layout = QHBoxLayout()
        time_layout.addWidget(QLabel("Время отправки:"))
        self.time_edit = QTimeEdit()
        self.time_edit.setTime(QTime(8, 0))
        self.time_edit.setDisplayFormat("HH:mm")
        time_layout.addWidget(self.time_edit)
        layout.addLayout(time_layout)

        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("✅ Добавить")
        self.add_btn.clicked.connect(self.add_subscription)
        btn_layout.addWidget(self.add_btn)

        self.remove_btn = QPushButton("❌ Удалить")
        self.remove_btn.clicked.connect(self.remove_subscription)
        btn_layout.addWidget(self.remove_btn)
        layout.addLayout(btn_layout)

        self.preview_btn = QPushButton("👁 Показать сейчас")
        self.preview_btn.clicked.connect(self.show_preview)
        layout.addWidget(self.preview_btn)

        layout.addWidget(QLabel("Активные уведомления:"))
        self.subs_text = QTextEdit()
        self.subs_text.setReadOnly(True)
        self.subs_text.setMaximumHeight(150)
        layout.addWidget(self.subs_text)

        self.status_label = QLabel("Статус: Готов")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: gray;")
        layout.addWidget(self.status_label)

        central_widget.setLayout(layout)

        self.on_category_changed(self.category_combo.currentText())

    def on_category_changed(self, category):
        self.param_combo.clear()

        if category == "🌤️ Погода":
            self.param_combo.setEditable(True)
            self.param_combo.addItems(["Москва", "Санкт-Петербург", "Губкин", "London", "New York"])
        elif category == "💱 Валюты":
            self.param_combo.setEditable(False)
            self.param_combo.addItems(CURRENCY_PAIRS)
        elif category == "₿ Крипта":
            self.param_combo.setEditable(False)
            self.param_combo.addItems(list(CRYPTO_COINS.values()))
        elif category == "🔮 Гороскоп":
            self.param_combo.setEditable(False)
            self.param_combo.addItems(list(ZODIAC_SIGNS.values()))
        elif category == "📚 Факты":
            self.param_combo.setEditable(False)
            self.param_combo.addItems(["Случайная", "Наука", "История", "Космос", "Технологии", "Животные", "Человек"])
        elif category == "📝 Цитаты":
            self.param_combo.setEditable(False)
            self.param_combo.addItems(["Случайные"])

    def add_subscription(self):
        category = self.category_combo.currentText()
        param = self.param_combo.currentText()
        time = self.time_edit.time().toString("HH:mm")

        sub_type_map = {
            "🌤️ Погода": "weather",
            "💱 Валюты": "currency",
            "₿ Крипта": "crypto",
            "🔮 Гороскоп": "horoscope",
            "📚 Факты": "fact",
            "📝 Цитаты": "quote"
        }

        sub_type = sub_type_map[category]

        if sub_type == "currency":
            for pair in CURRENCY_PAIRS:
                if param in pair:
                    param = pair
                    break
        elif sub_type == "crypto":
            for key, value in CRYPTO_COINS.items():
                if value == param:
                    param = key
                    break
        elif sub_type == "horoscope":
            for key, value in ZODIAC_SIGNS.items():
                if value == param:
                    param = key
                    break
        elif sub_type == "fact":
            cat_map = {
                "Случайная": "random",
                "Наука": "science",
                "История": "history",
                "Космос": "space",
                "Технологии": "technology",
                "Животные": "animals",
                "Человек": "human"
            }
            param = cat_map.get(param, "random")

        save_subscription(sub_type, {'param': param}, time)
        self.add_scheduler_job(sub_type, param, time)
        self.load_subscriptions()
        self.status_label.setText(f"✅ Добавлено: {category} в {time}")

    def remove_subscription(self):
        category = self.category_combo.currentText()
        time = self.time_edit.time().toString("HH:mm")

        sub_type_map = {
            "🌤️ Погода": "weather",
            "💱 Валюты": "currency",
            "₿ Крипта": "crypto",
            "🔮 Гороскоп": "horoscope",
            "📚 Факты": "fact",
            "📝 Цитаты": "quote"
        }

        sub_type = sub_type_map[category]
        delete_subscription(sub_type, time)
        self.load_subscriptions()
        self.status_label.setText(f"❌ Удалено: {category} в {time}")

    def add_scheduler_job(self, sub_type, param, time_str):
        hours, minutes = map(int, time_str.split(':'))

        job_funcs = {
            "weather": self.send_weather,
            "currency": self.send_currency,
            "crypto": self.send_crypto,
            "horoscope": self.send_horoscope,
            "fact": self.send_fact,
            "quote": self.send_quote
        }

        func = job_funcs.get(sub_type)
        if func:
            from apscheduler.triggers.cron import CronTrigger
            self.scheduler.add_job(
                func,
                CronTrigger(hour=hours, minute=minutes),
                args=[param],
                id=f"{sub_type}_{time_str}",
                replace_existing=True
            )

    def send_weather(self, city):
        try:
            result = asyncio.run(get_weather_aggregated(city))
            if result:
                self.show_notification_signal.emit("🌤️ Погода", result)
        except Exception as e:
            print(f"Error: {e}")

    def send_currency(self, pair):
        try:
            result = asyncio.run(get_currency_rates(pair))
            self.show_notification_signal.emit(f"💱 {pair}", result)
        except Exception as e:
            print(f"Error: {e}")

    def send_crypto(self, coin):
        try:
            result = asyncio.run(get_crypto_rates(coin))
            name = CRYPTO_COINS.get(coin, coin)
            self.show_notification_signal.emit(f"₿ {name}", result)
        except Exception as e:
            print(f"Error: {e}")

    def send_horoscope(self, sign):
        try:
            result = asyncio.run(get_horoscope(sign))
            name = ZODIAC_SIGNS.get(sign, sign)
            self.show_notification_signal.emit(f"🔮 {name}", result)
        except Exception as e:
            print(f"Error: {e}")

    def send_fact(self, category):
        try:
            result = asyncio.run(get_random_fact(category if category != "random" else None))
            self.show_notification_signal.emit("📚 Факт дня", result)
        except Exception as e:
            print(f"Error: {e}")

    def send_quote(self, _=None):
        try:
            result = asyncio.run(get_random_quote())
            self.show_notification_signal.emit("📝 Цитата дня", result)
        except Exception as e:
            print(f"Error: {e}")

    def show_preview(self):
        category = self.category_combo.currentText()

        if category == "🌤️ Погода":
            city = self.param_combo.currentText()
            result = asyncio.run(get_weather_aggregated(city))
            if result:
                self.show_notification_signal.emit("🌤️ Погода", result)
        elif category == "💱 Валюты":
            pair = self.param_combo.currentText()
            for p in CURRENCY_PAIRS:
                if pair in p:
                    pair = p
                    break
            result = asyncio.run(get_currency_rates(pair))
            self.show_notification_signal.emit(f"💱 {pair}", result)
        elif category == "₿ Крипта":
            coin_name = self.param_combo.currentText()
            coin_key = None
            for key, value in CRYPTO_COINS.items():
                if value == coin_name:
                    coin_key = key
                    break
            if coin_key:
                result = asyncio.run(get_crypto_rates(coin_key))
                self.show_notification_signal.emit(f"₿ {coin_name}", result)
        elif category == "🔮 Гороскоп":
            sign_name = self.param_combo.currentText()
            sign_key = None
            for key, value in ZODIAC_SIGNS.items():
                if value == sign_name:
                    sign_key = key
                    break
            if sign_key:
                result = asyncio.run(get_horoscope(sign_key))
                self.show_notification_signal.emit(f"🔮 {sign_name}", result)
        elif category == "📚 Факты":
            cat_map = {"Случайная": "random", "Наука": "science", "История": "history"}
            cat = cat_map.get(self.param_combo.currentText(), "random")
            result = asyncio.run(get_random_fact(cat if cat != "random" else None))
            self.show_notification_signal.emit("📚 Факт дня", result)
        elif category == "📝 Цитаты":
            result = asyncio.run(get_random_quote())
            self.show_notification_signal.emit("📝 Цитата дня", result)

    def load_subscriptions(self):
        subs = get_all_subscriptions()

        type_names = {
            "weather": "🌤️ Погода",
            "currency": "💱 Валюты",
            "crypto": "₿ Крипта",
            "horoscope": "🔮 Гороскоп",
            "fact": "📚 Факты",
            "quote": "📝 Цитаты"
        }

        text = ""
        for sub in subs:
            name = type_names.get(sub['type'], sub['type'])
            param = sub.get('param', '')

            if sub['type'] == 'crypto':
                param = CRYPTO_COINS.get(param, param)
            elif sub['type'] == 'horoscope':
                param = ZODIAC_SIGNS.get(param, param)

            text += f"• {name} — {param} — {sub['time']}\n"

        if not text:
            text = "Нет активных уведомлений"

        self.subs_text.setText(text)

    def closeEvent(self, event):
        event.ignore()
        self.hide()