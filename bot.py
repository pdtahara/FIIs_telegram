import os
import time
import requests
from telegram import Bot

TOKEN = os.getenv("8155409375:AAE5TiCikE1CJgWdFGc4vP0K3RE9JVTeSyI")
CHAT_ID = os.getenv("8473980241")

bot = Bot(token=TOKEN)

FIIS = ["VGIR11", "ARRI11", "MXRF11", "VGHF11", "BTHF11", "BTCI11", "FYTO11"]

def buscar_fii(fii):
    url = "https://fnet.bmfbovespa.com.br/fnet/publico/pesquisarGerenciadorDocumentosCVM"

    payload = {
        "sigla": fii,
        "pagina": 1
    }

    try:
        r = requests.post(url, data=payload, timeout=10)
        if r.status_code == 200:
            return r.json().get("data", [])
    except:
        pass

    return []

cache = set()

while True:
    for fii in FIIS:
        docs = buscar_fii(fii)

        for d in docs:
            doc_id = str(d.get("idDocumento"))

            if doc_id not in cache:
                bot.send_message(
                    chat_id=CHAT_ID,
                    text=f"📢 {fii}: {d.get('titulo','Novo documento')}"
                )
                cache.add(doc_id)

    time.sleep(300) 
