import json
import os
import time
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
SIGNATURES_FILE = os.path.join(DATA_DIR, 'signatures.json')
ALARM_STATE_FILE = os.path.join(DATA_DIR, 'alarm_state.json')
WALLETS_FILE = os.path.join(DATA_DIR, 'wallets.json')
USER_STATES_FILE = os.path.join(DATA_DIR, 'user_states.json')

def ensure_data_files():
    """Ensure data directory and required files exist."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        
    for file_path in [SIGNATURES_FILE, ALARM_STATE_FILE, WALLETS_FILE, USER_STATES_FILE]:
        if not os.path.exists(file_path):
            with open(file_path, 'w', encoding='utf-8') as f:
                if 'wallets' in file_path:
                    json.dump([], f)
                elif 'alarm_state' in file_path:
                    json.dump({'is_active': False, 'current_tx': None, 'bot_paused': False, 'pause_start_time': None, 'pause_end_time': None}, f)
                elif 'user_states' in file_path:
                    json.dump({}, f)
                else:
                    json.dump([], f)
    
    # Initialize .gitkeep
    with open(os.path.join(DATA_DIR, '.gitkeep'), 'a') as f:
        pass

# --- User States (Conversation) ---

def get_user_state(chat_id):
    ensure_data_files()
    try:
        with open(USER_STATES_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get(str(chat_id))
    except (FileNotFoundError, json.JSONDecodeError):
        return None

def set_user_state(chat_id, state):
    ensure_data_files()
    try:
        with open(USER_STATES_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except:
        data = {}
        
    if state is None:
        if str(chat_id) in data:
            del data[str(chat_id)]
    else:
        data[str(chat_id)] = state
        
    with open(USER_STATES_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

# --- Wallet Management (Single User / Multi Wallet) ---

def load_wallets():
    """Load wallets from JSON file (Flat list)."""
    ensure_data_files()
    try:
        with open(WALLETS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            # Migration from Multi-user (dict) to Single-user (list)
            if isinstance(data, dict):
                merged_wallets = []
                seen_addresses = set()
                for chat_id, wallets in data.items():
                    for w in wallets:
                        if w['address'] not in seen_addresses:
                            # Add default name if missing
                            if 'name' not in w:
                                w['name'] = f"Ví_{w['address'][:4]}"
                            w['is_active'] = w.get('is_active', True)
                            merged_wallets.append(w)
                            seen_addresses.add(w['address'])
                save_wallets(merged_wallets)
                return merged_wallets
                
            # Ensure is_active, alert_in, alert_out, auto_add_amount, auto_add_name exists for all existing flat wallets
            updated = False
            for w in data:
                if 'is_active' not in w:
                    w['is_active'] = True
                    updated = True
                if 'alert_in' not in w:
                    w['alert_in'] = True
                    updated = True
                if 'alert_out' not in w:
                    w['alert_out'] = True
                    updated = True
                if 'auto_add_min' not in w:
                    # Migrate old auto_add_amount if it exists
                    if w.get('auto_add_amount') is not None:
                        w['auto_add_min'] = w['auto_add_amount'] - 0.05
                        w['auto_add_max'] = w['auto_add_amount'] + 0.05
                    else:
                        w['auto_add_min'] = None
                        w['auto_add_max'] = None
                    updated = True
                if 'auto_add_list' not in w:
                    w['auto_add_list'] = None
                    updated = True
                if 'auto_add_name' not in w:
                    w['auto_add_name'] = None
                    updated = True
            if updated:
                save_wallets(data)
                
            return data
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_wallets(wallets):
    """Save wallets list to JSON file."""
    with open(WALLETS_FILE, 'w', encoding='utf-8') as f:
        json.dump(wallets, f, indent=4)

def add_wallet(address, min_sol=0.0, max_sol=1000000.0, name=None):
    """Add or update a wallet in the flat list."""
    wallets = load_wallets()
    
    if not name:
        name = f"Ví_{address[:4]}"
    
    # Check if wallet already exists
    for i, wallet in enumerate(wallets):
        if wallet['address'] == address:
            return False, f"Ví <code>{address[:8]}...</code> đã tồn tại trong danh sách.", i
    
    # Add new wallet
    wallets.append({
        'address': address,
        'name': name,
        'min_sol': min_sol,
        'max_sol': max_sol,
        'is_active': True,
        'alert_in': True,
        'alert_out': True,
        'auto_add_min': None,
        'auto_add_max': None,
        'auto_add_list': None,
        'auto_add_name': None
    })
    save_wallets(wallets)
    new_index = len(wallets) - 1
    return True, f"Đã thêm ví mới: <code>{address}</code> - {name} - {min_sol} đến {max_sol} SOL.", new_index

def remove_wallet(address):
    """Remove a wallet from the flat list."""
    wallets = load_wallets()
    new_wallets = [w for w in wallets if w['address'] != address]
    
    if len(new_wallets) == len(wallets):
        return False, "Không tìm thấy địa chỉ ví này."
    
    save_wallets(new_wallets)
    return True, "Đã xóa ví khỏi danh sách theo dõi."

def delete_wallet_by_index(index):
    wallets = load_wallets()
    if 0 <= index < len(wallets):
        del wallets[index]
        save_wallets(wallets)
        return True
    return False

def toggle_wallet_state(index):
    wallets = load_wallets()
    if 0 <= index < len(wallets):
        wallets[index]['is_active'] = not wallets[index].get('is_active', True)
        save_wallets(wallets)
        return True, wallets[index]['is_active']
    return False, False

def toggle_alert_in(index):
    wallets = load_wallets()
    if 0 <= index < len(wallets):
        wallets[index]['alert_in'] = not wallets[index].get('alert_in', True)
        save_wallets(wallets)
        return True, wallets[index]['alert_in']
    return False, False

def toggle_alert_out(index):
    wallets = load_wallets()
    if 0 <= index < len(wallets):
        wallets[index]['alert_out'] = not wallets[index].get('alert_out', True)
        save_wallets(wallets)
        return True, wallets[index]['alert_out']
    return False, False

def update_wallet_min(index, min_sol):
    wallets = load_wallets()
    if 0 <= index < len(wallets):
        wallets[index]['min_sol'] = min_sol
        save_wallets(wallets)
        return True
    return False

def update_wallet_max(index, max_sol):
    wallets = load_wallets()
    if 0 <= index < len(wallets):
        wallets[index]['max_sol'] = max_sol
        save_wallets(wallets)
        return True
    return False

def update_wallet_autoadd(index, min_amt, max_amt, exact_list, name):
    wallets = load_wallets()
    if 0 <= index < len(wallets):
        wallets[index]['auto_add_min'] = min_amt
        wallets[index]['auto_add_max'] = max_amt
        wallets[index]['auto_add_list'] = exact_list
        wallets[index]['auto_add_name'] = name
        save_wallets(wallets)
        return True
    return False

# --- Alarm State (Single User / Global) ---

def get_alarm_state():
    """Get global alarm state."""
    ensure_data_files()
    try:
        with open(ALARM_STATE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            # If data is a boolean or somehow corrupted, return default
            if not isinstance(data, dict):
                return {'is_active': False, 'current_tx': None, 'bot_paused': False, 'pause_start_time': None, 'pause_end_time': None}
                
            # If it looks like the old multi-user format (where keys are chat_ids, which are numeric strings)
            # and it doesn't have 'is_active' at the root
            if 'is_active' not in data:
                # Find the first valid state
                for k, v in data.items():
                    if isinstance(v, dict) and 'is_active' in v:
                        state = v
                        with open(ALARM_STATE_FILE, 'w', encoding='utf-8') as wf:
                            json.dump(state, wf, indent=4)
                        return state
                return {'is_active': False, 'current_tx': None, 'bot_paused': False, 'pause_start_time': None, 'pause_end_time': None}
                
            if 'bot_paused' not in data:
                data['bot_paused'] = False
            if 'pause_start_time' not in data:
                data['pause_start_time'] = None
            if 'pause_end_time' not in data:
                data['pause_end_time'] = None
            return data
    except (FileNotFoundError, json.JSONDecodeError):
        return {'is_active': False, 'current_tx': None, 'bot_paused': False, 'pause_start_time': None, 'pause_end_time': None}

def set_alarm_state(is_active, current_tx=None):
    """Set global alarm state."""
    state = get_alarm_state()
    state['is_active'] = is_active
    state['updated_at'] = time.time()
    
    if is_active and current_tx is not None:
        state['current_tx'] = current_tx
        state['spam_message_ids'] = []
        
    with open(ALARM_STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=4)

def toggle_bot_pause():
    """Toggles the global pause state of the bot."""
    state = get_alarm_state()
    current = state.get('bot_paused', False)
    state['bot_paused'] = not current
    with open(ALARM_STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=4)
    return state['bot_paused']

def update_schedule(start_time, end_time):
    """Updates the night mode schedule."""
    state = get_alarm_state()
    state['pause_start_time'] = start_time
    state['pause_end_time'] = end_time
    with open(ALARM_STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=4)

def add_spam_message_id(msg_id):
    """Add a spam message ID to the list to be deleted later."""
    state = get_alarm_state()
    spam_ids = state.get('spam_message_ids', [])
    if msg_id not in spam_ids:
        spam_ids.append(msg_id)
    state['spam_message_ids'] = spam_ids
    with open(ALARM_STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=4)

# --- Signatures ---
def load_signatures():
    ensure_data_files()
    try:
        with open(SIGNATURES_FILE, 'r', encoding='utf-8') as f:
            return set(json.load(f))
    except (json.JSONDecodeError, IOError):
        return set()

def save_signatures(signatures):
    ensure_data_files()
    full_list = sorted(list(signatures))
    sig_list = full_list[-1000:]
    with open(SIGNATURES_FILE, 'w', encoding='utf-8') as f:
        json.dump(sig_list, f)
