import threading
import time
import os
import requests
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
    
    interval = int(os.getenv('ALARM_INTERVAL', 1))
    max_duration = int(os.getenv('MAX_ALARM_DURATION', 1200))
    
    spam_count = 0
    last_tx_signature = None
    
    while True:
        state = get_alarm_state()
        
        if state.get('is_active'):
            updated_at = state.get('updated_at', 0)
            elapsed = time.time() - updated_at
            
            if elapsed > max_duration:
                logger.info("Alarm duration exceeded. Auto-stopping.")
                set_alarm_state(False)
            else:
                tx = state.get('current_tx', {})
                name = tx.get('wallet_name', 'N/A')
                addr = tx.get('wallet_addr', 'N/A')
                signature = tx.get('signature', '')
                
                if signature != last_tx_signature:
                    spam_count = 0
                    last_tx_signature = signature
                    
                spam_count += 1
                from datetime import datetime
                now_ms = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                
                reply_markup = {
                    "inline_keyboard": [[
                        {"text": "🛑 Dừng báo động", "callback_data": "stop_alarm"}
                    ]]
                }
                msg_text = f"🚨 <b>BÁO ĐỘNG LIÊN TỤC ({spam_count})</b>\nVí: <b>{name}</b>\nĐịa chỉ: <code>{addr}</code>\n⏰ <code>{now_ms}</code>"
                
                msg_id = send_message(msg_text, reply_markup=reply_markup)
                from utils.persistence import add_spam_message_id
                if isinstance(msg_id, int):
                    add_spam_message_id(msg_id)
        
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
