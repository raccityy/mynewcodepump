# user_sessions.py

user_sessions = {}

def set_user_price(user_id, price):
    if user_id not in user_sessions:
        user_sessions[user_id] = {}
    user_sessions[user_id]['price'] = price

def get_user_price(user_id):
    return user_sessions.get(user_id, {}).get('price')

def set_user_ca(user_id, ca):
    if user_id not in user_sessions:
        user_sessions[user_id] = {}
    user_sessions[user_id]['ca'] = ca

def get_user_ca(user_id):
    return user_sessions.get(user_id, {}).get('ca')
