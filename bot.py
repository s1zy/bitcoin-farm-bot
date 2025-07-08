
import json
import time
import requests
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = "7793860828:AAH-saWOoonpqnREsw62_oRevNZV8DD1utw"
DATA_FILE = "users.json"

# Загрузка пользователей
try:
    with open(DATA_FILE, "r") as f:
        users = json.load(f)
except FileNotFoundError:
    users = {}

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(users, f)

# Главное меню
main_menu = ReplyKeyboardMarkup(
    [
        [KeyboardButton("📜 Профиль"), KeyboardButton("💰 Баланс")],
        [KeyboardButton("🎮 Мои видеокарты"), KeyboardButton("🛒 Магазин")],
        [KeyboardButton("⚡️ Собрать доход"), KeyboardButton("💵 Продать BTC")],
        [KeyboardButton("📈 Курс BTC")]
    ],
    resize_keyboard=True
)

# Получить курс BTC
def get_btc_usd():
    try:
        response = requests.get("https://api.coindesk.com/v1/bpi/currentprice/USD.json")
        return response.json()["bpi"]["USD"]["rate_float"]
    except:
        return 0

# Старт
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in users:
        users[user_id] = {
            "balance_btc": 0.0,
            "balance_usd": 0.0,
            "gpus": {"Intel HD Graphics": 0.00001},
            "last_mine": time.time()
        }
        save_data()
        await update.message.reply_text(
            "👋 Привет! Выдана Intel HD Graphics (0.00001 BTC/ч).",
            reply_markup=main_menu
        )
    else:
        await update.message.reply_text(
            "Ты уже зарегистрирован! Вот твоё меню:",
            reply_markup=main_menu
        )

# Обработка всех кнопок
async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    text = update.message.text

    if user_id not in users:
        await start(update, context)
        return

    if text == "📜 Профиль":
        await profile(update, context)
    elif text == "💰 Баланс":
        await balance(update, context)
    elif text == "🎮 Мои видеокарты":
        await gpus(update, context)
    elif text == "🛒 Магазин":
        await shop(update, context)
    elif text == "⚡️ Собрать доход":
        await mine(update, context)
    elif text == "💵 Продать BTC":
        await sell_btc(update, context)
    elif text == "📈 Курс BTC":
        await btc_rate(update, context)
    elif text.lower().startswith("купить"):
        await buy_gpu(update, context)
    else:
        await update.message.reply_text("Не понял тебя 🤖")

# Профиль
async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = users[str(update.effective_user.id)]
    await update.message.reply_text(
        f"👤 Профиль:\n"
        f"BTC: {user['balance_btc']:.6f} BTC\n"
        f"USD: ${user['balance_usd']:.2f}\n"
        f"Карты: {', '.join(user['gpus'].keys())}"
    )

# Баланс
async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = users[str(update.effective_user.id)]
    rate = get_btc_usd()
    usd_equiv = user['balance_btc'] * rate
    await update.message.reply_text(
        f"💰 Баланс:\n"
        f"BTC: {user['balance_btc']:.6f} BTC (~${usd_equiv:.2f})\n"
        f"USD: ${user['balance_usd']:.2f}\n"
        f"Курс BTC: ${rate:.2f}"
    )

# Мои видеокарты
async def gpus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = users[str(update.effective_user.id)]
    if not user['gpus']:
        await update.message.reply_text("🎮 Нет видеокарт.")
    else:
        text = "🎮 Видеокарты:\n"
        for name, power in user['gpus'].items():
            text += f"- {name}: {power} BTC/ч\n"
        await update.message.reply_text(text)

# Магазин
async def shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🛒 Магазин:\n"
        "1. GTX 1050 Ti — $50 — 0.001 BTC/ч\n"
        "2. RTX 3080 — $500 — 0.01 BTC/ч\n"
        "Напиши: купить 1 или купить 2"
    )
# Купить карту
async def buy_gpu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = users[str(update.effective_user.id)]
    text = update.message.text.lower()

    if "1" in text:
        name, price, power = "GTX 1050 Ti", 50, 0.001
    elif "2" in text:
        name, price, power = "RTX 3080", 500, 0.01
    else:
        await update.message.reply_text("❌ Не понял, что купить 🤖")
        return

    if user['balance_usd'] >= price:
        user['balance_usd'] -= price
        user['gpus'][name] = user['gpus'].get(name, 0) + power
        save_data()
        await update.message.reply_text(f"✅ Куплено: {name} за ${price}!")
    else:
        await update.message.reply_text(f"❌ Не хватает денег! Нужно ${price}.")

# Собрать доход
async def mine(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = users[str(update.effective_user.id)]
    now = time.time()
    earned = sum(user['gpus'].values()) * ((now - user['last_mine']) / 3600)
    user['balance_btc'] += earned
    user['last_mine'] = now
    save_data()
    await update.message.reply_text(f"⚡️ Собрано: {earned:.6f} BTC!")

# Продать BTC
async def sell_btc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = users[str(update.effective_user.id)]
    if user['balance_btc'] <= 0:
        await update.message.reply_text("❌ Нет BTC для продажи.")
        return
    rate = get_btc_usd()
    usd = user['balance_btc'] * rate
    user['balance_usd'] += usd
    user['balance_btc'] = 0.0
    save_data()
    await update.message.reply_text(f"💵 Продано за ${usd:.2f} по курсу ${rate:.2f}.")

# Курс BTC
async def btc_rate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rate = get_btc_usd()
    await update.message.reply_text(f"📈 Курс BTC: ${rate:.2f}")

# Запуск
app = Application.builder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu))

print("✅ Бот запущен...")
app.run_polling()