import { NextResponse } from 'next/server'
import { getBotState, saveBotState, getWallets, saveWallets } from '@/lib/kv'
import { sendMessage, editMessage, answerCallbackQuery } from '@/lib/telegram'

export async function POST(req: Request) {
  try {
    const payload = await req.json()
    const message = payload.message
    const callback_query = payload.callback_query
    
    // Determine chat ID and authorize
    const adminId = process.env.TELEGRAM_CHAT_ID
    
    if (message) {
      const chatId = message.chat.id.toString()
      if (chatId !== adminId) return NextResponse.json({ ok: true }) // Ignore unauthorized
        
      const text = message.text || ''
      
      if (text.startsWith('/start') || text.startsWith('/web')) {
        const webUrl = 'https://bot-tele-eosin.vercel.app' // Hardcode for reliability
        await sendMessage(chatId, `🚀 <b>Mạng Nhện Tracer Đã Kết Nối!</b>\n\nToàn bộ hệ thống quản lý ví đã được tự động hóa và chuyển lên Web App để sếp dễ dàng thao tác (Bản đồ Bubblemaps, Lọc nâng cao, ...).\n\n👉 <b><a href="${webUrl}">BẤM VÀO ĐÂY ĐỂ MỞ WEB APP</a></b>\n\nCác lệnh khả dụng:\n/status - Xem trạng thái\n/wallets - Quản lý ví\n/stop - Dừng báo động\n/web - Mở Web App`)
      }
      
      if (text.startsWith('/add')) {
        const parts = text.split(' ')
        if (parts.length < 2) {
          await sendMessage(chatId, "❌ Sai cú pháp! Vui lòng dùng: `/add <địa chỉ ví> <tên ví>`")
        } else {
          const address = parts[1]
          const name = parts.slice(2).join(' ') || 'Ví mới'
          const wallets = await getWallets()
          if (wallets.some(w => w.address === address)) {
            await sendMessage(chatId, `⚠️ Ví <b>${address.slice(0,4)}...${address.slice(-4)}</b> đã tồn tại trong hệ thống!`)
          } else {
            wallets.push({ address, name, min_sol: 0, max_sol: 0, is_active: true, alert_in: true, alert_out: true, auto_add_min: null, auto_add_max: null, auto_add_list: null, auto_add_name: null })
            await saveWallets(wallets)
            await sendMessage(chatId, `✅ <b>Đã thêm ví thành công!</b>\n\nTên: ${name}\nĐịa chỉ: <code>${address}</code>\n\nDùng lệnh /wallets để quản lý hoặc mở Web App.`)
          }
        }
      } else if (!text.startsWith('/') && text.length >= 32 && text.length <= 44 && /^[1-9A-HJ-NP-Za-km-z]+$/.test(text)) {
        // Direct address paste
        const address = text
        const name = 'Ví mới'
        const wallets = await getWallets()
        if (wallets.some(w => w.address === address)) {
          await sendMessage(chatId, `⚠️ Ví <b>${address.slice(0,4)}...${address.slice(-4)}</b> đã tồn tại trong hệ thống!`)
        } else {
          wallets.push({ address, name, min_sol: 0, max_sol: 0, is_active: true, alert_in: true, alert_out: true, auto_add_min: null, auto_add_max: null, auto_add_list: null, auto_add_name: null })
          await saveWallets(wallets)
          await sendMessage(chatId, `✅ <b>Đã nhận diện và thêm ví tự động!</b>\n\nĐịa chỉ: <code>${address}</code>\n\nDùng lệnh /wallets để xem danh sách.`)
        }
      }
      
      if (text === '/wallets') {
        const wallets = await getWallets()
        if (wallets.length === 0) {
          await sendMessage(chatId, "📭 Danh sách ví trống! Gửi `/add <địa chỉ>` hoặc paste thẳng địa chỉ ví vào đây để thêm.")
        } else {
          await sendMessage(chatId, `📋 <b>Danh sách ví đang theo dõi (${wallets.length}):</b>`)
          for (let i = 0; i < wallets.length; i++) {
            const w = wallets[i]
            const statusIcon = w.is_active ? '🟢 Đang theo dõi' : '⏸ Đã tạm dừng'
            const msg = `💼 <b>Tên ví:</b> ${w.name}\n📍 <b>Địa chỉ:</b> <code>${w.address}</code>\n📊 <b>Giới hạn:</b> ${w.min_sol} - ${w.max_sol} SOL\n📈 <b>Trạng thái:</b> ${statusIcon}`
            const replyMarkup = {
              inline_keyboard: [
                [
                  { text: w.is_active ? "⏸ Tạm dừng" : "▶️ Bật lại", callback_data: `toggle_wallet_${w.address}` },
                  { text: "🗑 Xóa ví", callback_data: `delete_wallet_${w.address}` }
                ]
              ]
            }
            await sendMessage(chatId, msg, replyMarkup)
          }
        }
      }
      
      if (text === '/stop') {
        const state = await getBotState()
        state.is_active = false
        await saveBotState(state)
        await sendMessage(chatId, "🛑 <b>Đã dừng báo động.</b>")
      }
      
      if (text === '/status') {
        const state = await getBotState()
        const wallets = await getWallets()
        
        let statusText = "😴 <b>Đang theo dõi (Âm thầm)...</b>"
        if (state.bot_paused) statusText = "💤 <b>ĐANG NGỦ (Tạm dừng toàn cục)</b>"
        else if (state.combat_mode) statusText = "⚔️ <b>THỰC CHIẾN (Tàng hình báo động)</b>"
        else if (state.is_active) statusText = "🔔 <b>ĐANG BÁO ĐỘNG</b>"
        
        let msg = `📊 <b>Trạng thái:</b> ${statusText}\n`
        msg += `👥 <b>Số ví đang theo dõi:</b> ${wallets.length}\n\n`
        msg += `Dùng Web App để quản lý chi tiết.`
        
        const combatText = state.combat_mode ? "🔙 Tắt Thực Chiến" : "⚔️ Bật Thực Chiến"
        const replyMarkup = {
          inline_keyboard: [[{ text: combatText, callback_data: "toggle_combat" }]]
        }
        await sendMessage(chatId, msg, replyMarkup)
      }
      
    } else if (callback_query) {
      const chatId = callback_query.message?.chat?.id?.toString()
      if (chatId !== adminId) return NextResponse.json({ ok: true })
        
      const data = callback_query.data
      const messageId = callback_query.message?.message_id
      const callbackId = callback_query.id
      
      if (data === 'stop_alarm') {
        const state = await getBotState()
        state.is_active = false
        await saveBotState(state)
        await answerCallbackQuery(callbackId, "✅ Đã dừng báo động!")
        await editMessage(chatId, messageId, "<i>🛑 Báo động đã được sếp tắt.</i>")
      }
      
      if (data === 'toggle_combat') {
        const state = await getBotState()
        state.combat_mode = !state.combat_mode
        await saveBotState(state)
        
        const statusText = state.combat_mode ? "⚔️ <b>THỰC CHIẾN (Tàng hình báo động)</b>" : "😴 <b>Đang theo dõi (Âm thầm)...</b>"
        const combatText = state.combat_mode ? "🔙 Tắt Thực Chiến" : "⚔️ Bật Thực Chiến"
        const replyMarkup = {
          inline_keyboard: [[{ text: combatText, callback_data: "toggle_combat" }]]
        }
        await editMessage(chatId, messageId, `📊 <b>Trạng thái:</b> ${statusText}`, replyMarkup)
        await answerCallbackQuery(callbackId, state.combat_mode ? "Đã BẬT Thực chiến" : "Đã TẮT Thực chiến")
      }
      if (data.startsWith('toggle_wallet_')) {
        const addr = data.replace('toggle_wallet_', '')
        const wallets = await getWallets()
        const w = wallets.find(x => x.address === addr)
        if (w) {
          w.is_active = !w.is_active
          await saveWallets(wallets)
          const statusIcon = w.is_active ? '🟢 Đang theo dõi' : '⏸ Đã tạm dừng'
          const msg = `💼 <b>Tên ví:</b> ${w.name}\n📍 <b>Địa chỉ:</b> <code>${w.address}</code>\n📊 <b>Giới hạn:</b> ${w.min_sol} - ${w.max_sol} SOL\n📈 <b>Trạng thái:</b> ${statusIcon}`
          const replyMarkup = {
            inline_keyboard: [
              [
                { text: w.is_active ? "⏸ Tạm dừng" : "▶️ Bật lại", callback_data: `toggle_wallet_${w.address}` },
                { text: "🗑 Xóa ví", callback_data: `delete_wallet_${w.address}` }
              ]
            ]
          }
          await editMessage(chatId, messageId, msg, replyMarkup)
          await answerCallbackQuery(callbackId, w.is_active ? "Đã bật theo dõi ví" : "Đã tạm dừng ví")
        }
      }

      if (data.startsWith('delete_wallet_')) {
        const addr = data.replace('delete_wallet_', '')
        const wallets = await getWallets()
        const newWallets = wallets.filter(x => x.address !== addr)
        await saveWallets(newWallets)
        await editMessage(chatId, messageId, `🗑 <i>Đã xóa ví <code>${addr}</code> khỏi danh sách.</i>`)
        await answerCallbackQuery(callbackId, "Đã xóa ví thành công!")
      }
    }
    
    return NextResponse.json({ ok: true })
  } catch (error) {
    console.error(error)
    return NextResponse.json({ ok: false })
  }
}
