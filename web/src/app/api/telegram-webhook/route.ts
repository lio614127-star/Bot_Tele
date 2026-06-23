import { NextResponse } from 'next/server'
import { getBotState, saveBotState, getWallets } from '@/lib/kv'
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
        const webUrl = process.env.VERCEL_URL ? `https://${process.env.VERCEL_URL}` : 'http://localhost:3000'
        await sendMessage(chatId, `🚀 <b>Mạng Nhện Tracer Đã Kết Nối!</b>\n\nToàn bộ hệ thống quản lý ví đã được chuyển lên Web App để sếp theo dõi trực quan và dễ dàng hơn.\n\n👉 <b><a href="${webUrl}">Bấm vào đây để mở Web App</a></b>\n\nCác lệnh khả dụng:\n/status - Xem trạng thái\n/stop - Dừng báo động`)
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
    }
    
    return NextResponse.json({ ok: true })
  } catch (error) {
    console.error(error)
    return NextResponse.json({ ok: false })
  }
}
