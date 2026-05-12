import threading
import requests
from datetime import datetime

QUOTES_CACHE: dict = {}
LAST_UPDATE: str = ""


def fetch_quotes(callback=None):
    def _run():
        global QUOTES_CACHE, LAST_UPDATE
        try:
            url = ("https://economia.awesomeapi.com.br"
                   "/json/last/USD-BRL,EUR-BRL,BTC-BRL")
            r = requests.get(url, timeout=6)
            data = r.json()
            QUOTES_CACHE = {
                "USD": float(data["USDBRL"]["bid"]),
                "EUR": float(data["EURBRL"]["bid"]),
                "BTC": float(data["BTCBRL"]["bid"]),
            }
            LAST_UPDATE = datetime.now().strftime("%H:%M")
        except Exception as e:
            print(f"[quotes] {e}")
        if callback:
            callback(QUOTES_CACHE, LAST_UPDATE)

    threading.Thread(target=_run, daemon=True).start()