import threading
import time
import os
from utils.persistence import get_alarm_state, set_alarm_state
from services.telegram_service import send_message
from utils.logger import setup_logger

logger = setup_logger()

# Shared global state
alarm_thread = None
alarm_lock = threading.Lock()

def alarm_worker_loop():
    """
    Background worker that runs the alarm loop for the single user.
    """
    logger.info("Alarm worker loop started (Single-User).")
    
    interval = int(os.getenv('ALARM_INTERVAL', 10))
    max_duration = int(os.getenv('MAX_ALARM_DURATION', 1200))
    
    while True:
        state = get_alarm_state()
        
        if state.get('is_active'):
            updated_at = state.get('updated_at', 0)
            elapsed = time.time() - updated_at
            
            if elapsed > max_duration:
                logger.info("Alarm duration exceeded. Auto-stopping.")
                set_alarm_state(False)
                send_message("ℹ️ **Báo động đã tự động dừng** (hết thời gian tối đa).")
            else:
                # Trigger actual sound/notification
                tx = state.get('current_tx', {})
                name = tx.get('wallet_name', 'N/A')
                addr = tx.get('wallet_addr', 'N/A')
                
                logger.info(f"ALARM ACTIVE: {name} ({addr})")
                send_message(f"🔔 <b>ĐANG CÓ BIẾN!</b>\nVí: <b>{name}</b>\nĐịa chỉ: <code>{addr}</code>")
        
        time.sleep(interval)

def start_alarm_thread():
    """
    Starts the background alarm thread if it's not already running.
    """
    global alarm_thread
    with alarm_lock:
        if alarm_thread is None or not alarm_thread.is_alive():
            alarm_thread = threading.Thread(target=alarm_worker_loop, daemon=True)
            alarm_thread.start()
            logger.info("Alarm thread spawned.")
