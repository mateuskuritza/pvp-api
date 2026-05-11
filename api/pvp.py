from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import requests
from bs4 import BeautifulSoup
import json
import re


class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        params = parse_qs(urlparse(self.path).query)
        ticker = params.get("ticker", [None])[0]

        if not ticker:
            return self._json(400, {"error": "Parametro ticker e obrigatorio"})

        ticker = ticker.upper().strip()

        try:
            pvp = self._scrape(ticker)
            self._json(200, {"ticker": ticker, "pvp": pvp})
        except Exception as e:
            self._json(500, {"error": str(e)})

    def _scrape(self, ticker):
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }

        paths = [
            "acoes/" + ticker.lower(),
            "fundos-imobiliarios/" + ticker.lower(),
        ]

        for path in paths:
            url = "https://statusinvest.com.br/" + path
            try:
                r = requests.get(url, headers=headers, timeout=10)
                if r.status_code != 200:
                    continue
                soup = BeautifulSoup(r.text, "html.parser")

                for div in soup.select("div.indicator-today-container"):
                    h3 = div.find("h3", class_="title")
                    if h3 and "P/VP" in h3.text:
                        strong = div.find("strong", class_="value")
                        if strong:
                            val = re.sub(r"[^\d,.]", "", strong.text).replace(",", ".")
                            return float(val)
            except Exception:
                continue

        raise ValueError("P/VP nao encontrado para " + ticker)

    def _json(self, status, body):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(body).encode())

    def log_message(self, format, *args):
        pass
