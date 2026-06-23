import os
import requests
import json
import time
import re
from datetime import datetime
from utils.logger import setup_logger
from utils.persistence import (
    set_alarm_state, get_alarm_state, load_wallets, add_wallet, remove_wallet,
    get_user_state, set_user_state, toggle_wallet_state, delete_wallet_by_index,
    update_wallet_min, update_wallet_max, toggle_alert_in, toggle_alert_out,
    update_schedule, update_wallet_autoadd
)
from services.helius_service import sync_wallets_to_helius

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
        data = response.json()
        if data.get('ok'):
            return data.get('result', {}).get('message_id', True)
        return True
    except Exception as e:
        logger.error(f"Failed to send Telegram message: {e}")
        return False

def edit_message(message_id, text, reply_markup=None):
    """Edits an existing message."""
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    url = f"{TELEGRAM_API_URL}{bot_token}/editMessageText"
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    requests.post(url, json=payload, timeout=10)

def send_startup_message():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    text = (
        f"🚀 <b>Bot Alarm Online</b>\n"
        f"Time: <code>{now}</code>\n"
        f"Mode: Single-User\n\n"
        f"Dùng /wallets để xem danh sách ví."
    )
    return send_message(text)

def send_alarm_message(amount, wallet_addr, signature, wallet_name="N/A", direction="OUT (Gửi đi)", extra_text="", custom_markup=None):
    solscan_url = f"https://solscan.io/tx/{signature}"
    text = (
        f"🚨 <b>BÁO ĐỘNG! PHÁT HIỆN GIAO DỊCH</b>\n\n"
        f"🏷️ <b>Tên ví:</b> <b>{wallet_name}</b>\n"
        f"💰 <b>Số lượng:</b> {amount:.4f} SOL\n"
        f"🧭 <b>Hướng:</b> {direction}\n"
        f"👛 <b>Địa chỉ:</b> <code>{wallet_addr}</code>\n"
    )
    
    if extra_text:
        text += extra_text
        
    text += f"\n\n🔗 <a href='{solscan_url}'>Xem trên Solscan</a>"
    
    if custom_markup:
        reply_markup = custom_markup
    else:
        reply_markup = {
            "inline_keyboard": [[
                {"text": "🛑 Dừng báo động", "callback_data": "stop_alarm"}
            ]]
        }
    return send_message(text, reply_markup=reply_markup)

def is_valid_solana_address(address):
    if not 32 <= len(address) <= 44:
        return False
    base58_chars = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    return all(c in base58_chars for c in address)

def render_wallets_list():
    wallets = load_wallets()
    
    from utils.persistence import get_alarm_state
    state = get_alarm_state()
    bot_paused = state.get('bot_paused', False)
    
    if bot_paused:
        msg = "<b>🔴 BOT ĐANG NGỦ (TẠM DỪNG TOÀN CỤC)</b>\n<i>(Bot sẽ không nhận bất kỳ thông báo nào)</i>\n\n"
    else:
        msg = "<b>🟢 BOT ĐANG HOẠT ĐỘNG BÌNH THƯỜNG</b>\n\n"
        
    msg += f"<b>Tổng số ví đang theo dõi: {len(wallets)} / 100000</b>\n"
    msg += "✅ - Ví đang hoạt động\n"
    msg += "⏸️ - Bạn đã tạm dừng ví này\n\n"
    
    if not wallets:
        msg += "<i>Danh sách ví trống. Dùng /add để thêm.</i>"
    else:
        for i, w in enumerate(wallets):
            icon = "✅" if w.get('is_active', True) else "⏸️"
            name = w.get('name', 'N/A')
            msg += f"{icon} /w_{i}\n<code>{w['address']}</code> ({name})\n"
            
    reply_markup = None
    if bot_paused:
        reply_markup = {"inline_keyboard": [[{"text": "🟢 Đánh thức Bot (Bật lại)", "callback_data": "toggle_power"}]]}
        
    return msg, reply_markup

def render_wallet_detail(index):
    wallets = load_wallets()
    if index < 0 or index >= len(wallets):
        return "❌ Không tìm thấy ví này.", None
        
    w = wallets[index]
    is_active = w.get('is_active', True)
    alert_in = w.get('alert_in', True)
    alert_out = w.get('alert_out', True)
    
    msg = f"💼 <b>Tên ví:</b> {w.get('name', 'N/A')}\n"
    msg += f"📍 <b>Địa chỉ:</b> <code>{w['address']}</code>\n"
    msg += f"📊 <b>Giới hạn:</b> {w['min_sol']} - {w['max_sol']} SOL\n"
    msg += f"🟢 <b>Trạng thái:</b> {'Đang theo dõi (✅)' if is_active else 'Tạm dừng (⏸️)'}\n"
    
    auto_amt = w.get('auto_add_amount')
    auto_name = w.get('auto_add_name')
    if auto_amt is not None and auto_name:
        msg += f"🤖 <b>Auto-Add:</b> {auto_amt} SOL -> <code>{auto_name}</code>"
    else:
        msg += f"🤖 <b>Auto-Add:</b> Tắt"
    
    toggle_text = "⏸️ Tạm dừng" if is_active else "▶️ Tiếp tục"
    in_text = "✅ Nhận (IN)" if alert_in else "❌ Nhận (IN)"
    out_text = "✅ Gửi (OUT)" if alert_out else "❌ Gửi (OUT)"
    
    reply_markup = {
        "inline_keyboard": [
            [{"text": f"📝 Min: {w['min_sol']}", "callback_data": f"edit_min_{index}"}, 
             {"text": f"📝 Max: {w['max_sol']}", "callback_data": f"edit_max_{index}"}],
            [{"text": in_text, "callback_data": f"toggle_in_{index}"}, 
             {"text": out_text, "callback_data": f"toggle_out_{index}"}],
            [{"text": "🤖 Cài Auto-Add Ví Con", "callback_data": f"setup_autoadd_{index}"}],
            [{"text": toggle_text, "callback_data": f"toggle_{index}"}, 
             {"text": "🗑️ Xóa ví", "callback_data": f"delete_{index}"}],
            [{"text": "⬅️ Quay lại danh sách", "callback_data": "back_to_wallets"}]
        ]
    }
    return msg, reply_markup

def handle_webhook(payload):
    admin_id = os.getenv('TELEGRAM_CHAT_ID')
    message = payload.get('message')
    callback_query = payload.get('callback_query')
    
    if message:
        chat_id = str(message.get('chat', {}).get('id'))
        if chat_id != admin_id: return
            
        text = message.get('text', '')
        user_state = get_user_state(chat_id)
        
        # Handle active conversation state first
        if user_state and not text.startswith('/'):
            if user_state == 'WAITING_ADD':
                lines = text.strip().split('\n')
                results = []
                has_success = False
                added_indices = []
                for line in lines:
                    parts = line.split()
                    if len(parts) < 3:
                        results.append(f"❌ <code>{line[:15]}...</code>: Thiếu tham số.")
                        continue
                    
                    address = parts[0]
                    try:
                        min_sol, max_sol = float(parts[1]), float(parts[2])
                        name = " ".join(parts[3:]) if len(parts) > 3 else None
                        if not is_valid_solana_address(address):
                            results.append(f"❌ <code>{address[:8]}...</code>: Địa chỉ sai.")
                            continue
                        success, note, new_idx = add_wallet(address, min_sol, max_sol, name)
                        if success:
                            has_success = True
                            results.append(f"✅ {note}")
                            added_indices.append(new_idx)
                        else:
                            results.append(f"❌ {note}")
                    except ValueError:
                        results.append(f"❌ <code>{line[:15]}...</code>: Lỗi số min/max.")
                
                if results:
                    if has_success:
                        sync_success, sync_note = sync_wallets_to_helius()
                        results.append(f"\n🔄 <b>Helius Sync:</b>\n{sync_note}")
                        
                    reply_markup = None
                    if added_indices:
                        wallets = load_wallets()
                        keyboard = []
                        for idx in added_indices:
                            if idx < len(wallets):
                                w = wallets[idx]
                                keyboard.append([{"text": f"⚙️ Quản lý: {w.get('name', 'Ví mới')}", "callback_data": f"manage_{idx}"}])
                        if keyboard:
                            reply_markup = {"inline_keyboard": keyboard}
                            
                    send_message("📝 **Kết quả cập nhật:**\n" + "\n".join(results), reply_markup=reply_markup)
                set_user_state(chat_id, None)
                return
                
            elif user_state == 'WAITING_REMOVE':
                address = text.strip()
                success, note = remove_wallet(address)
                if success:
                    sync_success, sync_note = sync_wallets_to_helius()
                    note += f"\n\n🔄 <b>Helius Sync:</b>\n{sync_note}"
                send_message(f"{'🗑️' if success else '❌'} {note}")
                set_user_state(chat_id, None)
                return
                
            elif user_state.startswith('EDIT_MIN_'):
                index = int(user_state.split('_')[2])
                try:
                    min_sol = float(text.strip())
                    if update_wallet_min(index, min_sol):
                        send_message(f"✅ Đã cập nhật Min SOL thành: {min_sol}.")
                        msg, reply_markup = render_wallet_detail(index)
                        send_message(msg, reply_markup)
                    else:
                        send_message("❌ Lỗi: Không tìm thấy ví.")
                except ValueError:
                    send_message("❌ Lỗi định dạng số.")
                set_user_state(chat_id, None)
                return
                
            elif user_state.startswith('EDIT_MAX_'):
                index = int(user_state.split('_')[2])
                try:
                    max_sol = float(text.strip())
                    if update_wallet_max(index, max_sol):
                        send_message(f"✅ Đã cập nhật Max SOL thành: {max_sol}.")
                        msg, reply_markup = render_wallet_detail(index)
                        send_message(msg, reply_markup)
                    else:
                        send_message("❌ Lỗi: Không tìm thấy ví.")
                except ValueError:
                    send_message("❌ Lỗi định dạng số.")
                set_user_state(chat_id, None)
                return
                
            elif user_state.startswith('WAITING_AUTOADD_'):
                index = int(user_state.split('_')[2])
                if text.strip().lower() == 'off' or text.strip().lower() == 'tắt':
                    update_wallet_autoadd(index, None, None)
                    send_message("✅ Đã tắt tính năng Auto-Add cho ví này.")
                else:
                    parts = text.strip().split()
                    if len(parts) >= 2:
                        try:
                            amt = float(parts[0])
                            name = " ".join(parts[1:])
                            update_wallet_autoadd(index, amt, name)
                            send_message(f"✅ Đã cấu hình Auto-Add: Nếu ví đích mới nhận đúng ~{amt} SOL, sẽ tự động lưu với tên '{name}'.")
                        except ValueError:
                            send_message("❌ Định dạng số SOL không hợp lệ.")
                    else:
                        send_message("❌ Vui lòng nhập đúng cú pháp: `Số_SOL Tên_Ví`")
                        
                msg, reply_markup = render_wallet_detail(index)
                send_message(msg, reply_markup)
                set_user_state(chat_id, None)
                return
                
            elif user_state == 'WAITING_SCHEDULE':
                if text.strip().lower() == 'off' or text.strip().lower() == 'tắt':
                    update_schedule(None, None)
                    send_message("✅ Đã TẮT tính năng Hẹn giờ đi ngủ. Bot sẽ hoạt động 24/24.")
                else:
                    parts = text.strip().split()
                    if len(parts) == 2:
                        import re
                        time_pattern = re.compile(r"^(0[0-9]|1[0-9]|2[0-3]):[0-5][0-9]$")
                        if time_pattern.match(parts[0]) and time_pattern.match(parts[1]):
                            update_schedule(parts[0], parts[1])
                            send_message(f"✅ Đã lưu lịch trình ngủ: Từ {parts[0]} đến {parts[1]}.")
                        else:
                            send_message("❌ Định dạng giờ không hợp lệ. Phải là HH:MM.")
                    else:
                        send_message("❌ Cú pháp sai. Vui lòng nhập: `HH:MM HH:MM`")
                set_user_state(chat_id, None)
                return

        # Handle commands
        if text.startswith('/start'):
            send_message(
                f"👋 Chào Sếp! Bot đã sẵn sàng.\n\n"
                f"<b>Lệnh điều khiển:</b>\n"
                f"📋 /wallets - Quản lý danh sách ví\n"
                f"➕ /add - Thêm ví mới\n"
                f"🗑️ /remove - Xóa ví bằng địa chỉ\n"
                f"📊 /status - Trạng thái báo động\n"
                f"🛑 /stop - Dừng báo động\n"
                f"⏰ /schedule - Cài đặt giờ đi ngủ (Bot tự tắt)"
            )
        elif text == '/stop':
            set_alarm_state(False)
            send_message("🛑 <b>Đã dừng báo động.</b>")
            
        elif text == '/status':
            state = get_alarm_state()
            bot_paused = state.get('bot_paused', False)
            is_active = state.get('is_active', False)
            
            if bot_paused:
                status_text = "💤 <b>ĐANG NGỦ (Tạm dừng toàn cục)</b>"
            elif is_active:
                status_text = "🔔 <b>ĐANG BÁO ĐỘNG</b>"
            else:
                status_text = "😴 <b>Đang theo dõi...</b>"
                
            wallets = load_wallets()
            
            msg = f"📊 <b>Trạng thái:</b> {status_text}\n"
            msg += f"👥 <b>Số ví đang theo dõi:</b> {len(wallets)}"
            
            if is_active and state.get('current_tx'):
                tx = state.get('current_tx')
                msg += f"\n\n🔥 <b>Ví kích hoạt:</b>\n<b>{tx.get('wallet_name', 'N/A')}</b>\n<code>{tx.get('wallet_addr', 'N/A')}</code>"
                
            power_text = "🟢 Đánh thức Bot (Bật)" if bot_paused else "🔴 Tắt Bot (Đi ngủ)"
            reply_markup = {"inline_keyboard": [[{"text": power_text, "callback_data": "toggle_power"}]]}
            send_message(msg, reply_markup=reply_markup)
            
        elif text == '/schedule':
            state = get_alarm_state()
            pause_start = state.get('pause_start_time')
            pause_end = state.get('pause_end_time')
            
            msg = "⏰ <b>CÀI ĐẶT LỊCH TRÌNH NGỦ (AUTO-PAUSE)</b>\n\n"
            if pause_start and pause_end:
                msg += f"💤 <b>Đang bật:</b> Bot sẽ tự ngủ từ <code>{pause_start}</code> đến <code>{pause_end}</code>.\n\n"
            else:
                msg += f"☀️ <b>Đang tắt:</b> Bot hoạt động 24/24.\n\n"
                
            msg += (
                "👉 Để cài đặt, hãy nhập thời gian bắt đầu và kết thúc (Giờ 24h, định dạng HH:MM).\n"
                "Ví dụ 1: <code>01:00 06:00</code>\n"
                "Ví dụ 2: <code>23:30 07:00</code>\n\n"
                "👉 Để tắt tính năng này, hãy nhắn: <code>off</code>"
            )
            set_user_state(chat_id, 'WAITING_SCHEDULE')
            reply_markup = {"inline_keyboard": [[{"text": "❌ Hủy", "callback_data": "cancel_action"}]]}
            send_message(msg, reply_markup=reply_markup)
            
        elif text == '/list' or text == '/wallets':
            msg, reply_markup = render_wallets_list()
            send_message(msg, reply_markup=reply_markup)
            
        elif text.startswith('/w_'):
            match = re.match(r'/w_(\d+)', text)
            if match:
                index = int(match.group(1))
                msg, reply_markup = render_wallet_detail(index)
                send_message(msg, reply_markup)
                
        elif text.startswith('/add'):
            set_user_state(chat_id, 'WAITING_ADD')
            reply_markup = {"inline_keyboard": [[{"text": "❌ Hủy", "callback_data": "cancel_action"}]]}
            send_message(
                "📝 <b>Thêm ví mới</b>\n"
                "Vui lòng gửi danh sách ví. Gửi mỗi ví trên 1 dòng theo cấu trúc:\n\n"
                "<code>Địa_Chỉ_Ví Min_SOL Max_SOL Tên_Ví</code>\n\n"
                "Ví dụ:\n<code>6TTQDxeg... 1.5 3.0 Ví_Dev_2</code>",
                reply_markup=reply_markup
            )
            
        elif text.startswith('/remove'):
            set_user_state(chat_id, 'WAITING_REMOVE')
            reply_markup = {"inline_keyboard": [[{"text": "❌ Hủy", "callback_data": "cancel_action"}]]}
            send_message("📝 <b>Xóa ví</b>\nVui lòng gửi địa chỉ ví cần xóa:", reply_markup=reply_markup)

    elif callback_query:
        chat_id = str(callback_query.get('message', {}).get('chat', {}).get('id'))
        if chat_id != admin_id: return
        
        data = callback_query.get('data')
        message_id = callback_query.get('message', {}).get('message_id')
        callback_id = callback_query.get('id')
        
        def answer(txt=""):
            url = f"{TELEGRAM_API_URL}{os.getenv('TELEGRAM_BOT_TOKEN')}/answerCallbackQuery"
            requests.post(url, json={"callback_query_id": callback_id, "text": txt})
            
        if data == 'stop_alarm':
            state = get_alarm_state()
            spam_ids = list(state.get('spam_message_ids', []))
            tx = state.get('current_tx', {})
            first_msg_id = tx.get('first_message_id')
            
            # Dọn dẹp trạng thái ngay lập tức
            set_alarm_state(False)
            
            # Trả lời nhanh để tắt hiệu ứng loading của nút bấm
            answer("✅ Đã dừng và đang dọn dẹp tin nhắn!")
            
            # Xóa tin nhắn ngầm để không bị timeout
            bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
            def delete_worker(spam_list, first_id, c_id, token):
                import requests
                for spam_id in spam_list:
                    try:
                        del_url = f"{TELEGRAM_API_URL}{token}/deleteMessage"
                        requests.post(del_url, json={"chat_id": c_id, "message_id": spam_id}, timeout=5)
                    except:
                        pass
                
                if first_id:
                    try:
                        edit_url = f"{TELEGRAM_API_URL}{token}/editMessageReplyMarkup"
                        requests.post(edit_url, json={"chat_id": c_id, "message_id": first_id}, timeout=5)
                    except:
                        pass
            
            import threading
            threading.Thread(target=delete_worker, args=(spam_ids, first_msg_id, chat_id, bot_token), daemon=True).start()
            
        elif data == 'cancel_action':
            set_user_state(chat_id, None)
            edit_message(message_id, "❌ <i>Đã hủy thao tác.</i>")
            answer()
            
        elif data == 'toggle_power':
            from utils.persistence import toggle_bot_pause
            is_paused = toggle_bot_pause()
            
            if is_paused:
                answer("🔴 Đã TẮT bot. Hệ thống sẽ bỏ qua mọi giao dịch.")
            else:
                answer("🟢 Đã BẬT bot. Hệ thống bắt đầu theo dõi trở lại.")
                
            # Cập nhật lại màn hình status nếu đang ở màn hình status
            state = get_alarm_state()
            bot_paused = state.get('bot_paused', False)
            is_active = state.get('is_active', False)
            
            if bot_paused:
                status_text = "💤 <b>ĐANG NGỦ (Tạm dừng toàn cục)</b>"
            elif is_active:
                status_text = "🔔 <b>ĐANG BÁO ĐỘNG</b>"
            else:
                status_text = "😴 <b>Đang theo dõi...</b>"
                
            wallets = load_wallets()
            msg = f"📊 <b>Trạng thái:</b> {status_text}\n"
            msg += f"👥 <b>Số ví đang theo dõi:</b> {len(wallets)}"
            
            if is_active and state.get('current_tx'):
                tx = state.get('current_tx')
                msg += f"\n\n🔥 <b>Ví kích hoạt:</b>\n<b>{tx.get('wallet_name', 'N/A')}</b>\n<code>{tx.get('wallet_addr', 'N/A')}</code>"
                
            power_text = "🟢 Đánh thức Bot (Bật)" if bot_paused else "🔴 Tắt Bot (Đi ngủ)"
            reply_markup = {"inline_keyboard": [[{"text": power_text, "callback_data": "toggle_power"}]]}
            
            try:
                edit_message(message_id, msg, reply_markup)
            except:
                pass
                
        elif data == 'back_to_wallets':
            set_user_state(chat_id, None)
            msg, reply_markup = render_wallets_list()
            edit_message(message_id, msg, reply_markup)
            answer()
            
        elif data.startswith('delete_'):
            index = int(data.split('_')[1])
            if delete_wallet_by_index(index):
                sync_wallets_to_helius()
                edit_message(message_id, "🗑️ <i>Đã xóa ví thành công!</i>")
                # Gửi lại list
                msg, reply_markup = render_wallets_list()
                send_message(msg, reply_markup=reply_markup)
            else:
                edit_message(message_id, "❌ Lỗi: Không tìm thấy ví.")
            answer()
            
        elif data.startswith('toggle_') and not data.startswith('toggle_in_') and not data.startswith('toggle_out_'):
            index = int(data.split('_')[1])
            success, is_active = toggle_wallet_state(index)
            if success:
                msg, reply_markup = render_wallet_detail(index)
                edit_message(message_id, msg, reply_markup)
            answer()
            
        elif data.startswith('manage_'):
            index = int(data.split('_')[1])
            msg, reply_markup = render_wallet_detail(index)
            send_message(msg, reply_markup)
            answer()
            
        elif data.startswith('edit_min_'):
            index = int(data.split('_')[2])
            set_user_state(chat_id, f'EDIT_MIN_{index}')
            reply_markup = {"inline_keyboard": [[{"text": "⬅️ Hủy", "callback_data": "cancel_action"}]]}
            send_message("✏️ Vui lòng nhập số Min SOL mới. Ví dụ: <code>0.5</code>", reply_markup=reply_markup)
            answer()
            
        elif data.startswith('edit_max_'):
            index = int(data.split('_')[2])
            set_user_state(chat_id, f'EDIT_MAX_{index}')
            reply_markup = {"inline_keyboard": [[{"text": "⬅️ Hủy", "callback_data": "cancel_action"}]]}
            send_message("✏️ Vui lòng nhập số Max SOL mới. Ví dụ: <code>10.0</code>", reply_markup=reply_markup)
            answer()
            
        elif data.startswith('toggle_in_'):
            index = int(data.split('_')[2])
            success, is_alert_in = toggle_alert_in(index)
            if success:
                msg, reply_markup = render_wallet_detail(index)
                edit_message(message_id, msg, reply_markup)
            answer()
            
        elif data.startswith('toggle_out_'):
            index = int(data.split('_')[2])
            success, is_alert_out = toggle_alert_out(index)
            if success:
                msg, reply_markup = render_wallet_detail(index)
                edit_message(message_id, msg, reply_markup)
            answer()
            
        elif data.startswith('setup_autoadd_'):
            index = int(data.split('_')[2])
            set_user_state(chat_id, f'WAITING_AUTOADD_{index}')
            reply_markup = {"inline_keyboard": [[{"text": "⬅️ Hủy", "callback_data": "cancel_action"}]]}
            send_message(
                "🤖 <b>CÀI ĐẶT AUTO-ADD VÍ CON</b>\n\n"
                "Gửi cho tôi <code>Số_SOL Tên_Ví</code>.\n\n"
                "Ví dụ: Nếu Dev gửi ~2.1 SOL sang một ví MỚI HOÀN TOÀN, bạn muốn lưu nó là 'Ví_Phụ', hãy nhắn:\n"
                "<code>2.1 Vi_Phu</code>\n\n"
                "👉 Để TẮT tính năng này, nhắn: <code>off</code>", 
                reply_markup=reply_markup
            )
            answer()
            
        elif data.startswith('add_sub_'):
            address = data.split('_')[2]
            name = f"Ví_con_{address[:4]}"
            success, note, new_idx = add_wallet(address, 0.0, 1000.0, name)
            if success:
                sync_success, sync_note = sync_wallets_to_helius()
                send_message(f"✅ Đã thêm ví con thành công!\n{note}")
                # Hủy nút Thêm ví con trên tin nhắn cũ để tránh bấm 2 lần
                try:
                    import copy
                    current_markup = callback_query.get('message', {}).get('reply_markup')
                    if current_markup:
                        new_markup = copy.deepcopy(current_markup)
                        # Bỏ nút add_sub đi
                        new_markup['inline_keyboard'] = [row for row in new_markup['inline_keyboard'] if not any(btn.get('callback_data', '').startswith('add_sub_') for btn in row)]
                        edit_message(message_id, callback_query.get('message', {}).get('text'), new_markup)
                except Exception as e:
                    pass
            else:
                send_message(f"❌ Lỗi thêm ví: {note}")
            answer()
