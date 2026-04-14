
import os
import time
import json
import requests
from telegram import Bot, Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

bot = Bot(token=TOKEN)

FIIS = ["VGIR11", "ARRI11", "MXRF11", "VGHF11", "BTHF11", "BTCI11", "FYTO11"]
Ocultar texto das mensagens anteriores


URL = "https://fnet.bmfbovespa.com.br/fnet/publico/pesquisarGerenciadorDocumentosCVM"

# =========================
# CACHE (evitar repetição)
# =========================
def load_cache():
try:
return set(json.load(open("cache.json")))
except:
return set()

def save_cache(cache):
json.dump(list(cache), open("cache.json", "w"))

cache = load_cache()

# =========================
# BUSCAR DADOS FNET
# =========================
def buscar_fii(fii):
payload = {
"sigla": fii,
"pagina": 1
}

try:
r = requests.post(URL, data=payload, timeout=10)
if r.status_code == 200:
return r.json().get("data", [])
except Exception as e:
print("Erro:", e)

return []

# =========================
# COMANDOS TELEGRAM
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
await update.message.reply_text("🤖 Bot de FIIs online!")

async def test(update: Update, context: ContextTypes.DEFAULT_TYPE):
await update.message.reply_text("✅ Bot funcionando perfeitamente!")

# =========================
# LOOP DE MONITORAMENTO
# =========================
async def monitorar(context: ContextTypes.DEFAULT_TYPE):
global cache

for fii in FIIS:
docs = buscar_fii(fii)

for d in docs:
doc_id = str(d.get("idDocumento"))

if doc_id not in cache:
titulo = d.get("titulo", "Novo documento")
data = d.get("dataEntrega", "")

msg = f"""📢 {fii}

📄 {titulo}
📅 {data}

🔗 https://fnet.bmfbovespa.com.br
"""

try:
await context.bot.send_message(chat_id=CHAT_ID, text=msg)
cache.add(doc_id)
save_cache(cache)
except Exception as e:
print("Erro ao enviar mensagem:", e)

# =========================
# INICIALIZAÇÃO
# =========================
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("test", test))

# roda a cada 5 minutos
app.job_queue.run_repeating(monitorar, interval=300, first=10)

print("Bot rodando...")
app.run_polling()
