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
            to_user = transfer.get('toUserAccount') or transfer.get('toUser')
            amount_lamports = transfer.get('amount', 0)
            amount_sol = amount_lamports / 1_000_000_000.0
            
            # Log all processed transfers for debugging
            logger.debug(f"Processing transfer: {amount_sol} SOL from {from_user} to {to_user}")
            
            # Match against flat wallet list
            matched_this_transfer = False
            for wallet in wallets:
                if not wallet.get('is_active', True):
                    continue
                
                is_out = (from_user == wallet['address'])
                is_in = (to_user == wallet['address'])
                
                if is_out or is_in:
                    if wallet['min_sol'] <= amount_sol <= wallet['max_sol']:
                        direction = "OUT (Gửi đi)" if is_out else "IN (Nhận về)"
                        logger.info(f"MATCH: {amount_sol} SOL {direction} - {wallet['name']} ({wallet['address']})")
                        
                        # Trigger global alarm
                        tx_data = {
                            'wallet_addr': wallet['address'],
                            'wallet_name': wallet['name'],
                            'amount': amount_lamports,
                            'signature': signature,
                            'direction': direction
                        }
                        set_alarm_state(True, tx_data)
                        
                        # Send alert
                        send_alarm_message(amount_sol, wallet['address'], signature, wallet_name=wallet['name'], direction=direction)
                        
                        # Ensure alarm thread is running
                        start_alarm_thread()
                        
                        match_found = True
                        last_signature = signature
                        matched_this_transfer = True
                        break 
            
            if not matched_this_transfer:
                # Optional: log why it didn't match if it's from a known wallet but out of range
                for wallet in wallets:
                    if from_user == wallet['address']:
                        logger.info(f"IGNORED: {amount_sol} SOL from {wallet['name']} is outside range [{wallet['min_sol']}, {wallet['max_sol']}]")
            
            if match_found: break

        signatures.add(signature)
    
    save_signatures(signatures)
    return match_found, last_signature
