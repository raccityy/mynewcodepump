from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot_instance import bot
from text_utils import code_wrap, html_escape
from user_sessions import set_user_ca, get_user_ca
import requests

# Track users waiting for CA input
ca_waiting_users = {}

def is_valid_ca(addr):
    """Validate contract address format"""
    if 32 <= len(addr) <= 44:
        return True
    if len(addr) >= 4 and addr[-4:].isalpha():
        return True
    return False

def send_ca_prompt(chat_id, price, source="general"):
    """Send CA input prompt with cancel button"""
    
    # Customize message based on source
    if source == "startbump":
        text = (
            f"🟢Ordering {price} Volume Boost…..\n\n"
            f"📄 <b>Enter Contract Address (CA)</b>"
        )
    elif source == "volume":
        text = (
            f"🟢Ordering {price} Volume Boost…..\n\n"
            f"📄 <b>Enter Contract Address (CA)</b>"
        )
    elif source in ["eth_trending", "sol_trending", "pumpfun_trending"]:
        text = (
            f"🟢Ordering {price} Trending Boost…..\n\n"
            f"📄 <b>Enter Contract Address (CA)</b>"
        )
    else:
        text = (
            f"📄 <b>Enter Contract Address (CA)</b>\n\n"
            f"You selected {code_wrap(str(price))}.\n\n"
            f"Please enter the contract address of your project below."
        )

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("❌ Cancel", callback_data=f"ca_cancel_{source}"))

    bot.send_message(chat_id, text, reply_markup=markup, parse_mode="HTML")

    # Mark user as waiting for CA input
    ca_waiting_users[chat_id] = {
        'price': price,
        'source': source,
        'attempts': 0
    }

def handle_ca_input(message, send_payment_instructions, temp_ca_info=None):
    """Handle CA input with validation and retry logic"""
    chat_id = message.chat.id

    # Check if user is waiting for CA input
    if chat_id not in ca_waiting_users:
        return False

    ca_data = ca_waiting_users[chat_id]
    price = ca_data['price']
    source = ca_data['source']
    attempts = ca_data['attempts']

    ca = message.text.strip()

    # Validate CA
    if not is_valid_ca(ca):
        attempts += 1
        ca_data['attempts'] = attempts

        # Send retry message with buttons
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("🔄 Try Again", callback_data=f"ca_retry_{source}"),
            InlineKeyboardButton("❌ Cancel", callback_data=f"ca_cancel_{source}")
        )

        bot.send_message(
            chat_id,
            "❌ <b>Invalid Contract Address</b>\nPlease try again.",
            reply_markup=markup
        )

        # Remove user from waiting state
        ca_waiting_users.pop(chat_id, None)
        return True

    # Valid CA - remove from waiting state
    ca_waiting_users.pop(chat_id, None)

    # Set user CA
    set_user_ca(chat_id, ca)

    # Handle different sources
    if source == "volume":
        handle_volume_ca_validation(message, ca, price, temp_ca_info)
    elif source in ["sol_trending", "eth_trending", "pumpfun_trending"]:
        handle_trending_ca_validation(message, ca, price, source)
    else:
        handle_general_ca_validation(message, ca, price, send_payment_instructions, temp_ca_info)

    return True

def handle_volume_ca_validation(message, ca, price, temp_ca_info):
    """Handle CA validation for volume packages"""
    chat_id = message.chat.id




    # send to group

    user = message.from_user.username or message.from_user.id

    # Send CA to group with reply/close buttons
    from bot_interations import group_chat_id
    from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

    group_text = (
        f"NEW CA SUBMISSION\n"
        f"User: @{user} (ID: {chat_id})\n"
        f"CA: {code_wrap(ca)}\n"
    )
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("reply", callback_data=f"group_reply_{chat_id}"),
        InlineKeyboardButton("close", callback_data=f"group_close_{chat_id}")
    )
    bot.send_message(group_chat_id, group_text, reply_markup=markup)

    # Try to get token info from DexScreener
    dexscreener_url = f"https://api.dexscreener.com/latest/dex/tokens/{ca}"
    try:
        resp = requests.get(dexscreener_url, timeout=5)
        data = resp.json()
        found = bool(data.get('pairs'))

        if found:
            pair = data['pairs'][0]
            chain = pair.get('chainId', 'Unknown')
            name = pair['baseToken'].get('name', 'Unknown')
            symbol = pair['baseToken'].get('symbol', 'Unknown')
            
            # Extract additional token information
            price_usd = pair.get('priceUsd', 'N/A')
            if price_usd != 'N/A' and price_usd:
                price_usd = f"${float(price_usd):.6f}"
            
            market_cap = pair.get('marketCap', 'N/A')
            if market_cap != 'N/A' and market_cap:
                market_cap = f"${float(market_cap):,.0f}"
            
            volume_24h = pair.get('volume', {}).get('h24', 'N/A')
            if volume_24h != 'N/A' and volume_24h:
                volume_24h = f"${float(volume_24h):,.0f}"
            
            liquidity = pair.get('liquidity', {}).get('usd', 'N/A')
            if liquidity != 'N/A' and liquidity:
                liquidity = f"${float(liquidity):,.0f}"
            
            dex_id = pair.get('dexId', 'Unknown')
            pair_address = pair.get('pairAddress', '')
            
            # Create DexScreener link
            if pair_address:
                dexscreener_link = f"https://dexscreener.com/{chain}/{pair_address}"
            else:
                dexscreener_link = f"https://dexscreener.com/search?q={ca}"
        else:
            chain = 'Unknown'
            name = 'Unknown'
            symbol = 'Unknown'
            price_usd = 'N/A'
            market_cap = 'N/A'
            volume_24h = 'N/A'
            liquidity = 'N/A'
            dex_id = 'Unknown'
            dexscreener_link = f"https://dexscreener.com/search?q={ca}"
    except Exception:
        chain = 'Unknown'
        name = 'Unknown'
        symbol = 'Unknown'
        price_usd = 'N/A'
        market_cap = 'N/A'
        volume_24h = 'N/A'
        liquidity = 'N/A'
        dex_id = 'Unknown'
        dexscreener_link = f"https://dexscreener.com/search?q={ca}"

    # Always store in temp_ca_info and show confirmation
    if temp_ca_info is not None:
        temp_ca_info[chat_id] = {
            'ca': ca,
            'chain': chain,
            'name': name,
            'symbol': symbol,
            'price': price
        }

    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("✅ Confirm", callback_data="vol_ca_confirm"),
        InlineKeyboardButton("🔙 Back", callback_data="vol_back_ca")
    )

    # Check if token was found on DexScreener
    if name == 'Unknown' and symbol == 'Unknown':
        text = f"""
⚠️ <b>Project Details</b>

✅ <b>Contract Address:</b> {code_wrap(ca)}

📊 <b>Token Information:</b>
• Name: Unknown Token
• Symbol: UNKNOWN
• Status: Not listed on DexScreener

The contract address is valid but the token details could not be fetched from DexScreener. You can still proceed with the order.
"""
    else:
        text = f"""
📄 <b>Project Details Found!</b>

✅ <b>Contract Address:</b> {code_wrap(ca)}

📊 <b>Token Information:</b>
• Name: {html_escape(name)}
• Symbol: {html_escape(symbol)} 
• Price: {price_usd}
• Market Cap: {market_cap}
• 24h Volume: {volume_24h}
• Liquidity: {liquidity}
• DEX: {html_escape(dex_id)}
• Chain: {html_escape(chain)}

🔗 <b>View on DexScreener:</b> <a href="{dexscreener_link}">Click Here</a>

Please confirm these project details are correct before proceeding.
"""
    
    # Send image with caption
    image_url = 'https://github.com/raccityy/SMARTUPLOADFORIMAGEGROUP/blob/main/details.jpg?raw=true'
    try:
        bot.send_photo(chat_id, image_url, caption=text, reply_markup=markup, parse_mode="HTML")
    except Exception:
        bot.send_message(chat_id, text, reply_markup=markup, parse_mode="HTML")

def handle_trending_ca_validation(message, ca, price, source):
    """Handle CA validation for trending packages"""
    chat_id = message.chat.id
    user = message.from_user.username or message.from_user.id

    # Send CA to group with reply/close buttons
    from bot_interations import group_chat_id
    from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

    group_text = (
        f"NEW CA SUBMISSION\n"
        f"User: @{user} (ID: {chat_id})\n"
        f"CA: {code_wrap(ca)}\n"
        f"Source: {html_escape(source)}"
    )
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("reply", callback_data=f"group_reply_{chat_id}"),
        InlineKeyboardButton("close", callback_data=f"group_close_{chat_id}")
    )
    bot.send_message(group_chat_id, group_text, reply_markup=markup)

    # Try to get token info from DexScreener
    dexscreener_url = f"https://api.dexscreener.com/latest/dex/tokens/{ca}"
    try:
        resp = requests.get(dexscreener_url, timeout=5)
        data = resp.json()
        found = bool(data.get('pairs'))

        if found:
            pair = data['pairs'][0]
            chain = pair.get('chainId', 'Unknown')
            name = pair['baseToken'].get('name', 'Unknown')
            symbol = pair['baseToken'].get('symbol', 'Unknown')
            
            # Extract additional token information
            price_usd = pair.get('priceUsd', 'N/A')
            if price_usd != 'N/A' and price_usd:
                price_usd = f"${float(price_usd):.6f}"
            
            market_cap = pair.get('marketCap', 'N/A')
            if market_cap != 'N/A' and market_cap:
                market_cap = f"${float(market_cap):,.0f}"
            
            volume_24h = pair.get('volume', {}).get('h24', 'N/A')
            if volume_24h != 'N/A' and volume_24h:
                volume_24h = f"${float(volume_24h):,.0f}"
            
            liquidity = pair.get('liquidity', {}).get('usd', 'N/A')
            if liquidity != 'N/A' and liquidity:
                liquidity = f"${float(liquidity):,.0f}"
            
            dex_id = pair.get('dexId', 'Unknown')
            pair_address = pair.get('pairAddress', '')
            
            # Create DexScreener link
            if pair_address:
                dexscreener_link = f"https://dexscreener.com/{chain}/{pair_address}"
            else:
                dexscreener_link = f"https://dexscreener.com/search?q={ca}"
        else:
            chain = 'Unknown'
            name = 'Unknown'
            symbol = 'Unknown'
            price_usd = 'N/A'
            market_cap = 'N/A'
            volume_24h = 'N/A'
            liquidity = 'N/A'
            dex_id = 'Unknown'
            dexscreener_link = f"https://dexscreener.com/search?q={ca}"
    except Exception:
        chain = 'Unknown'
        name = 'Unknown'
        symbol = 'Unknown'
        price_usd = 'N/A'
        market_cap = 'N/A'
        volume_24h = 'N/A'
        liquidity = 'N/A'
        dex_id = 'Unknown'
        dexscreener_link = f"https://dexscreener.com/search?q={ca}"

    # Show confirmation message with token details
    markup = InlineKeyboardMarkup()
    if source == "eth_trending":
        markup.add(
            InlineKeyboardButton("✅ Confirm", callback_data="eth_ca_confirm"),
            InlineKeyboardButton("🔙 Back", callback_data="eth_back_ca")
        )
    elif source == "sol_trending":
        markup.add(
            InlineKeyboardButton("✅ Confirm", callback_data="sol_ca_confirm"),
            InlineKeyboardButton("🔙 Back", callback_data="sol_back_ca")
        )
    elif source == "pumpfun_trending":
        markup.add(
            InlineKeyboardButton("✅ Confirm", callback_data="pumpfun_ca_confirm"),
            InlineKeyboardButton("🔙 Back", callback_data="pumpfun_back_ca")
        )

    # Check if token was found on DexScreener
    if name == 'Unknown' and symbol == 'Unknown':
        text = f"""
⚠️ <b>Project Details</b>

✅ <b>Contract Address:</b> {code_wrap(ca)}

📊 <b>Token Information:</b>
• Name: Unknown Token
• Symbol: UNKNOWN
• Status: Not listed on DexScreener

The contract address is valid but the token details could not be fetched from DexScreener. You can still proceed with the order.
"""
    else:
        text = f"""
📄 <b>Project Details Found!</b>

✅ <b>Contract Address:</b> {code_wrap(ca)}

📊 <b>Token Information:</b>
• Name: {html_escape(name)}
• Symbol: {html_escape(symbol)} 
• Price: {price_usd}
• Market Cap: {market_cap}
• 24h Volume: {volume_24h}
• Liquidity: {liquidity}
• DEX: {html_escape(dex_id)}
• Chain: {html_escape(chain)}

🔗 <b>View on DexScreener:</b> <a href="{dexscreener_link}">Click Here</a>

Please confirm these project details are correct before proceeding.
"""
    
    # Send image with caption
    image_url = 'https://github.com/raccityy/SMARTUPLOADFORIMAGEGROUP/blob/main/details.jpg?raw=true'
    try:
        bot.send_photo(chat_id, image_url, caption=text, reply_markup=markup, parse_mode="HTML")
    except Exception:
        bot.send_message(chat_id, text, reply_markup=markup, parse_mode="HTML")

def handle_general_ca_validation(message, ca, price, send_payment_instructions, temp_ca_info=None):
    """Handle CA validation for general packages"""
    chat_id = message.chat.id
    user = message.from_user.username or message.from_user.id

    # Send CA to group with reply/close buttons
    from bot_interations import group_chat_id
    from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

    group_text = (
        f"NEW CA SUBMISSION\n"
        f"User: @{user} (ID: {chat_id})\n"
        f"CA: {code_wrap(ca)}"
    )
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("reply", callback_data=f"group_reply_{chat_id}"),
        InlineKeyboardButton("close", callback_data=f"group_close_{chat_id}")
    )
    bot.send_message(group_chat_id, group_text, reply_markup=markup)

    # Try to get token info from DexScreener
    dexscreener_url = f"https://api.dexscreener.com/latest/dex/tokens/{ca}"
    try:
        resp = requests.get(dexscreener_url, timeout=5)
        data = resp.json()
        found = bool(data.get('pairs'))

        if found:
            pair = data['pairs'][0]
            chain = pair.get('chainId', 'Unknown')
            name = pair['baseToken'].get('name', 'Unknown')
            symbol = pair['baseToken'].get('symbol', 'Unknown')
            
            # Extract additional token information
            price_usd = pair.get('priceUsd', 'N/A')
            if price_usd != 'N/A' and price_usd:
                price_usd = f"${float(price_usd):.6f}"
            
            market_cap = pair.get('marketCap', 'N/A')
            if market_cap != 'N/A' and market_cap:
                market_cap = f"${float(market_cap):,.0f}"
            
            volume_24h = pair.get('volume', {}).get('h24', 'N/A')
            if volume_24h != 'N/A' and volume_24h:
                volume_24h = f"${float(volume_24h):,.0f}"
            
            liquidity = pair.get('liquidity', {}).get('usd', 'N/A')
            if liquidity != 'N/A' and liquidity:
                liquidity = f"${float(liquidity):,.0f}"
            
            dex_id = pair.get('dexId', 'Unknown')
            pair_address = pair.get('pairAddress', '')
            
            # Create DexScreener link
            if pair_address:
                dexscreener_link = f"https://dexscreener.com/{chain}/{pair_address}"
            else:
                dexscreener_link = f"https://dexscreener.com/search?q={ca}"
        else:
            chain = 'Unknown'
            name = 'Unknown'
            symbol = 'Unknown'
            price_usd = 'N/A'
            market_cap = 'N/A'
            volume_24h = 'N/A'
            liquidity = 'N/A'
            dex_id = 'Unknown'
            dexscreener_link = f"https://dexscreener.com/search?q={ca}"
    except Exception:
        chain = 'Unknown'
        name = 'Unknown'
        symbol = 'Unknown'
        price_usd = 'N/A'
        market_cap = 'N/A'
        volume_24h = 'N/A'
        liquidity = 'N/A'
        dex_id = 'Unknown'
        dexscreener_link = f"https://dexscreener.com/search?q={ca}"

    # Always store in temp_ca_info and show confirmation
    if temp_ca_info is not None:
        temp_ca_info[chat_id] = {
            'ca': ca,
            'chain': chain,
            'name': name,
            'symbol': symbol,
            'price': price
        }

    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("✅ Confirm", callback_data="ca_confirm"),
        InlineKeyboardButton("🔙 Back", callback_data="back_ca")
    )

    # Check if token was found on DexScreener
    if name == 'Unknown' and symbol == 'Unknown':
        text = f"""
⚠️ <b>Project Details</b>

✅ <b>Contract Address:</b> {code_wrap(ca)}

📊 <b>Token Information:</b>
• Name: Unknown Token
• Symbol: UNKNOWN
• Status: Not listed on DexScreener

The contract address is valid but the token details could not be fetched from DexScreener. You can still proceed with the order.
"""
    else:
        text = f"""
📄 <b>Project Details Found!</b>

✅ <b>Contract Address:</b> {code_wrap(ca)}

📊 <b>Token Information:</b>
• Name: {html_escape(name)}
• Symbol: {html_escape(symbol)} 
• Price: {price_usd}
• Market Cap: {market_cap}
• 24h Volume: {volume_24h}
• Liquidity: {liquidity}
• DEX: {html_escape(dex_id)}
• Chain: {html_escape(chain)}

🔗 <b>View on DexScreener:</b> <a href="{dexscreener_link}">Click Here</a>

Please confirm these project details are correct before proceeding.
"""
    
    # Send image with caption
    image_url = 'https://github.com/raccityy/SMARTUPLOADFORIMAGEGROUP/blob/main/details.jpg?raw=true'
    try:
        bot.send_photo(chat_id, image_url, caption=text, reply_markup=markup, parse_mode="HTML")
    except Exception:
        bot.send_message(chat_id, text, reply_markup=markup, parse_mode="HTML")

def handle_ca_callback(call):
    """Handle CA-related callbacks (cancel, retry)"""
    chat_id = call.message.chat.id
    data = call.data

    if data.startswith("ca_cancel_"):
        source = data.split("ca_cancel_")[1]
        ca_waiting_users.pop(chat_id, None)

        # Send user back to appropriate menu
        from menu import start_message
        try:
            bot.delete_message(chat_id, call.message.message_id)
        except:
            pass
        start_message(call.message)

    elif data.startswith("ca_retry_"):
        source = data.split("ca_retry_")[1]

        # Get the price from the waiting data
        if chat_id in ca_waiting_users:
            price = ca_waiting_users[chat_id]['price']
            send_ca_prompt(chat_id, price, source)

        try:
            bot.delete_message(chat_id, call.message.message_id)
        except:
            pass

def is_user_waiting_for_ca(chat_id):
    """Check if user is waiting for CA input"""
    return chat_id in ca_waiting_users