import json
import os
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
SIGNATURES_FILE = os.path.join(DATA_DIR, 'signatures.json')
ALARM_STATE_FILE = os.path.join(DATA_DIR, 'alarm_state.json')
WALLETS_FILE = os.path.join(DATA_DIR, 'wallets.json')

def ensure_data_files():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    
    if not os.path.exists(SIGNATURES_FILE):
        with open(SIGNATURES_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f)
            
    if not os.path.exists(ALARM_STATE_FILE):
        with open(ALARM_STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump({'alarm_active': False}, f)
            
    if not os.path.exists(WALLETS_FILE):
        with open(WALLETS_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f)

def load_signatures():
    ensure_data_files()
    try:
        with open(SIGNATURES_FILE, 'r', encoding='utf-8') as f:
            return set(json.load(f))
    except (json.JSONDecodeError, IOError):
        return set()

def save_signatures(signatures):
    ensure_data_files()
    # Keep only target number of signatures
    full_list = sorted(list(signatures))
    sig_list = full_list[-1000:]
    with open(SIGNATURES_FILE, 'w', encoding='utf-8') as f:
        json.dump(sig_list, f)

def get_alarm_state():
    """
    Returns the current alarm state object.
    """
    ensure_data_files()
    try:
        with open(ALARM_STATE_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return {"is_active": False, "start_time": None, "current_tx": None}

def set_alarm_state(is_active, transaction_data=None):
    """
    Updates the alarm state with transaction data and start time if activating.
    """
    state = get_alarm_state()
    # If activating, set start_time if not already active
    if is_active:
        current_state = state if isinstance(state, dict) else {}
        if not current_state.get("is_active"):
            current_state["start_time"] = datetime.now().timestamp()
        current_state["current_tx"] = transaction_data
        current_state["is_active"] = True
        state = current_state
    else:
        state = {
            "is_active": False,
            "start_time": None,
            "current_tx": None
        }
    
    with open(ALARM_STATE_FILE, 'w') as f:
        json.dump(state, f, indent=4)
    return state

def load_wallets():
    ensure_data_files()
    try:
        with open(WALLETS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []

def save_wallets(wallets):
    ensure_data_files()
    with open(WALLETS_FILE, 'w', encoding='utf-8') as f:
        json.dump(wallets, f, indent=4)

def add_wallet(address, min_sol=0.0, max_sol=1000000.0):
    wallets = load_wallets()
    # Check if wallet already exists
    for wallet in wallets:
        if wallet['address'] == address:
            wallet['min_sol'] = min_sol
            wallet['max_sol'] = max_sol
            save_wallets(wallets)
            return True, "Đã cập nhật cấu hình cho ví hiện tại."
    
    # Add new wallet
    wallets.append({
        'address': address,
        'min_sol': min_sol,
        'max_sol': max_sol
    })
    save_wallets(wallets)
    return True, "Đã thêm ví mới vào danh sách theo dõi."

def remove_wallet(address):
    wallets = load_wallets()
    new_wallets = [w for w in wallets if w['address'] != address]
    if len(new_wallets) < len(wallets):
        save_wallets(new_wallets)
        return True, "Đã xóa ví khỏi danh sách theo dõi."
    return False, "Không tìm thấy ví này trong danh sách."
