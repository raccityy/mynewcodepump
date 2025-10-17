from user_sessions import set_user_price
from bot_instance import bot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from menu import start_message
from ca_input_handler import send_ca_prompt

def handle_start_bump(call):
    chat_id = call.message.chat.id
    text = """
🟢The Best and Fastest Trend bot for creating ATH bump orders.

Supported Platform: Pumpfun and Raydium.

Pump-fun BumpBot charges a one-time fee of 0.3-0.6 SOL per token, making it the Fastest and Easiest bump bot ever!

🔔Alert channel: 
https://t.me/PumpAlert69
"""
    markup = InlineKeyboardMarkup()
    button3 = InlineKeyboardButton("🟢0.3 Sol Bump", callback_data="bump_0.3")
    button4 = InlineKeyboardButton("🟢0.4 Sol Bump", callback_data="bump_0.4")
    button5 = InlineKeyboardButton("🟢0.5 Sol Bump", callback_data="bump_0.5")
    button6 = InlineKeyboardButton("🟢0.6 Sol Bump", callback_data="bump_0.6")
    buttonback = InlineKeyboardButton("🔙 Back", callback_data="back")
    mainmenu = InlineKeyboardButton("🔝 Main Menu", callback_data="mainmenu")
    markup.row(button3)
    markup.row(button4, button5)
    markup.row(button6)
    markup.row(buttonback)
    markup.row(mainmenu)
    bot.send_message(
        chat_id,
        text,
        reply_markup=markup,
        parse_mode="markdown"
    )

def handle_startbumps_callbacks(call):
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    if call.data.startswith("bump_"):
        sol_amount = call.data.split("_")[1]
        set_user_price(chat_id, sol_amount)
        try:
            bot.delete_message(chat_id, message_id)
        except Exception as e:
            print(f"{e}")
        send_ca_prompt(chat_id, f"{sol_amount} SOL", "startbump")
    elif call.data == "back":
        # Go back to main menu (one step back from startbump)
        bot.delete_message(chat_id, message_id)
        start_message(call.message)
    elif call.data == "mainmenu":
        # Go to main menu
        bot.delete_message(chat_id, message_id)
        start_message(call.message)
