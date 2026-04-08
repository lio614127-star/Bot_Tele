import os
from utils.persistence import load_signatures, save_signatures, set_alarm_state, load_wallets
from utils.logger import setup_logger, log_transaction_match

logger = setup_logger()

def process_helius_webhook(payload):
    """
    Processes Helius webhook payload for native SOL transfers.
    Returns: (bool, str) - (is_match, signature)
    """
    wallets = load_wallets()
    
    if not wallets:
        logger.warning("Không có ví nào trong danh sách theo dõi (wallets.json)")
        return False, None

    # Helius webhooks often have a list of entries
    if not isinstance(payload, list):
        payload = [payload]

    signatures = load_signatures()
    match_found = False
    match_signature = None

    for entry in payload:
        signature = entry.get('signature')
        
        # 1. Deduplication check
        if signature in signatures:
            continue
            
        native_transfers = entry.get('nativeTransfers', [])
        for transfer in native_transfers:
            from_user = transfer.get('fromUser')
            to_user = transfer.get('toUser')
            # Lamports to SOL conversion (10^9)
            amount_sol = transfer.get('amount', 0) / 1_000_000_000.0
            
            # Check against all configured wallets
            for wallet in wallets:
                target_address = wallet.get('address')
                min_sol = wallet.get('min_sol', 0.0)
                max_sol = wallet.get('max_sol', 1000000.0)
                
                # Decision: ALERT on OUTGOING SOL from target wallet
                if from_user == target_address:
                    if min_sol <= amount_sol <= max_sol:
                        logger.info(f"Detected outgoing transfer of {amount_sol} SOL from {from_user} to {to_user}")
                        
                        # Add wallet info to transfer data for the alarm message if needed
                        transfer['wallet_name'] = target_address
                        
                        # Log match and store signature
                        log_transaction_match(signature, amount_sol, transfer)
                        signatures.add(signature)
                        save_signatures(signatures)
                        
                        # Update alarm state to active
                        set_alarm_state(True, transaction_data=transfer)
                        
                        match_found = True
                        match_signature = signature
                        break
            
            if match_found:
                break
        
        if match_found:
            break
            
    return match_found, match_signature
