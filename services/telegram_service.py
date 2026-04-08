import os
import requests
import json
from datetime import datetime
from utils.logger import setup_logger
from utils.persistence import set_alarm_state, get_alarm_state, load_wallets, add_wallet, remove_wallet

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
        f"🚀 <b>Crypto Alarm Bot Online</b>\n"
        f"Time: <code>{now}</code>\n"
        f"Status: Monitoring active\n\n"
        f"Dùng /list để xem danh sách ví đang theo dõi."
    )
    return send_message(text)

def send_alarm_message(amount, wallet, signature):
    """
    Sends an interactive alarm message.
    """
    solscan_url = f"https://solscan.io/tx/{signature}"
    text = (
        f"🚨 <b>BÁO ĐỘNG! PHÁT HIỆN GIAO DỊCH</b>\n\n"
        f"💰 <b>Số lượng:</b> {amount:.4f} SOL\n"
        f"📤 <b>Hướng:</b> Gửi đi (OUT)\n"
        f"👛 <b>Ví liên quan:</b> <code>{wallet}</code>\n\n"
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
    # Solana uses base58 (no 0, O, I, l)
    base58_chars = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    return all(c in base58_chars for c in address)

def handle_webhook(payload):
    """
    Handles incoming updates from Telegram (Messages and Callback Queries).
    """
    allowed_chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    # Check if it's a message or callback_query
    message = payload.get('message')
    callback_query = payload.get('callback_query')
    
    if message:
        chat_id = str(message.get('chat', {}).get('id'))
        if chat_id != allowed_chat_id:
            logger.warning(f"Ignored message from unauthorized Chat ID: {chat_id} (Allowed: {allowed_chat_id})")
            return
            
        text = message.get('text', '')
        
        if text.startswith('/start'):
            send_message(
                "👋 Chào bạn! Bot đang hoạt động.\n\n"
                "<b>Các lệnh điều khiển:</b>\n"
                "📋 /list - Xem danh sách ví\n"
                "➕ /add &lt;wallet&gt; &lt;min&gt; &lt;max&gt; - Thêm ví\n"
                "<i>(Gửi nhiều dòng để thêm nhiều ví cùng lúc)</i>\n"
                "🗑️ /remove &lt;wallet&gt; - Xóa ví\n"
                "📊 /status - Kiểm tra trạng thái bot\n"
                "🛑 /stop - Dừng báo động khẩn cấp"
            )
            
        elif text == '/stop':
            set_alarm_state(False)
            send_message("🛑 <b>Đã dừng báo động</b> theo lệnh của bạn.")
            
        elif text == '/status':
            state = get_alarm_state()
            is_active = state.get('is_active', False)
            status_text = "🔔 <b>ĐANG BÁO ĐỘNG</b>" if is_active else "😴 <b>Đang nghỉ ngơi</b>"
            wallets = load_wallets()
            
            msg = f"📊 <b>Trạng thái:</b> {status_text}\n"
            msg += f"👥 <b>Số lượng ví:</b> {len(wallets)}"
            
            if is_active and state.get('current_tx'):
                tx = state.get('current_tx')
                msg += f"\n\n🔥 <b>Ví đang kích hoạt:</b>\n<code>{tx.get('wallet_name', 'N/A')}</code>"
                msg += f"\n💰 <b>Số lượng:</b> {tx.get('amount', 0) / 1_000_000_000.0:.4f} SOL"
            
            send_message(msg)
            
        elif text == '/list':
            wallets = load_wallets()
            if not wallets:
                send_message("<b>📋 Danh sách ví trống.</b>\nDùng lệnh <code>/add &lt;wallet&gt; &lt;min&gt; &lt;max&gt;</code> để thêm.")
                return
                
            msg = "📋 <b>Danh sách ví đang theo dõi:</b>\n\n"
            for i, w in enumerate(wallets, 1):
                msg += f"{i}. <code>{w['address']}</code>\n   ({w['min_sol']} - {w['max_sol']} SOL)\n\n"
            send_message(msg)
            
        elif text.startswith('/add'):
            lines = text.strip().split('\n')
            results = []
            
            for line in lines:
                parts = line.split()
                # Skip first part if it's the command /add
                if parts[0] == '/add':
                    parts = parts[1:]
                
                if len(parts) < 3:
                    if len(lines) == 1:
                        send_message("❌ <b>Sai cú pháp.</b> Dùng:\n<code>/add &lt;wallet&gt; &lt;min&gt; &lt;max&gt;</code>")
                        return
                    continue 
                
                address = parts[0]
                try:
                    min_sol = float(parts[1])
                    max_sol = float(parts[2])
                    
                    # Validation
                    if not is_valid_solana_address(address):
                        results.append(f"❌ <code>{address[:8]}...</code>: Địa chỉ không hợp lệ.")
                        continue
                    if min_sol < 0 or max_sol < 0:
                        results.append(f"❌ <code>{address[:8]}...</code>: SOL không được âm.")
                        continue
                    if min_sol > max_sol:
                        results.append(f"❌ <code>{address[:8]}...</code>: Min ({min_sol}) > Max ({max_sol}).")
                        continue

                    success, note = add_wallet(address, min_sol, max_sol)
                    if success:
                        emoji = "✨" if "thêm" in note.lower() else "🔄"
                        results.append(f"{emoji} <code>{address[:8]}...</code>: {min_sol}-{max_sol} SOL ({note})")
                    else:
                        results.append(f"❌ <code>{address[:8]}...</code>: {note}")
                except ValueError:
                    results.append(f"❌ <code>{line[:20]}...</code>: Min/Max phải là số.")
            
            if results:
                send_message("📝 <b>KẾT QUẢ CẬP NHẬT:</b>\n" + "\n".join(results))
            else:
                send_message("❌ <b>Không tìm thấy dữ liệu hợp lệ để xử lý.</b>")
                
        elif text.startswith('/remove'):
            parts = text.split()
            if len(parts) < 2:
                send_message("❌ <b>Sai cú pháp.</b> Dùng:\n<code>/remove &lt;wallet&gt;</code>")
                return
            
            address = parts[1]
            if not is_valid_solana_address(address):
                send_message("❌ <b>Địa chỉ ví không hợp lệ.</b>")
                return

            success, note = remove_wallet(address)
            if success:
                send_message(f"🗑️ <b>Thành công!</b>\n{note}\nVí: <code>{address}</code>")
            else:
                send_message(f"❌ <b>Lỗi:</b> {note}")
            
    elif callback_query:
        chat_id = str(callback_query.get('from', {}).get('id'))
        if chat_id != allowed_chat_id:
            return
            
        data = callback_query.get('data')
        if data == 'stop_alarm':
            set_alarm_state(False)
            # Answer callback query to remove loading state in Telegram UI
            callback_id = callback_query.get('id')
            bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
            url = f"{TELEGRAM_API_URL}{bot_token}/answerCallbackQuery"
            requests.post(url, json={"callback_query_id": callback_id, "text": "Đã dừng báo động!"})
            send_message("🛑 Đã dừng báo động từ nút bấm.")
