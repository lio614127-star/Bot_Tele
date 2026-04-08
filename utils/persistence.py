import json
import os
import time
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
SIGNATURES_FILE = os.path.join(DATA_DIR, 'signatures.json')
ALARM_STATE_FILE = os.path.join(DATA_DIR, 'alarm_state.json')
WALLETS_FILE = os.path.join(DATA_DIR, 'wallets.json')

def ensure_data_files():
    """Ensure data directory and required files exist."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        
    for file_path in [SIGNATURES_FILE, ALARM_STATE_FILE, WALLETS_FILE]:
        if not os.path.exists(file_path):
            with open(file_path, 'w', encoding='utf-8') as f:
                if 'wallets' in file_path:
                    json.dump([], f)
                elif 'state' in file_path:
                    json.dump({'is_active': False, 'current_tx': None}, f)
                else:
                    json.dump([], f)
    
    # Initialize .gitkeep
    with open(os.path.join(DATA_DIR, '.gitkeep'), 'a') as f:
        pass

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
                            merged_wallets.append(w)
                            seen_addresses.add(w['address'])
                save_wallets(merged_wallets)
                return merged_wallets
                
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
    for wallet in wallets:
        if wallet['address'] == address:
            wallet['min_sol'] = min_sol
            wallet['max_sol'] = max_sol
            wallet['name'] = name
            save_wallets(wallets)
            return True, f"Đã cập nhật ví '{name}'."
    
    # Add new wallet
    wallets.append({
        'address': address,
        'name': name,
        'min_sol': min_sol,
        'max_sol': max_sol
    })
    save_wallets(wallets)
    return True, f"Đã thêm ví mới: '{name}'"

def remove_wallet(address):
    """Remove a wallet from the flat list."""
    wallets = load_wallets()
    new_wallets = [w for w in wallets if w['address'] != address]
    
    if len(new_wallets) == len(wallets):
        return False, "Không tìm thấy địa chỉ ví này."
    
    save_wallets(new_wallets)
    return True, "Đã xóa ví khỏi danh sách theo dõi."

# --- Alarm State (Single User / Global) ---

def get_alarm_state():
    """Get global alarm state."""
    ensure_data_files()
    try:
        with open(ALARM_STATE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Migration from Multi-user (dict) to Single-user (object)
            if isinstance(data, dict) and any(isinstance(v, dict) for v in data.values()):
                # Take the first active state or default
                admin_id = os.getenv('TELEGRAM_CHAT_ID')
                state = data.get(admin_id, list(data.values())[0] if data else {'is_active': False})
                with open(ALARM_STATE_FILE, 'w', encoding='utf-8') as wf:
                    json.dump(state, wf)
                return state
                
            return data
    except (FileNotFoundError, json.JSONDecodeError):
        return {'is_active': False, 'current_tx': None}

def set_alarm_state(is_active, current_tx=None):
    """Set global alarm state."""
    state = {
        'is_active': is_active,
        'current_tx': current_tx,
        'updated_at': time.time()
    }
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
