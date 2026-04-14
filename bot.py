import os
import json
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

URL = "https://fnet.bmfbovespa.com.br/fnet/publico/pesquisarGerenciadorDocumentosCVM"

# =========================
# CARTEIRA DINÂMICA
# =========================
def load_fiis():
    try:
        return json.load(open("fiis.json"))
    except:
        return []

def save_fiis(fiis):
    json.dump(fiis, open("fiis.json", "w"))

FIIS = load_fiis()

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
        print("Erro ao buscar:", e)

    return []

# =========================
# COMANDOS TELEGRAM
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Bot de FIIs online!")

async def test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot funcionando!")

async def fiis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not FIIS:
        await update.message.reply_text("Carteira vazia")
        return

    lista = "\n".join(FIIS)
    await update.message.reply_text(f"📊 FIIs monitorados:\n{lista}")

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global FIIS

    if not context.args:
        await update.message.reply_text("Use: /add HGLG11")
        return

    fii = context.args[0].upper()

    if fii in FIIS:
        await update.message.reply_text(f"{fii} já está na carteira")
        return

    FIIS.append(fii)
    save_fiis(FIIS)

    await update.message.reply_text(f"✅ {fii} adicionado!")

async def remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global FIIS

    if not context.args:
        await update.message.reply_text("Use: /remove HGLG11")
        return

    fii = context.args[0].upper()

    if fii not in FIIS:
        await update.message.reply_text(f"{fii} não está na carteira")
        return

    FIIS.remove(fii)
    save_fiis(FIIS)

    await update.message.reply_text(f"❌ {fii} removido!")

# =========================
# MONITORAMENTO
# =========================
async def monitorar(context: ContextTypes.DEFAULT_TYPE):
    global cache

    if not FIIS:
        return

    for fii in FIIS:
        docs = buscar_fii(fii)

        print(f"{fii} → encontrados {len(docs)} documentos")

        for d in docs:
            doc_id = str(d.get("idDocumento"))

            if doc_id in cache:
                continue

            titulo = d.get("titulo", "Novo documento")
            data = d.get("dataEntrega", "")

            titulo_lower = titulo.lower()

            # FILTRO (evita spam)
            if not any(p in titulo_lower for p in ["rendimento", "fato relevante"]):
                continue

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
                print("Erro ao enviar:", e)

# =========================
# INICIALIZAÇÃO
# =========================
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("test", test))
app.add_handler(CommandHandler("fiis", fiis))
app.add_handler(CommandHandler("add", add))
app.add_handler(CommandHandler("remove", remove))

# roda a cada 5 minutos
app.job_queue.run_repeating(monitorar, interval=300, first=10)

print("Bot rodando...")
app.run_polling()
