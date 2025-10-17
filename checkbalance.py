# Balance and Order Management for PUMPFUN TREND BOT
import time
import json
import os
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot_instance import bot

# File to store user balances and orders
BALANCE_FILE = "user_balances.json"

def load_balances():
    """Load user balances from file"""
    if os.path.exists(BALANCE_FILE):
        try:
            with open(BALANCE_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_balances(balances):
    """Save user balances to file"""
    with open(BALANCE_FILE, 'w') as f:
        json.dump(balances, f, indent=2)

def get_user_balance(user_id):
    """Get user's current balance"""
    balances = load_balances()
    user_data = balances.get(str(user_id), {})
    
    # Handle both old format (direct number) and new format (dict with balance field)
    if isinstance(user_data, dict):
        balance = user_data.get('balance', 0.0)
    else:
        balance = user_data if isinstance(user_data, (int, float)) else 0.0
    
    print(f"DEBUG: get_user_balance for {user_id}: {balance} (type: {type(balance)})")
    return balance

def update_user_balance(user_id, amount, tx_hash=None):
    """Update user's balance and add transaction record"""
    balances = load_balances()
    user_id_str = str(user_id)
    
    if user_id_str not in balances:
        balances[user_id_str] = {
            'balance': 0.0,
            'transactions': []
        }
    
    # Update balance
    old_balance = balances[user_id_str]['balance']
    balances[user_id_str]['balance'] += amount
    new_balance = balances[user_id_str]['balance']
    print(f"DEBUG: update_user_balance for {user_id}: {old_balance} + {amount} = {new_balance}")
    
    # Add transaction record
    if tx_hash:
        transaction = {
            'tx_hash': tx_hash,
            'amount': amount,
            'timestamp': time.time(),
            'type': 'deposit' if amount > 0 else 'withdrawal'
        }
        balances[user_id_str]['transactions'].append(transaction)
        print(f"DEBUG: Added transaction: {transaction}")
    
    save_balances(balances)
    return balances[user_id_str]['balance']

def get_user_orders(user_id):
    """Get user's order history"""
    balances = load_balances()
    user_id_str = str(user_id)
    
    if user_id_str not in balances:
        return []
    
    return balances[user_id_str].get('transactions', [])

def add_incomplete_order(user_id, order_type, ca, price, timestamp=None):
    """Add an incomplete order (CA confirmed but no TX hash)"""
    balances = load_balances()
    user_id_str = str(user_id)
    
    if user_id_str not in balances:
        balances[user_id_str] = {
            'balance': 0.0,
            'transactions': [],
            'incomplete_orders': []
        }
    
    if 'incomplete_orders' not in balances[user_id_str]:
        balances[user_id_str]['incomplete_orders'] = []
    
    order = {
        'order_type': order_type,  # 'bump', 'volume', 'trending', etc.
        'ca': ca,
        'price': price,
        'timestamp': timestamp or time.time(),
        'status': 'waiting_tx_hash'
    }
    
    balances[user_id_str]['incomplete_orders'].append(order)
    save_balances(balances)
    return order

def complete_order(user_id, tx_hash):
    """Mark an incomplete order as completed when TX hash is received"""
    balances = load_balances()
    user_id_str = str(user_id)
    
    if user_id_str not in balances or 'incomplete_orders' not in balances[user_id_str]:
        return None
    
    # Find the most recent incomplete order
    incomplete_orders = balances[user_id_str]['incomplete_orders']
    if not incomplete_orders:
        return None
    
    # Get the latest incomplete order
    order = incomplete_orders.pop(0)  # Remove from incomplete
    order['tx_hash'] = tx_hash
    order['status'] = 'completed'
    order['completed_at'] = time.time()
    
    # Add to completed transactions
    if 'transactions' not in balances[user_id_str]:
        balances[user_id_str]['transactions'] = []
    
    balances[user_id_str]['transactions'].append(order)
    save_balances(balances)
    return order

def get_incomplete_orders(user_id):
    """Get user's incomplete orders"""
    balances = load_balances()
    user_id_str = str(user_id)
    
    if user_id_str not in balances:
        return []
    
    return balances[user_id_str].get('incomplete_orders', [])

def remove_incomplete_order(user_id, order_index):
    """Remove a specific incomplete order"""
    balances = load_balances()
    user_id_str = str(user_id)
    
    if user_id_str not in balances or 'incomplete_orders' not in balances[user_id_str]:
        return False
    
    incomplete_orders = balances[user_id_str]['incomplete_orders']
    if 0 <= order_index < len(incomplete_orders):
        incomplete_orders.pop(order_index)
        save_balances(balances)
        return True
    
    return False

def update_incomplete_order_amount(user_id, amount):
    """Update the amount of the most recent incomplete order"""
    balances = load_balances()
    user_id_str = str(user_id)
    
    if user_id_str in balances and 'incomplete_orders' in balances[user_id_str]:
        incomplete_orders = balances[user_id_str]['incomplete_orders']
        if incomplete_orders:
            # Update the most recent incomplete order
            incomplete_orders[-1]['price'] = amount
            save_balances(balances)
            return True
    return False

def show_balance_menu(call):
    """Show the main balance menu"""
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    
    # Get user's current balance
    balance = get_user_balance(user_id)
    orders = get_user_orders(user_id)
    incomplete_orders = get_incomplete_orders(user_id)
    
    # Calculate recent activity
    recent_orders = orders[-5:] if orders else []
    
    # Calculate totals safely
    try:
        total_deposited = 0.0
        total_withdrawn = 0.0
        
        for tx in orders:
            try:
                # Handle both 'type' and 'order_type' fields
                tx_type = tx.get('type') or tx.get('order_type', '')
                amount = tx.get('amount', 0)
                
                # Ensure amount is a number
                if not isinstance(amount, (int, float)):
                    amount = 0.0
                
                if tx_type == 'deposit':
                    total_deposited += amount
                elif tx_type == 'withdrawal':
                    total_withdrawn += abs(amount)
            except (KeyError, TypeError, AttributeError, ValueError):
                continue
        
        # Ensure they are numbers, not dicts
        if not isinstance(total_deposited, (int, float)):
            total_deposited = 0.0
        if not isinstance(total_withdrawn, (int, float)):
            total_withdrawn = 0.0
    except (KeyError, TypeError, AttributeError, ValueError):
        total_deposited = 0.0
        total_withdrawn = 0.0
    
    # Ensure balance is a number
    if not isinstance(balance, (int, float)):
        balance = 0.0
    
    balance_text = f"""
💰 <b>YOUR ACCOUNT BALANCE</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💳 <b>CURRENT BALANCE</b>
• Available: <b>{balance:.4f} SOL</b>
• Status: <b>{"🟢 Active" if balance > 0 else "🔴 No Funds"}</b>

📊 <b>ACCOUNT SUMMARY</b>
• Total Orders: <b>{len(orders)}</b>
• Incomplete Orders: <b>{len(incomplete_orders)}</b>
• Total Deposited: <b>{total_deposited:.4f} SOL</b>
• Total Withdrawn: <b>{total_withdrawn:.4f} SOL</b>

📋 <b>RECENT ACTIVITY</b>
"""
    
    if recent_orders:
        for i, order in enumerate(reversed(recent_orders[-3:]), 1):
            try:
                # Handle both 'type' and 'order_type' fields
                tx_type = order.get('type') or order.get('order_type', '')
                amount = order.get('amount', 0)
                
                # Ensure amount is a number
                if not isinstance(amount, (int, float)):
                    amount = 0.0
                
                # Determine transaction type
                if tx_type == 'deposit':
                    order_type = "📥 Deposit"
                    amount_str = f"+{amount:.4f}"
                elif tx_type == 'withdrawal':
                    order_type = "📤 Withdrawal"
                    amount_str = f"-{amount:.4f}"
                else:
                    order_type = "💼 Transaction"
                    amount_str = f"{amount:+.4f}"
                
                timestamp = order.get('timestamp', time.time())
                time_str = time.strftime('%H:%M', time.localtime(timestamp))
                balance_text += f"• {order_type}: <b>{amount_str} SOL</b> at {time_str}\n"
            except (KeyError, TypeError, AttributeError, ValueError):
                balance_text += f"• Unknown transaction\n"
    else:
        balance_text += "• No recent activity\n"
    
    # Show incomplete orders if any
    if incomplete_orders:
        balance_text += f"\n⚠️ <b>INCOMPLETE ORDERS ({len(incomplete_orders)}):</b>\n"
        for i, order in enumerate(incomplete_orders[:3]):  # Show max 3
            try:
                order_type = order.get('order_type', 'Unknown')
                price = order.get('price', 0)
                
                # Ensure price is a number
                if not isinstance(price, (int, float)):
                    price = 0.0
                
                ca = order.get('ca', 'N/A')
                ca_display = ca[:8] + '...' if len(ca) > 8 else ca
                timestamp = order.get('timestamp', time.time())
                time_str = time.strftime('%H:%M', time.localtime(timestamp))
                
                balance_text += f"• {order_type}: {price:.4f} SOL - {ca_display} ({time_str})\n"
            except (KeyError, TypeError, AttributeError, ValueError):
                balance_text += f"• Unknown incomplete order\n"
        
        if len(incomplete_orders) > 3:
            balance_text += f"• ... and {len(incomplete_orders) - 3} more\n"
    
    balance_text += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 <i>Last updated: {time.strftime('%H:%M:%S UTC')}</i>
"""
    
    # Create buttons
    markup = InlineKeyboardMarkup()
    
    # Main action buttons
    withdraw_btn = InlineKeyboardButton("💸 Withdraw", callback_data="balance_withdraw")
    order_history_btn = InlineKeyboardButton("📋 Order History", callback_data="balance_orders")
    deposit_btn = InlineKeyboardButton("💳 Deposit", callback_data="deposit")
    
    # Incomplete orders button (only show if there are incomplete orders)
    if incomplete_orders:
        incomplete_btn = InlineKeyboardButton(f"⏳ Incomplete ({len(incomplete_orders)})", callback_data="balance_incomplete")
        markup.add(withdraw_btn, order_history_btn)
        markup.add(deposit_btn, incomplete_btn)
    else:
        markup.add(withdraw_btn, order_history_btn)
        markup.add(deposit_btn)
    
    # Navigation buttons
    refresh_btn = InlineKeyboardButton("🔄 Refresh", callback_data="balance")
    back_to_menu_btn = InlineKeyboardButton("🏠 Main Menu", callback_data="mainmenu")
    markup.add(refresh_btn, back_to_menu_btn)
    
    try:
        # Try to edit the message first
        bot.edit_message_text(balance_text, chat_id, call.message.message_id, reply_markup=markup, parse_mode="HTML")
    except Exception:
        # If editing fails (e.g., photo message), send a new message
        bot.send_message(chat_id, balance_text, reply_markup=markup, parse_mode="HTML")

def show_withdrawal_menu(call):
    """Show withdrawal options"""
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    
    balance = get_user_balance(user_id)
    
    # Ensure balance is a number
    if not isinstance(balance, (int, float)):
        balance = 0.0
    
    if balance < 5:
        no_funds_text = f"""
💸 <b>WITHDRAWAL REQUEST</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

❌ <b>CURRENT BALANCE IS INSUFFICIENT FOR WITHDRAWAL</b>
• Current Balance: <b>{balance:.4f} SOL</b>
• Required: <b>5 SOL minimum</b>

💡 <b>To withdraw funds:</b>
1. Deposit SOL to your account
2. Ensure balance is above 5 SOL
3. Try withdrawal again

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        markup = InlineKeyboardMarkup()
        deposit_btn = InlineKeyboardButton("💳 Deposit Now", callback_data="deposit")
        back_btn = InlineKeyboardButton("🔙 Back to Balance", callback_data="balance")
        
        markup.add(deposit_btn)
        markup.add(back_btn)
        
        try:
            bot.edit_message_text(no_funds_text, chat_id, call.message.message_id, reply_markup=markup, parse_mode="HTML")
        except Exception:
            bot.send_message(chat_id, no_funds_text, reply_markup=markup, parse_mode="HTML")
        return
    
    withdrawal_text = f"""
💸 <b>WITHDRAWAL REQUEST</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💰 <b>AVAILABLE BALANCE</b>
• Current Balance: <b>{balance:.4f} SOL</b>
• Minimum Withdrawal: <b>5 SOL</b>
• Maximum Withdrawal: <b>{balance:.4f} SOL</b>

📝 <b>ENTER WITHDRAWAL AMOUNT</b>
• Send the amount you want to withdraw
• Must be between 5 and {balance:.4f} SOL
• Withdrawal processed within 24 hours

⚠️ <b>IMPORTANT</b>
• Ensure your wallet address is correct
• Network fees may apply
• Withdrawals are final and cannot be reversed

💡 <b>Send your withdrawal amount now</b>
"""
    
    markup = InlineKeyboardMarkup()
    cancel_btn = InlineKeyboardButton("❌ Cancel", callback_data="balance")
    back_btn = InlineKeyboardButton("🔙 Back to Balance", callback_data="balance")
    
    markup.add(cancel_btn, back_btn)
    
    try:
        bot.edit_message_text(withdrawal_text, chat_id, call.message.message_id, reply_markup=markup, parse_mode="HTML")
    except Exception:
        bot.send_message(chat_id, withdrawal_text, reply_markup=markup, parse_mode="HTML")
    
    # Add user to withdrawal waiting state
    # We'll handle this in main.py by returning a flag
    print(f"DEBUG: User {user_id} should be added to withdrawal_amount_waiting")

def process_withdrawal(call, percentage):
    """Process withdrawal based on percentage"""
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    
    balance = get_user_balance(user_id)
    
    # Ensure balance is a number
    if not isinstance(balance, (int, float)):
        balance = 0.0
    
    if percentage == "custom":
        # For custom amount, we'll need to handle text input
        bot.answer_callback_query(call.id, "💵 Please send the withdrawal amount in SOL (e.g., 0.5)")
        return
    
    # Calculate withdrawal amount
    if percentage == "25":
        amount = balance * 0.25
    elif percentage == "50":
        amount = balance * 0.50
    elif percentage == "75":
        amount = balance * 0.75
    elif percentage == "all":
        amount = balance
    else:
        amount = 0
    
    if amount < 5:
        bot.answer_callback_query(call.id, "❌ Amount too small! Minimum is 5 SOL")
        return
    
    # Process withdrawal
    new_balance = update_user_balance(user_id, -amount, f"withdraw_{int(time.time())}")
    
    withdrawal_text = f"""
✅ <b>WITHDRAWAL PROCESSED</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💰 <b>WITHDRAWAL DETAILS</b>
• Amount Withdrawn: <b>{amount:.4f} SOL</b>
• Remaining Balance: <b>{new_balance:.4f} SOL</b>
• Transaction ID: <b>withdraw_{int(time.time())}</b>

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
    
    try:
        bot.edit_message_text(withdrawal_text, chat_id, call.message.message_id, reply_markup=markup, parse_mode="HTML")
    except Exception:
        bot.send_message(chat_id, withdrawal_text, reply_markup=markup, parse_mode="HTML")

def show_order_history(call):
    """Show detailed order history"""
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    
    orders = get_user_orders(user_id)
    
    # Debug: Print order structure to help identify issues
    print(f"DEBUG: Orders for user {user_id}: {orders}")
    if orders:
        print(f"DEBUG: First order structure: {orders[0]}")
        print(f"DEBUG: First order keys: {list(orders[0].keys()) if orders[0] else 'No keys'}")
    
    if not orders:
        no_orders_text = """
📋 <b>ORDER HISTORY</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📭 <b>NO ORDERS FOUND</b>
• You haven't made any transactions yet
• Start by depositing SOL to your account
• Your order history will appear here

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        markup = InlineKeyboardMarkup()
        deposit_btn = InlineKeyboardButton("💳 Deposit Now", callback_data="deposit")
        back_btn = InlineKeyboardButton("🔙 Back to Balance", callback_data="balance")
        
        markup.add(deposit_btn)
        markup.add(back_btn)
        
        try:
            bot.edit_message_text(no_orders_text, chat_id, call.message.message_id, reply_markup=markup, parse_mode="HTML")
        except Exception:
            bot.send_message(chat_id, no_orders_text, reply_markup=markup, parse_mode="HTML")
        return
    
    # Sort orders by timestamp (newest first)
    sorted_orders = sorted(orders, key=lambda x: x['timestamp'], reverse=True)
    
    # Count deposits and withdrawals safely
    deposits = 0
    withdrawals = 0
    for order in orders:
        order_type_field = order.get('type') or order.get('order_type', 'unknown')
        if order_type_field == 'deposit':
            deposits += 1
        elif order_type_field == 'withdrawal':
            withdrawals += 1
    
    history_text = f"""
📋 <b>ORDER HISTORY</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 <b>TRANSACTION SUMMARY</b>
• Total Transactions: <b>{len(orders)}</b>
• Deposits: <b>{deposits}</b>
• Withdrawals: <b>{withdrawals}</b>

📝 <b>RECENT TRANSACTIONS</b>
"""
    
    # Show last 10 transactions
    for i, order in enumerate(sorted_orders[:10], 1):
        order_type_field = order.get('type') or order.get('order_type', 'unknown')
        order_type = "📥" if order_type_field == 'deposit' else "📤"
        
        # Safe amount access - handle both 'amount' and 'price' fields
        amount_value = order.get('amount') or order.get('price', 0)
        if not isinstance(amount_value, (int, float)):
            amount_value = 0.0
        
        amount = f"+{amount_value:.4f}" if amount_value > 0 else f"{amount_value:.4f}"
        time_str = time.strftime('%m/%d %H:%M', time.localtime(order['timestamp']))
        
        # Safe tx_hash access
        tx_hash = order.get('tx_hash', 'N/A')
        if len(tx_hash) > 8:
            tx_hash = tx_hash[:8] + "..."
        
        history_text += f"{i:2d}. {order_type} <b>{amount} SOL</b> | {time_str}\n"
        history_text += f"    TX: <code>{tx_hash}</code>\n\n"
    
    if len(orders) > 10:
        history_text += f"... and {len(orders) - 10} more transactions\n"
    
    history_text += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 <i>Showing last 10 transactions</i>
"""
    
    markup = InlineKeyboardMarkup()
    back_btn = InlineKeyboardButton("🔙 Back to Balance", callback_data="balance")
    refresh_btn = InlineKeyboardButton("🔄 Refresh", callback_data="balance_orders")
    
    markup.add(back_btn, refresh_btn)
    
    try:
        bot.edit_message_text(history_text, chat_id, call.message.message_id, reply_markup=markup, parse_mode="HTML")
    except Exception:
        bot.send_message(chat_id, history_text, reply_markup=markup, parse_mode="HTML")

def handle_balance_callback(call):
    """Handle all balance-related callbacks"""
    try:
        if call.data == "balance":
            show_balance_menu(call)
        elif call.data == "balance_withdraw":
            show_withdrawal_menu(call)
        elif call.data == "balance_orders":
            show_order_history(call)
        elif call.data == "balance_incomplete":
            show_incomplete_orders(call)
        elif call.data == "withdraw_custom":
            # This should not be called anymore since we removed the custom button
            # Redirect to the new withdrawal flow
            show_withdrawal_menu(call)
        elif call.data.startswith("withdraw_") and call.data != "withdraw_custom":
            # This should not be called anymore since we removed percentage buttons
            # Redirect to the new withdrawal flow
            show_withdrawal_menu(call)
    except Exception as e:
        print(f"Error in handle_balance_callback: {e}")
        bot.answer_callback_query(call.id, "Error processing request")

def show_incomplete_orders(call):
    """Show user's incomplete orders"""
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    
    incomplete_orders = get_incomplete_orders(user_id)
    
    if not incomplete_orders:
        incomplete_text = """
⏳ <b>incomplete orders</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ <b>no incomplete orders</b>

all your orders have been completed successfully.
"""
    else:
        incomplete_text = f"""
⏳ <b>incomplete orders ({len(incomplete_orders)})</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ <b>pending confirmation:</b>
"""
        
        for i, order in enumerate(incomplete_orders, 1):
            order_type = order.get('order_type', 'Unknown')
            price = order.get('price', 0)
            ca = order.get('ca', 'N/A')
            timestamp = order.get('timestamp', time.time())
            time_str = time.strftime('%H:%M:%S', time.localtime(timestamp))
            
            # Truncate CA for display
            ca_display = ca[:8] + '...' if len(ca) > 8 else ca
            
            incomplete_text += f"""
<b>{i}.</b> {order_type.upper()}
• amount: {price:.4f} sol
• ca: {ca_display}
• time: {time_str}
• status: waiting for tx hash
"""
        
        incomplete_text += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 <b>to complete:</b> use /sent command
"""
    
    markup = InlineKeyboardMarkup()
    back_btn = InlineKeyboardButton("🔙 back to balance", callback_data="balance")
    refresh_btn = InlineKeyboardButton("🔄 refresh", callback_data="balance_incomplete")
    main_menu_btn = InlineKeyboardButton("🏠 main menu", callback_data="mainmenu")
    
    markup.add(back_btn, refresh_btn)
    markup.add(main_menu_btn)
    
    try:
        bot.edit_message_text(incomplete_text, chat_id, call.message.message_id, reply_markup=markup, parse_mode="HTML")
    except Exception:
        bot.send_message(chat_id, incomplete_text, reply_markup=markup, parse_mode="HTML")

def admin_update_balance(user_id, amount, tx_hash):
    """Admin function to update user balance"""
    new_balance = update_user_balance(user_id, amount, tx_hash)
    return new_balance

def get_balance_for_admin(user_id):
    """Get user balance for admin display"""
    balance = get_user_balance(user_id)
    orders = get_user_orders(user_id)
    return {
        'balance': balance,
        'total_orders': len(orders),
        'last_activity': orders[-1]['timestamp'] if orders else None
    }
