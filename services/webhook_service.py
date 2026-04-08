import os
from utils.persistence import load_signatures, save_signatures, set_alarm_state, load_wallets
from utils.logger import setup_logger

logger = setup_logger()

from services.telegram_service import send_alarm_message
from services.alarm_manager import start_alarm_thread

def process_helius_webhook(payload):
    """
    Processes Helius webhook for single-user, multi-wallet configuration.
    """
    wallets = load_wallets() # Flat list
    
    if not isinstance(payload, list):
        payload = [payload]

    signatures = load_signatures()
    match_found = False
    last_signature = None

    for entry in payload:
        signature = entry.get('signature')
        if not signature or signature in signatures:
            continue
            
        native_transfers = entry.get('nativeTransfers', [])
        for transfer in native_transfers:
            from_user = transfer.get('fromUserAccount') or transfer.get('fromUser')
            amount_lamports = transfer.get('amount', 0)
            amount_sol = amount_lamports / 1_000_000_000.0
            
            # Match against flat wallet list
            for wallet in wallets:
                if from_user == wallet['address']:
                    if wallet['min_sol'] <= amount_sol <= wallet['max_sol']:
                        logger.info(f"MATCH: {amount_sol} SOL từ {wallet['name']} ({from_user})")
                        
                        # Trigger global alarm
                        tx_data = {
                            'wallet_addr': from_user,
                            'wallet_name': wallet['name'],
                            'amount': amount_lamports,
                            'signature': signature
                        }
                        set_alarm_state(True, tx_data)
                        
                        # Send alert
                        send_alarm_message(amount_sol, from_user, signature, wallet_name=wallet['name'])
                        
                        # Ensure alarm thread is running
                        start_alarm_thread()
                        
                        match_found = True
                        last_signature = signature
                        break 
            
            if match_found: break

        signatures.add(signature)
    
    save_signatures(signatures)
    return match_found, last_signature
