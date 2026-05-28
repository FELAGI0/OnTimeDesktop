from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QComboBox, QTimeEdit,
    QFrame, QLineEdit, QScrollArea
)
from PyQt6.QtCore import Qt, QTime, pyqtSignal
from PyQt6.QtGui import QFont
import asyncio

from database import save_subscription, delete_subscription, get_all_subscriptions
from services.weather import get_weather_aggregated
from services.currency import get_currency_rates, CURRENCY_PAIRS
from services.crypto import get_crypto_rates, CRYPTO_COINS
from services.horoscope import get_horoscope, ZODIAC_SIGNS
from services.fact import get_random_fact
from services.quote import get_random_quote

STYLE = """
* {
    font-family: "Segoe UI";
}
QMainWindow {
    background: #1a1a1a;
}
QLabel {
    color: #e0e0e0;
    background: transparent;
    border: none;
}
QComboBox {
    background: #2a2a2a;
    color: #e0e0e0;
    border: none;
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 13px;
    min-height: 20px;
}
QComboBox:hover {
    background: #333;
}
QComboBox::drop-down {
    border: none;
    width: 20px;
}
QComboBox QAbstractItemView {
    background: #2a2a2a;
    color: #e0e0e0;
    border: none;
    border-radius: 4px;
    selection-background-color: #3a3a3a;
}
QLineEdit {
    background: #2a2a2a;
    color: #e0e0e0;
    border: none;
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 13px;
    min-height: 20px;
}
QLineEdit:focus {
    background: #333;
}
QTimeEdit {
    background: #2a2a2a;
    color: #e0e0e0;
    border: none;
    border-radius: 6px;
    padding: 4px 8px;
    font-size: 13px;
    min-height: 20px;
}
QTimeEdit:hover {
    background: #333;
}
QTimeEdit::up-button {
    border: none;
    width: 16px;
    border-radius: 3px;
}
QTimeEdit::down-button {
    border: none;
    width: 16px;
    border-radius: 3px;
}
QTimeEdit::up-button:hover, QTimeEdit::down-button:hover {
    background: #444;
}
QScrollArea {
    border: none;
    background: transparent;
}
QScrollBar:vertical {
    background: #1a1a1a;
    width: 6px;
}
QScrollBar::handle:vertical {
    background: #3a3a3a;
    border-radius: 3px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background: #4a4a4a;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
"""


class NotifCard(QFrame):
    delete_clicked = pyqtSignal(str, str)

    def __init__(self, icon, title, subtitle, time_str, sub_type):
        super().__init__()
        self.setObjectName("card")
        self.setStyleSheet("""
            QFrame#card {
                background: #222;
                border: none;
                border-radius: 8px;
            }
            QFrame#card:hover {
                background: #282828;
            }
        """)
        self.setFixedHeight(56)

        layout = QHBoxLayout()
        layout.setContentsMargins(14, 8, 14, 8)
        layout.setSpacing(10)

        icon_label = QLabel(icon)
        icon_label.setFont(QFont("Segoe UI", 18))
        layout.addWidget(icon_label)

        info = QVBoxLayout()
        info.setSpacing(1)

        title_label = QLabel(title)
        title_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        info.addWidget(title_label)

        sub_label = QLabel(subtitle)
        sub_label.setFont(QFont("Segoe UI", 9))
        sub_label.setStyleSheet("color: #999;")
        info.addWidget(sub_label)

        layout.addLayout(info)
        layout.addStretch()

        time_label = QLabel(time_str)
        time_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        time_label.setStyleSheet("color: #5B8CFF;")
        layout.addWidget(time_label)

        del_btn = QPushButton("✕")
        del_btn.setFixedSize(26, 26)
        del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        del_btn.setStyleSheet("""
            QPushButton {
                background: #2a1515;
                color: #ff5555;
                border: none;
                border-radius: 5px;
                font-size: 12px;
            }
            QPushButton:hover {
                background: #3a1a1a;
            }
        """)
        del_btn.clicked.connect(lambda: self.delete_clicked.emit(sub_type, time_str))
        layout.addWidget(del_btn)

        self.setLayout(layout)


class MainWindow(QMainWindow):
    show_notification_signal = pyqtSignal(str, str)

    def __init__(self, scheduler):
        super().__init__()
        self.scheduler = scheduler
        self.setStyleSheet(STYLE)
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("OnTimeBot")
        self.setMinimumSize(660, 520)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(16)

        title = QLabel("OnTimeBot")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        main_layout.addWidget(title)

        section_label = QLabel("Новое уведомление")
        section_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        section_label.setStyleSheet("color: #999;")
        main_layout.addWidget(section_label)

        form_layout = QHBoxLayout()
        form_layout.setSpacing(8)

        self.type_combo = QComboBox()
        self.type_combo.addItems(["Погода", "Валюты", "Крипта", "Гороскоп", "Факты", "Цитаты"])
        self.type_combo.currentTextChanged.connect(self.on_type_changed)
        form_layout.addWidget(self.type_combo)

        self.param_input = QLineEdit()
        self.param_input.setPlaceholderText("Город")
        form_layout.addWidget(self.param_input)

        self.param_combo = QComboBox()
        self.param_combo.hide()
        form_layout.addWidget(self.param_combo)

        self.time_edit = QTimeEdit()
        self.time_edit.setTime(QTime(8, 0))
        self.time_edit.setDisplayFormat("HH:mm")
        form_layout.addWidget(self.time_edit)

        add_btn = QPushButton("Добавить")
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.setStyleSheet("""
            QPushButton {
                background: #5B8CFF;
                color: #fff;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 12px;
                min-height: 20px;
            }
            QPushButton:hover {
                background: #4B7CEF;
            }
        """)
        add_btn.clicked.connect(self.add_subscription)
        form_layout.addWidget(add_btn)

        preview_btn = QPushButton("Показать")
        preview_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        preview_btn.setStyleSheet("""
            QPushButton {
                background: #2a2a2a;
                color: #aaa;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 12px;
                min-height: 20px;
            }
            QPushButton:hover {
                background: #333;
                color: #fff;
            }
        """)
        preview_btn.clicked.connect(self.show_preview)
        form_layout.addWidget(preview_btn)

        main_layout.addLayout(form_layout)

        sep = QFrame()
        sep.setStyleSheet("background: #2a2a2a;")
        sep.setFixedHeight(1)
        main_layout.addWidget(sep)

        list_title = QLabel("Уведомления")
        list_title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        list_title.setStyleSheet("color: #999;")
        main_layout.addWidget(list_title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        self.notif_widget = QWidget()
        self.notif_layout = QVBoxLayout()
        self.notif_layout.setSpacing(6)
        self.notif_layout.addStretch()
        self.notif_widget.setLayout(self.notif_layout)

        scroll.setWidget(self.notif_widget)
        main_layout.addWidget(scroll, stretch=1)

        central.setLayout(main_layout)

        self.on_type_changed("Погода")

    def on_type_changed(self, cat):
        if cat in ["Валюты", "Крипта", "Гороскоп", "Факты", "Цитаты"]:
            self.param_input.hide()
            self.param_combo.show()
            self.param_combo.clear()
            if cat == "Валюты":
                self.param_combo.addItems(CURRENCY_PAIRS)
            elif cat == "Крипта":
                self.param_combo.addItems(list(CRYPTO_COINS.values()))
            elif cat == "Гороскоп":
                self.param_combo.addItems(list(ZODIAC_SIGNS.values()))
            elif cat == "Факты":
                self.param_combo.addItems(
                    ["Случайная", "Наука", "История", "Космос", "Технологии", "Животные", "Человек"])
            elif cat == "Цитаты":
                self.param_combo.addItems(["Случайные"])
        else:
            self.param_combo.hide()
            self.param_input.show()

    def get_param(self):
        if self.type_combo.currentText() == "Погода":
            return self.param_input.text().strip()
        return self.param_combo.currentText()

    def add_subscription(self):
        cat = self.type_combo.currentText()
        param = self.get_param()
        time = self.time_edit.time().toString("HH:mm")
        if not param: return

        smap = {"Погода": "weather", "Валюты": "currency", "Крипта": "crypto", "Гороскоп": "horoscope", "Факты": "fact",
                "Цитаты": "quote"}
        st = smap[cat]

        if st == "crypto":
            for k, v in CRYPTO_COINS.items():
                if v == param: param = k; break
        elif st == "horoscope":
            for k, v in ZODIAC_SIGNS.items():
                if v == param: param = k; break
        elif st == "fact":
            cm = {"Случайная": "random", "Наука": "science", "История": "history", "Космос": "space",
                  "Технологии": "technology", "Животные": "animals", "Человек": "human"}
            param = cm.get(param, "random")

        save_subscription(st, {'param': param}, time)
        self._add_job(st, param, time)
        self.load_subscriptions()

    def remove_subscription(self, st, time):
        delete_subscription(st, time)
        self.load_subscriptions()

    def _add_job(self, st, param, time):
        from apscheduler.triggers.cron import CronTrigger
        funcs = {
            "weather": self.send_weather, "currency": self.send_currency,
            "crypto": self.send_crypto, "horoscope": self.send_horoscope,
            "fact": self.send_fact, "quote": self.send_quote
        }
        h, m = map(int, time.split(':'))
        f = funcs.get(st)
        if f:
            self.scheduler.add_job(f, CronTrigger(hour=h, minute=m), args=[param], id=f"{st}_{time}",
                                   replace_existing=True)

    def send_weather(self, city):
        r = asyncio.run(get_weather_aggregated(city))
        if r: self.show_notification_signal.emit("Погода", r)

    def send_currency(self, pair):
        r = asyncio.run(get_currency_rates(pair))
        self.show_notification_signal.emit(f"Курс {pair}", r)

    def send_crypto(self, coin):
        r = asyncio.run(get_crypto_rates(coin))
        self.show_notification_signal.emit(f"Крипта {CRYPTO_COINS.get(coin, coin)}", r)

    def send_horoscope(self, sign):
        r = asyncio.run(get_horoscope(sign))
        self.show_notification_signal.emit(f"Гороскоп {ZODIAC_SIGNS.get(sign, sign)}", r)

    def send_fact(self, cat):
        r = asyncio.run(get_random_fact(cat if cat != "random" else None))
        self.show_notification_signal.emit("Факт дня", r)

    def send_quote(self, _=None):
        r = asyncio.run(get_random_quote())
        self.show_notification_signal.emit("Цитата дня", r)

    def show_preview(self):
        cat = self.type_combo.currentText()
        param = self.get_param()
        if not param: return

        if cat == "Погода":
            r = asyncio.run(get_weather_aggregated(param))
            if r: self.show_notification_signal.emit("Погода", r)
        elif cat == "Валюты":
            r = asyncio.run(get_currency_rates(param))
            self.show_notification_signal.emit(f"Курс {param}", r)
        elif cat == "Крипта":
            for k, v in CRYPTO_COINS.items():
                if v == param:
                    r = asyncio.run(get_crypto_rates(k))
                    self.show_notification_signal.emit(f"Крипта {v}", r)
                    break
        elif cat == "Гороскоп":
            for k, v in ZODIAC_SIGNS.items():
                if v == param:
                    r = asyncio.run(get_horoscope(k))
                    self.show_notification_signal.emit(f"Гороскоп {v}", r)
                    break
        elif cat == "Факты":
            cm = {"Случайная": "random", "Наука": "science", "История": "history", "Космос": "space",
                  "Технологии": "technology", "Животные": "animals", "Человек": "human"}
            c = cm.get(param, "random")
            r = asyncio.run(get_random_fact(c if c != "random" else None))
            self.show_notification_signal.emit("Факт дня", r)
        elif cat == "Цитаты":
            r = asyncio.run(get_random_quote())
            self.show_notification_signal.emit("Цитата дня", r)

    def load_subscriptions(self):
        for i in reversed(range(self.notif_layout.count())):
            w = self.notif_layout.itemAt(i).widget()
            if w:
                w.setParent(None)
                w.deleteLater()

        subs = get_all_subscriptions()
        icons = {"weather": "🌤", "currency": "💱", "crypto": "₿", "horoscope": "🔮", "fact": "📚", "quote": "📝"}
        names = {"weather": "Погода", "currency": "Валюты", "crypto": "Крипта", "horoscope": "Гороскоп",
                 "fact": "Факты", "quote": "Цитаты"}

        for sub in subs:
            icon = icons.get(sub['type'], "")
            name = names.get(sub['type'], sub['type'])
            param = sub.get('param', '')

            if sub['type'] == 'crypto':
                param = CRYPTO_COINS.get(param, param)
            elif sub['type'] == 'horoscope':
                param = ZODIAC_SIGNS.get(param, param)

            card = NotifCard(icon, name, param, sub['time'], sub['type'])
            card.delete_clicked.connect(self.remove_subscription)
            self.notif_layout.insertWidget(self.notif_layout.count() - 1, card)

    def closeEvent(self, event):
        event.ignore()
        self.hide()