import os
import time
from datetime import datetime
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from utils.logger import setup_logger, log_unauthorized
from services.webhook_service import process_helius_webhook
from services.telegram_service import handle_webhook, send_startup_message, send_message
from services.alarm_manager import start_alarm_thread
from utils.persistence import get_alarm_state, set_alarm_state

# Load environment variables
load_dotenv()

app = Flask(__name__)
logger = setup_logger()

# Fail-fast check for critical variables
CRITICAL_VARS = [
    'TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_ID', 'SECRET_TOKEN', 
    'TELEGRAM_SECRET', 'ALARM_INTERVAL', 'MAX_ALARM_DURATION'
]
missing_vars = [v for v in CRITICAL_VARS if not os.getenv(v)]
if missing_vars and not os.getenv('PYTEST_CURRENT_TEST'):
    logger.critical(f"UNABLE TO START: Missing mandatory environment variables: {', '.join(missing_vars)}")
    exit(1)

SECRET_TOKEN = os.getenv('SECRET_TOKEN')

@app.route('/')
def health_check():
    return jsonify({"status": "healthy", "service": "CryptoAlarmBot"}), 200

@app.route('/webhook/<token>', methods=['POST'])
def helius_webhook(token):
    """
    Secured Helius webhook endpoint.
    """
    if token != os.getenv('SECRET_TOKEN'):
        log_unauthorized(request.remote_addr, request.path)
        return jsonify({"error": "Unauthorized"}), 404

    payload = request.json
    if not payload:
        return jsonify({"error": "No payload"}), 400

    is_match, signature = process_helius_webhook(payload)
    
    if is_match:
        return jsonify({"status": "match_found", "signature": signature}), 200
    else:
        return jsonify({"status": "processed", "message": "No matching transfers"}), 200

@app.route(f'/telegram/{os.getenv("TELEGRAM_SECRET")}', methods=['POST'])
def telegram_webhook():
    payload = request.json
    if not payload:
        return jsonify({"error": "No payload"}), 400
    handle_webhook(payload)
    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    # Startup Recovery (Single-User)
    state = get_alarm_state()
    if state.get('is_active'):
        updated_at = state.get('updated_at')
        max_duration = int(os.getenv('MAX_ALARM_DURATION', 1200))
        
        if updated_at and (time.time() - updated_at) < max_duration:
            logger.info("Resuming active alarm from saved state.")
            start_alarm_thread()
            send_message("⚠️ **Bot đã khởi động lại và tiếp tục báo động cho bạn.**")
        else:
            set_alarm_state(False)

    # Send startup notification to Admin
    send_startup_message()
    
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
