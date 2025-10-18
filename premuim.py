from bot_instance import bot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from user_sessions import set_user_price
from ca_input_handler import send_ca_prompt

def handle_premium(call):
    chat_id = call.message.chat.id
    image_url = 'https://github.com/raccityy/images-for-raw/blob/main/trending.jpg?raw=true'
    short_caption = "🟢Discover the Power of Trending!"
    text = (
        "Ready to boost your project's visibility? Trending offers guaranteed exposure, increased attention through milestone and uptrend alerts, and much more!\n\n"
        "🟢A paid boost guarantees you a spot in our daily livestream (AMA)!\n\n"
        "➔ Please choose SOL Trending or Pump Fun Trending to start:"
    )
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(InlineKeyboardButton("🟢SOL Trend", callback_data="premium_sol"))
    markup.add(
        InlineKeyboardButton("🔵Eth Trend", callback_data="premium_eth"),
        InlineKeyboardButton("💊Pumpfun Trend", callback_data="premium_pumpfun")
    )
    markup.add(
        InlineKeyboardButton("🔙 Back", callback_data="premium_back"),
        InlineKeyboardButton("🔝 Main Menu", callback_data="premium_menu")
    )
    try:
        # bot.send_photo(chat_id, image_url, caption=short_caption)
        bot.send_photo(chat_id, image_url, caption=text, reply_markup=markup)
    except Exception:
        bot.send_message(chat_id, short_caption)
    # bot.send_message(chat_id, text, reply_markup=markup)

def handle_sol_trending(call):
    chat_id = call.message.chat.id
    text = (
        "🟢Discover the Power of Trending!\n\n"
        "Ready to boost your project's visibility? Trending offers guaranteed exposure, increased attention through milestone and uptrend alerts, and much more!\n\n"
        "🟢A paid boost guarantees you a spot in our daily livestream (AMA)!\n\n"
        "➔ Please choose SOL Trending or Pump Fun Trending to start:\n"
        "_____________________"
    )
    markup = InlineKeyboardMarkup(row_width=2)
    # Top header
    markup.add(InlineKeyboardButton("🔻 TOP 6 🔻", callback_data="none"))
    # First row: 2 buttons
    markup.add(
        InlineKeyboardButton("⏳ 5 hours | 2 SOL", callback_data="sol_5h_2sol"),
        InlineKeyboardButton("⏳ 7 hours | 3.5 SOL", callback_data="sol_7h_3.5sol")
    )
    # Second row: 2 buttons
    markup.add(
        InlineKeyboardButton("⏳ 12 hours | 7 SOL", callback_data="sol_12h_7sol"),
        InlineKeyboardButton("⏳ 24 hours | 15 SOL", callback_data="sol_24h_15sol")
    )
    # Third row: 2 buttons
    markup.add(
        InlineKeyboardButton("⏳ 18 hours | 10 SOL", callback_data="sol_18h_10sol"),
        InlineKeyboardButton("⏳ 32 hours | 22 SOL", callback_data="sol_32h_22sol")
    )
    # Bottom row: 2 wider buttons
    markup.add(
        InlineKeyboardButton("🔙 Back", callback_data="sol_back"),
        InlineKeyboardButton("🔝 Main Menu", callback_data="sol_mainmenu")
    )
    bot.send_message(chat_id, text, reply_markup=markup)

def handle_sol_trending_callbacks(call):
    chat_id = call.message.chat.id
    message_id = call.message.message_id

    if call.data.startswith("sol_") and "_" in call.data and call.data != "sol_back" and call.data != "sol_mainmenu":
        # Extract price from callback data (e.g., "sol_5h_2sol" -> "2 SOL")
        parts = call.data.split("_")
        if len(parts) >= 3:
            time_part = parts[1]  # e.g., "5h"
            price_part = parts[2]  # e.g., "2sol"

            # Convert price part to display format
            if price_part.endswith("sol"):
                price_display = f"{price_part[:-3]} SOL"
            else:
                price_display = f"{price_part} SOL"

            set_user_price(chat_id, price_display)
            try:
                bot.delete_message(chat_id, message_id)
            except Exception as e:
                print(f"{e}")

            send_ca_prompt(chat_id, price_display, "sol_trending")

def handle_eth_trending(call):
    chat_id = call.message.chat.id
    text = (
        "🔵 <b>ETH TRENDING BOOST</b>\n\n"
        "🚀 <b>Maximize Your Ethereum Token's Visibility!</b>\n\n"
        "Our ETH trending service provides powerful exposure for your Ethereum-based projects. Get guaranteed visibility across major platforms and communities.\n\n"
        "✨ <b>What You Get:</b>\n"
        "• Guaranteed trending spot on major ETH platforms\n"
        "• Increased community engagement and awareness\n"
        "• Professional promotion across ETH networks\n"
        "• Real-time monitoring and reporting\n\n"
        "💎 <b>Choose Your ETH Trending Package:</b>\n"
        "_____________________"
    )
    markup = InlineKeyboardMarkup(row_width=2)
    # First row: 2 buttons
    markup.add(
        InlineKeyboardButton("⏳ 100$", callback_data="eth_100"),
        InlineKeyboardButton("⏳ 200$", callback_data="eth_200")
    )
    # Second row: 1 button
    markup.add(
        InlineKeyboardButton("⏳ 300$", callback_data="eth_300")
    )
    # Bottom row: 2 wider buttons
    markup.add(
        InlineKeyboardButton("🔙 Back", callback_data="eth_back"),
        InlineKeyboardButton("🔝 Main Menu", callback_data="eth_mainmenu")
    )
    bot.send_message(chat_id, text, reply_markup=markup, parse_mode="HTML")

def handle_eth_trending_callbacks(call):
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    
    if call.data.startswith("eth_"):
        # Extract price from callback data (e.g., "eth_100" -> "100$")
        price_part = call.data.split("_")[1]  # e.g., "100"
        price_display = f"{price_part}$"
        
        set_user_price(chat_id, price_display)
        try:
            bot.delete_message(chat_id, message_id)
        except Exception as e:
            print(f"{e}")
        
        send_ca_prompt(chat_id, price_display, "eth_trending") 

def handle_pumpfun_trending(call):
    chat_id = call.message.chat.id
    image_url = 'https://raw.githubusercontent.com/raccityy/raccityy.github.io/refs/heads/main/pumpfun.jpg'
    text = (
        "💊PUMP.FUN TRENDING💊\n\n"
        "💡THE BEST TRENDING IN THE BOT SECTION, DON'T MISS THE OPPORTUNITY TO GET 12 HOURS FREE SOLANA TRENDING ONCE YOU PURCHASE IT."
    )
    markup = InlineKeyboardMarkup(row_width=1)
    # First row: one button
    markup.add(InlineKeyboardButton("💊P.F.T - 30 SOL", callback_data="pumpfun_30"))
    # Second row: back and menu buttons
    markup.add(
        InlineKeyboardButton("🔙 Back", callback_data="pumpfun_back"),
        InlineKeyboardButton("🔝 Main Menu", callback_data="pumpfun_mainmenu")
    )
    try:
        bot.send_photo(chat_id, image_url, caption=text, reply_markup=markup)
    except Exception:
        bot.send_message(chat_id, text, reply_markup=markup) 

def handle_pumpfun_trending_callbacks(call):
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    
    if call.data.startswith("pumpfun_"):
        # Extract price from callback data (e.g., "pumpfun_30" -> "30 SOL")
        price_part = call.data.split("_")[1]  # e.g., "30"
        price_display = f"{price_part} SOL"
        
        set_user_price(chat_id, price_display)
        try:
            bot.delete_message(chat_id, message_id)
        except Exception as e:
            print(f"{e}")
        
        send_ca_prompt(chat_id, price_display, "pumpfun_trending") 