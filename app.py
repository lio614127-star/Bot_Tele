import os
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
    'TELEGRAM_SECRET', 'TARGET_WALLET', 'ALARM_INTERVAL', 'MAX_ALARM_DURATION'
]
missing_vars = [v for v in CRITICAL_VARS if not os.getenv(v)]
if missing_vars and not os.getenv('PYTEST_CURRENT_TEST'):
    logger.critical(f"UNABLE TO START: Missing mandatory environment variables: {', '.join(missing_vars)}")
    exit(1)
elif missing_vars:
    logger.warning(f"Missing environment variables during test: {', '.join(missing_vars)}")

SECRET_TOKEN = os.getenv('SECRET_TOKEN')

@app.route('/')
def health_check():
    return jsonify({"status": "healthy", "service": "CryptoAlarmBot"}), 200

@app.route('/webhook/<token>', methods=['POST'])
def helius_webhook(token):
    """
    Secured Helius webhook endpoint.
    """
    # Dynamic token check to support environment updates and testing
    if token != os.getenv('SECRET_TOKEN'):
        log_unauthorized(request.remote_addr, request.path)
        return jsonify({"error": "Unauthorized"}), 404

    payload = request.json
    if not payload:
        logger.error("Received webhook with no JSON payload")
        return jsonify({"error": "No payload"}), 400

    logger.info(f"Received webhook at secured endpoint")
    
    is_match, signature = process_helius_webhook(payload)
    
    if is_match:
        # Start the alarm
        start_alarm_thread()
        return jsonify({"status": "match_found", "signature": signature}), 200
    else:
        return jsonify({"status": "processed", "message": "No matching outgoing SOL transfers found"}), 200

@app.route(f'/telegram/{os.getenv("TELEGRAM_SECRET")}', methods=['POST'])
def telegram_webhook():
    """
    Secured Telegram webhook endpoint.
    """
    payload = request.json
    if not payload:
        return jsonify({"error": "No payload"}), 400
        
    handle_webhook(payload)
    return jsonify({"status": "ok"}), 200

# Error handler for unauthorized paths (optional but good for logging)
@app.errorhandler(404)
def unauthorized_access(e):
    # If the secret token is wrong, it will likely hit a 404
    log_unauthorized(request.remote_addr, request.path)
    return jsonify({"error": "Not Found"}), 404

if __name__ == '__main__':
    # Startup Recovery
    state = get_alarm_state()
    if state.get('is_active'):
        start_time = state.get('start_time')
        max_duration = int(os.getenv('MAX_ALARM_DURATION', 1200))
        if start_time and (datetime.now().timestamp() - start_time) < max_duration:
            logger.info("Resuming active alarm from saved state.")
            start_alarm_thread()
            # Defer sending resumed message slightly to ensure thread is ready
            send_message("⚠️ <b>Alarm resumed after restart</b>\nBot đã khởi động lại và tiếp tục báo động cho bạn.")
        else:
            logger.info("Active alarm state found but exceeded duration. Resetting.")
            set_alarm_state(False)

    # Send startup notification
    send_startup_message()
    
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG_MODE', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)
