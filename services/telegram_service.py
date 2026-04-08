import os
import requests
import json
import time
from datetime import datetime
from utils.logger import setup_logger
from utils.persistence import (
    set_alarm_state, get_alarm_state, load_wallets, add_wallet, remove_wallet
)

logger = setup_logger()

# Constants
TELEGRAM_API_URL = "https://api.telegram.org/bot"

def send_message(text, reply_markup=None):
    """
    Sends a message to the configured TELEGRAM_CHAT_ID.
    """
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if not bot_token or not chat_id:
        logger.error("Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID")
        return False
        
    url = f"{TELEGRAM_API_URL}{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    
    if reply_markup:
        payload["reply_markup"] = reply_markup
        
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        return True
    except Exception as e:
        logger.error(f"Failed to send Telegram message: {e}")
        return False

def send_startup_message():
    """
    Sends a startup notification.
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    text = (
        f"🚀 <b>Bot Alarm Online</b>\n"
        f"Time: <code>{now}</code>\n"
        f"Mode: Single-User\n\n"
        f"Dùng /list để xem danh sách ví."
    )
    return send_message(text)

def send_alarm_message(amount, wallet_addr, signature, wallet_name="N/A"):
    """
    Sends an interactive alarm message with wallet name.
    """
    solscan_url = f"https://solscan.io/tx/{signature}"
    text = (
        f"🚨 <b>BÁO ĐỘNG! PHÁT HIỆN GIAO DỊCH</b>\n\n"
        f"🏷️ <b>Tên ví:</b> <b>{wallet_name}</b>\n"
        f"💰 <b>Số lượng:</b> {amount:.4f} SOL\n"
        f"📤 <b>Hướng:</b> OUT (Gửi đi)\n"
        f"👛 <b>Địa chỉ:</b> <code>{wallet_addr}</code>\n\n"
        f"🔗 <a href='{solscan_url}'>Xem trên Solscan</a>"
    )
    
    reply_markup = {
        "inline_keyboard": [[
            {"text": "🛑 Dừng báo động", "callback_data": "stop_alarm"}
        ]]
    }
    
    return send_message(text, reply_markup=reply_markup)

def is_valid_solana_address(address):
    """
    Simple validation for Solana address format.
    """
    if not 32 <= len(address) <= 44:
        return False
    base58_chars = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    return all(c in base58_chars for c in address)

def handle_webhook(payload):
    """
    Handles incoming updates from Telegram.
    """
    admin_id = os.getenv('TELEGRAM_CHAT_ID')
    
    message = payload.get('message')
    callback_query = payload.get('callback_query')
    
    if message:
        chat_id = str(message.get('chat', {}).get('id'))
        if chat_id != admin_id:
            logger.warning(f"Ignored unauthorized chat: {chat_id}")
            return
            
        text = message.get('text', '')
        
        if text.startswith('/start'):
            send_message(
                f"👋 Chào Sếp! Bot đã sẵn sàng.\n\n"
                f"<b>Lệnh điều khiển:</b>\n"
                f"📋 /list - Danh sách ví\n"
                f"➕ /add - Thêm ví (addr min max [tên])\n"
                f"🗑️ /remove - Xóa ví\n"
                f"📊 /status - Trạng thái\n"
                f"🛑 /stop - Dừng báo động"
            )
            
        elif text == '/stop':
            set_alarm_state(False)
            send_message("🛑 <b>Đã dừng báo động.</b>")
            
        elif text == '/status':
            state = get_alarm_state()
            is_active = state.get('is_active', False)
            status_text = "🔔 <b>ĐANG BÁO ĐỘNG</b>" if is_active else "😴 <b>Đang theo dõi...</b>"
            wallets = load_wallets()
            
            msg = f"📊 <b>Trạng thái:</b> {status_text}\n"
            msg += f"👥 <b>Số ví đang theo dõi:</b> {len(wallets)}"
            
            if is_active and state.get('current_tx'):
                tx = state.get('current_tx')
                msg += f"\n\n🔥 <b>Ví kích hoạt:</b>\n<b>{tx.get('wallet_name', 'N/A')}</b>\n<code>{tx.get('wallet_addr', 'N/A')}</code>"
            
            send_message(msg)
            
        elif text == '/list':
            wallets = load_wallets()
            if not wallets:
                send_message("📋 Danh sách ví trống.")
                return
                
            msg = "📋 <b>Danh sách ví theo dõi:</b>\n\n"
            for i, w in enumerate(wallets, 1):
                msg += f"{i}. <b>{w.get('name', 'N/A')}</b>\n   <code>{w['address']}</code>\n   ({w['min_sol']} - {w['max_sol']} SOL)\n\n"
            send_message(msg)
            
        elif text.startswith('/add'):
            lines = text.strip().split('\n')
            results = []
            
            for line in lines:
                parts = line.split()
                if parts[0] == '/add': parts = parts[1:]
                if len(parts) < 3:
                    if len(lines) == 1: send_message("❌ **Sai cú pháp:** <code>/add addr min max [tên]</code>")
                    continue 
                
                address = parts[0]
                try:
                    min_sol, max_sol = float(parts[1]), float(parts[2])
                    # Name is everything from parts[3:]
                    name = " ".join(parts[3:]) if len(parts) > 3 else None
                    
                    if not is_valid_solana_address(address):
                        results.append(f"❌ <code>{address[:8]}</code>: Địa chỉ sai.")
                        continue

                    success, note = add_wallet(address, min_sol, max_sol, name)
                    results.append(f"✅ {note}")
                except ValueError:
                    results.append(f"❌ <code>{line[:15]}</code>: Lỗi số.")
            
            if results:
                send_message("📝 **Kết quả cập nhật:**\n" + "\n".join(results))
                
        elif text.startswith('/remove'):
            parts = text.split()
            if len(parts) < 2:
                send_message("❌ **Cú pháp:** <code>/remove addr</code>")
                return
            
            address = parts[1]
            success, note = remove_wallet(address)
            send_message(f"{'🗑️' if success else '❌'} {note}")

    elif callback_query:
        chat_id = str(callback_query.get('from', {}).get('id'))
        if chat_id != admin_id: return
            
        if callback_query.get('data') == 'stop_alarm':
            set_alarm_state(False)
            callback_id = callback_query.get('id')
            url = f"{TELEGRAM_API_URL}{os.getenv('TELEGRAM_BOT_TOKEN')}/answerCallbackQuery"
            requests.post(url, json={"callback_query_id": callback_id, "text": "Đã dừng!"})
            send_message("🛑 **Báo động đã dừng.**")
