from bot_instance import bot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from user_sessions import set_user_price, set_user_ca, get_user_price
from ca_input_handler import send_ca_prompt
import requests

# Temporary storage for CA info for volume flow
volume_temp_ca_info = {}

PACKAGE_PRICES = {
    'vol_iron': '1.2',
    'vol_bronze': '3',
    'vol_silver': '5.5',
    'vol_gold': '7.5',
    'vol_platinum': '10',
    'vol_diamond': '15',
}

def handle_volume(call):
    chat_id = call.message.chat.id
    image_url = 'https://github.com/raccityy/smartnewandimproved/blob/main/volume.jpg?raw=true'
    short_caption = "Choose the desired Volume Boost package:"
    text = (
        "Choose the desired Volume Boost package:\n\n"
        "🧪Iron Package - $60,200\n"
        "Volume\n"
        "🧪Bronze Package - $152,000 volume\n"
        "🧪Silver Package - $666,000 Volume\n"
        "🧪Gold Package - $932,000 Volume\n"
        "🧪Platinum Package - $1,400,000 Volume\n"
        "🧪 Diamond Package - $2,400,000 Volume\n\n"
        "Volume booster is a mass system of boosting your token radically with no slow bumps motion, and out come of realized ATH(Martket Cap)📊\n\n"
        "Please select the package below:"
    )
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("1.2 Sol - Iron⛓️", callback_data="vol_iron"),
        InlineKeyboardButton("3 Sol - Bronze🥉", callback_data="vol_bronze"),
        InlineKeyboardButton("5.5 Sol - Silver🥈", callback_data="vol_silver"),
        InlineKeyboardButton("7.5 Sol - Gold 🥇", callback_data="vol_gold"),
        InlineKeyboardButton("10 Sol - Platinum ⚪️", callback_data="vol_platinum"),
        InlineKeyboardButton("15 Sol - Diamond 💎", callback_data="vol_diamond"),
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
