from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
import sys
from apscheduler.schedulers.background import BackgroundScheduler

from gui.main_window import MainWindow
from gui.tray import TrayIcon
from database import init_db, get_all_subscriptions
from services.weather import get_weather_aggregated
from services.currency import get_currency_rates, CURRENCY_PAIRS
from services.crypto import get_crypto_rates, CRYPTO_COINS
from services.horoscope import get_horoscope, ZODIAC_SIGNS
from services.fact import get_random_fact
from services.quote import get_random_quote
from plyer import notification
import asyncio


class OnTimeBotApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)

        init_db()

        self.scheduler = BackgroundScheduler()

        self.main_window = MainWindow(self.scheduler)
        self.main_window.show_notification_signal.connect(self.show_windows_notification)

        self.tray = TrayIcon(self.main_window)

        self.restore_subscriptions()
        self.scheduler.start()

    def restore_subscriptions(self):
        from apscheduler.triggers.cron import CronTrigger

        subs = get_all_subscriptions()

        for sub in subs:
            param = sub.get('param', '')
            hours, minutes = map(int, sub['time'].split(':'))

            job_funcs = {
                "weather": self.main_window.send_weather,
                "currency": self.main_window.send_currency,
                "crypto": self.main_window.send_crypto,
                "horoscope": self.main_window.send_horoscope,
                "fact": self.main_window.send_fact,
                "quote": self.main_window.send_quote
            }

            func = job_funcs.get(sub['type'])
            if func:
                self.scheduler.add_job(
                    func,
                    CronTrigger(hour=hours, minute=minutes),
                    args=[param],
                    id=f"{sub['type']}_{sub['time']}",
                    replace_existing=True
                )

    def show_windows_notification(self, title, message):
        try:
            notification.notify(
                title=title,
                message=message[:200],
                app_name="OnTimeBot Desktop",
                timeout=10
            )
        except Exception as e:
            print(f"Notification error: {e}")

    def run(self):
        self.main_window.show()
        sys.exit(self.app.exec())


if __name__ == "__main__":
    app = OnTimeBotApp()
    app.run()