from bot_instance import bot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from premuim import handle_sol_trending

# Track users waiting for banner image
banner_waiting = {}

def handle_dexscreener(call):
    chat_id = call.message.chat.id
    image_url = 'https://raw.githubusercontent.com/raccityy/raccityy.github.io/refs/heads/main/dexscreener.jpg'
    text = (
        "🔘DEX Screener is a data platform and on-chain analytics tool designed for decentralized exchanges (DEXs), providing real-time insights into token prices, liquidity pools, trading volumes, and market trends across multiple blockchains."
    )
    markup = InlineKeyboardMarkup(row_width=2)
    # First row: one button
    markup.add(InlineKeyboardButton("TREND ON DEX", callback_data="dexscreener_trend"))
    # Second row: back and menu buttons
    markup.add(
        InlineKeyboardButton("🔙 Back", callback_data="dexscreener_back"),
        InlineKeyboardButton("🔝 Main Menu", callback_data="dexscreener_mainmenu")
    )
    try:
        bot.send_photo(chat_id, image_url, caption=text, reply_markup=markup)
    except Exception:
        bot.send_message(chat_id, text, reply_markup=markup)

def handle_dexscreener_trend(call):
    chat_id = call.message.chat.id
    text = (
        "[🗒]\n"
        "📄KINDLY Send Your Banner at Least 600 Pixels Wide"
    )
    banner_waiting[chat_id] = True
    bot.send_message(chat_id, text) 