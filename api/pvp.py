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
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9",
        }
        paths = ["fundos-imobiliarios/" + ticker.lower(), "acoes/" + ticker.lower()]
    
        for path in paths:
            url = "https://statusinvest.com.br/" + path
            r = requests.get(url, headers=headers, timeout=15)
            if r.status_code != 200:
                continue
            
            soup = BeautifulSoup(r.text, "html.parser")
            
            # Estratégia 1: achar h3 com título "P/VP" e pegar o strong mais próximo
            for h3 in soup.find_all("h3"):
                title = h3.get_text(strip=True)
                if title == "P/VP" or title.upper() == "P/VP":
                    # Sobe até o container e procura o strong com a classe value
                    container = h3.find_parent("div")
                    while container is not None:
                        strong = container.find("strong", class_="value")
                        if strong and strong.get_text(strip=True):
                            val = re.sub(r"[^\d,.-]", "", strong.get_text())
                            val = val.replace(".", "").replace(",", ".")  # 1.234,56 -> 1234.56
                            try:
                                return float(val)
                            except ValueError:
                                pass
                        container = container.find_parent("div")
            
            # Estratégia 2 (fallback): h3 com atributo title
            for h3 in soup.find_all("h3", attrs={"title": re.compile(r"P/VP|Preço.*Valor Patrimonial", re.I)}):
                container = h3.find_parent("div", class_=re.compile(r"info"))
                if container:
                    strong = container.find("strong", class_="value")
                    if strong:
                        val = re.sub(r"[^\d,.-]", "", strong.get_text())
                        val = val.replace(".", "").replace(",", ".")
                        try:
                            return float(val)
                        except ValueError:
                            pass
        
        raise ValueError("P/VP nao encontrado para " + ticker)

    def _json(self, status, body):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(body).encode())

    def log_message(self, format, *args):
        pass
