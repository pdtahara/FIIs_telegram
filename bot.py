import os
import json
import re
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
# CACHE (evitar duplicados)
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
# BUSCA FNET
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
        print("Erro FNET:", e)

    return []

# =========================
# EXTRAI VALOR (R$)
# =========================
def extrair_valor(texto):
    if not texto:
        return None

    match = re.search(r"R\$\s?(\d+[.,]?\d*)", texto)
    if match:
        return match.group(0)

    return None

# =========================
# COMANDOS
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Bot FIIs + FIAGRO online!")

async def test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot funcionando!")

async def fiis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not FIIS:
        await update.message.reply_text("Carteira vazia")
        return

    await update.message.reply_text("📊 FIIs/FIAGRO:\n" + "\n".join(FIIS))

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

        print(f"{fii} → {len(docs)} docs")

        for d in docs:
            doc_id = str(d.get("idDocumento"))

            if doc_id in cache:
                continue

            titulo = d.get("titulo", "")
            data = d.get("dataEntrega", "")

            titulo_lower = titulo.lower()

            # FILTRO INTELIGENTE (FIIs + FIAGRO)
            if not any(p in titulo_lower for p in [
                "rendimento",
                "provento",
                "distribuição",
                "dividendo",
                "fato relevante"
            ]):
                continue

            # detectar tipo
            tipo = "🌾 FIAGRO" if "agro" in titulo_lower else "🏢 FII"

            # extrair valor
            valor = extrair_valor(titulo)

            valor_texto = f"💰 Valor: {valor}" if valor else "💰 Valor: não identificado"

            msg = f"""📢 {fii} ({tipo})

📄 {titulo}
📅 {data}
{valor_texto}

🔗 https://fnet.bmfbovespa.com.br
"""

            try:
                await context.bot.send_message(chat_id=CHAT_ID, text=msg)

                cache.add(doc_id)
                save_cache(cache)

            except Exception as e:
                print("Erro envio:", e)

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
