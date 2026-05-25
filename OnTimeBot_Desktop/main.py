import sys
import os

sys.path.append(os.path.dirname(__file__))

from app import OnTimeBotApp

if __name__ == "__main__":
    app = OnTimeBotApp()
    app.run()