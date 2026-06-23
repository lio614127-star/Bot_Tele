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
    from utils.persistence import get_alarm_state
    state = get_alarm_state()
    if state.get('bot_paused', False):
        logger.info("Bot is paused globally. Ignoring webhook.")
        return False, None
        
    pause_start = state.get('pause_start_time')
    pause_end = state.get('pause_end_time')
    if pause_start and pause_end:
        from datetime import datetime
        now_str = datetime.now().strftime("%H:%M")
        is_paused_schedule = False
        if pause_start < pause_end:
            is_paused_schedule = pause_start <= now_str <= pause_end
        else:
            is_paused_schedule = now_str >= pause_start or now_str <= pause_end
            
        if is_paused_schedule:
            logger.info(f"Bot is scheduled paused ({pause_start} - {pause_end}). Ignoring webhook.")
            return False, None
            
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
                
                alert_out = wallet.get('alert_out', True)
                alert_in = wallet.get('alert_in', True)
                
                # Check toggles before alerting
                should_alert = (is_out and alert_out) or (is_in and alert_in)
                
                if should_alert:
                    if wallet['min_sol'] <= amount_sol <= wallet['max_sol']:
                        direction = "OUT (Gửi đi)" if is_out else "IN (Nhận về)"
                        logger.info(f"MATCH: {amount_sol} SOL {direction} - {wallet['name']} ({wallet['address']})")
                        
                        trace_info = ""
                        reply_markup = None
                        
                        if is_out and to_user:
                            from services.rpc_service import get_wallet_info
                            balance, is_new, creation_date = get_wallet_info(to_user)
                            
                            auto_add_amount = wallet.get('auto_add_amount')
                            auto_add_name = wallet.get('auto_add_name')
                            
                            is_auto_added = False
                            if is_new and auto_add_amount is not None and auto_add_name:
                                if abs(amount_sol - auto_add_amount) <= 0.05:
                                    new_name = f"{auto_add_name}_{to_user[:4]}"
                                    from utils.persistence import add_wallet
                                    success, note, new_idx = add_wallet(to_user, 0.0, 1000.0, new_name)
                                    if success:
                                        import threading
                                        from services.helius_service import sync_wallets_to_helius
                                        threading.Thread(target=sync_wallets_to_helius, daemon=True).start()
                                        trace_info = f"\n\n🚨 <b>ĐÃ TỰ ĐỘNG BẮT VÍ CON MỚI!</b>\n👉 Thêm ví: <code>{to_user}</code>\n👉 Tên: {new_name}"
                                        is_auto_added = True
                            
                            if not is_auto_added:
                                trace_info = (
                                    f"\n\n🔍 <b>Phân tích ví nhận:</b>\n"
                                    f"👛 Địa chỉ: <code>{to_user}</code>\n"
                                    f"💰 Số dư: {balance:.4f} SOL\n"
                                    f"📅 Lần đầu h/động: {creation_date} {'(VÍ MỚI)' if is_new else '(Ví Cũ)'}"
                                )
                                reply_markup = {
                                    "inline_keyboard": [
                                        [{"text": f"➕ Thêm làm ví con", "callback_data": f"add_sub_{to_user[:40]}"}],
                                        [{"text": "🛑 Dừng báo động", "callback_data": "stop_alarm"}]
                                    ]
                                }
                        
                        msg_id = send_alarm_message(
                            amount_sol,
                            wallet['address'],
                            signature,
                            wallet_name=wallet['name'],
                            direction=direction,
                            extra_text=trace_info,
                            custom_markup=reply_markup
                        )
                        tx_data = {
                            'wallet_addr': wallet['address'],
                            'wallet_name': wallet['name'],
                            'amount': amount_lamports,
                            'signature': signature,
                            'direction': direction,
                            'first_message_id': msg_id if isinstance(msg_id, int) else None
                        }
                        set_alarm_state(True, tx_data)
                        
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
