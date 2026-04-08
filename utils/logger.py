import logging
import os
from datetime import datetime

LOG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'app.log')

def setup_logger():
    # Ensure data directory exists for log file
    data_dir = os.path.dirname(LOG_FILE)
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger('CryptoAlarmBot')

def log_unauthorized(ip, endpoint):
    logger = logging.getLogger('CryptoAlarmBot')
    logger.warning(f"UNAUTHORIZED ACCESS ATTEMPT: IP={ip}, Endpoint={endpoint}, Time={datetime.now()}")

def log_transaction_match(signature, amount, transfer_details):
    logger = logging.getLogger('CryptoAlarmBot')
    logger.info(f"MATCH FOUND: Signature={signature}, Amount={amount} SOL. Details: {transfer_details}")
