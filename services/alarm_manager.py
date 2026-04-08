import time
import os
import threading
from datetime import datetime
from utils.persistence import get_alarm_state, set_alarm_state
from services.telegram_service import send_alarm_message, send_message
from utils.logger import setup_logger

logger = setup_logger()

# Global state to prevent duplicate threads
_alarm_thread = None
_thread_lock = threading.Lock()

def start_alarm_thread():
    """
    Starts the background alarm thread if it's not already running.
    """
    global _alarm_thread
    with _thread_lock:
        if _alarm_thread is None or not _alarm_thread.is_alive():
            _alarm_thread = threading.Thread(target=alarm_worker_loop, daemon=True)
            _alarm_thread.start()
            logger.info("Background alarm thread started.")

def alarm_worker_loop():
    """
    The background loop that spams alerts and checks for auto-stop.
    """
    logger.info("Alarm worker loop entering...")
    
    # Reload config frequently in case of env changes during dev
    # In production, these are usually static
    interval = int(os.getenv('ALARM_INTERVAL', 2))
    max_duration = int(os.getenv('MAX_ALARM_DURATION', 1200)) # Default 20 mins
    
    while True:
        state = get_alarm_state()
        
        if not state.get('is_active'):
            logger.info("Alarm inactive. Worker loop exiting.")
            break
            
        # Check for auto-stop
        start_time = state.get('start_time')
        if start_time:
            elapsed = datetime.now().timestamp() - start_time
            if elapsed > max_duration:
                logger.info(f"Alarm exceeded max duration ({elapsed:.0f}s > {max_duration}s). Auto-stopping.")
                set_alarm_state(False)
                send_message("🚨 <b>Auto-stop activated</b>\nBáo động đã tự động dừng sau 20 phút để đảm bảo an toàn.")
                break
        
        # Send alert
        tx_data = state.get('current_tx')
        if tx_data:
            # tx_data expected to be a dict with 'amount', 'wallet', 'signature'
            send_alarm_message(
                amount=tx_data.get('amount', 0),
                wallet=tx_data.get('wallet', 'Unknown'),
                signature=tx_data.get('signature', '')
            )
        else:
            logger.warning("Alarm active but no transaction data found.")
            
        time.sleep(interval)
