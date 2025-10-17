from bot_instance import bot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from user_sessions import set_user_price, set_user_ca, get_user_price
from ca_input_handler import send_ca_prompt
import requests

# Temporary storage for CA info for volume flow
volume_temp_ca_info = {}

PACKAGE_PRICES = {
    'vol_iron': '1',
    'vol_bronze': '3',
    'vol_gold': '5.2',
    'vol_platinum': '7.5',
    'vol_silver': '10',
    'vol_diamond': '15',
}

def handle_volume(call):
    chat_id = call.message.chat.id
    image_url = 'https://github.com/raccityy/raccityy.github.io/blob/main/volume.jpg?raw=true'
    short_caption = "Choose the desired Volume Boost package:"
    text = (
        "🧪Iron Package - $40,200 Volume\n"
        "🧪Bronze Package - $92,000 Volume\n"
        "🧪Silver Package - $466,000 Volume\n"
        "🧪Gold Package - $932,000 Volume\n"
        "🧪Platinum Package - $1,400,000 Volume\n"
        "🧪 Diamond Package - $2,400,000 Volume\n\n"
        "Please select the package below:"
    )
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("1 SOL - Irion⛓️", callback_data="vol_iron"),
        InlineKeyboardButton("3 SOL - Bronze 🥉", callback_data="vol_bronze"),
        InlineKeyboardButton("5.2 SOL - Gold", callback_data="vol_gold"),
        InlineKeyboardButton("7.5 SOL - Platinum ⏺️", callback_data="vol_platinum"),
        InlineKeyboardButton("10 SOL - Silver 🥈", callback_data="vol_silver"),
        InlineKeyboardButton("15 SOL - Diamond💎", callback_data="vol_diamond"),
        InlineKeyboardButton("🔙 Back", callback_data="vol_back"),
        InlineKeyboardButton("🔝 Main Menu", callback_data="vol_mainmenu")
    )
    try:
        # bot.send_photo(chat_id, image_url, caption=short_caption)
        bot.send_photo(chat_id, image_url, caption=text, reply_markup=markup)
    except Exception:
        bot.send_message(chat_id, short_caption)

def handle_volume_package(call):
    chat_id = call.message.chat.id
    package = call.data
    price = PACKAGE_PRICES.get(package)
    if not price:
        bot.send_message(chat_id, "Unknown package selected.")
        return
    set_user_price(chat_id, price)
    send_ca_prompt(chat_id, f"{price} SOL", "volume")

# This function is now handled by the new CA input handler
# Keeping for backward compatibility but it's no longer used
