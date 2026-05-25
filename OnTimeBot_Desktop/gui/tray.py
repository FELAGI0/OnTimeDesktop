from PyQt6.QtWidgets import QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import QCoreApplication
import os


class TrayIcon(QSystemTrayIcon):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

        icon_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'icon.ico')
        if os.path.exists(icon_path):
            self.setIcon(QIcon(icon_path))
        else:
            self.setIcon(QIcon.fromTheme("appointment-soon"))

        self.setToolTip("OnTimeBot Desktop")

        menu = QMenu()

        show_action = QAction("Открыть")
        show_action.triggered.connect(self.show_window)
        menu.addAction(show_action)

        menu.addSeparator()

        quit_action = QAction("Выход")
        quit_action.triggered.connect(self.quit_app)
        menu.addAction(quit_action)

        self.setContextMenu(menu)
        self.activated.connect(self.on_tray_activated)

        self.show()

    def show_window(self):
        self.main_window.show()
        self.main_window.raise_()
        self.main_window.activateWindow()

    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_window()

    def quit_app(self):
        self.main_window.scheduler.shutdown()
        QCoreApplication.quit()