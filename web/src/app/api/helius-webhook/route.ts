import { NextResponse } from 'next/server'
import { getBotState, saveBotState, getWallets, saveWallets, Wallet } from '@/lib/kv'
import { sendMessage } from '@/lib/telegram'

const LAMPORTS_PER_SOL = 1e9

export async function POST(req: Request) {
  try {
    const transactions = await req.json()
    if (!Array.isArray(transactions)) return NextResponse.json({ ok: true })
      
    const state = await getBotState()
    const wallets = await getWallets()
    const adminId = process.env.TELEGRAM_CHAT_ID || ''
    
    // Check global pause
    if (state.bot_paused) return NextResponse.json({ ok: true })
      
    for (const tx of transactions) {
      if (tx.type !== 'TRANSFER' && tx.type !== 'UNKNOWN') continue
      
      const sig = tx.signature
      const nativeTransfers = tx.nativeTransfers || []
      
      for (const wallet of wallets) {
        if (!wallet.is_active) continue
        
        let amountOut = 0
        let toUser = ''
        let isOut = false
        
        // Find if our wallet sent SOL
        for (const transfer of nativeTransfers) {
          if (transfer.fromUserAccount === wallet.address) {
            isOut = true
            amountOut += transfer.amount
            toUser = transfer.toUserAccount
          }
        }
        
        const amountSol = amountOut / LAMPORTS_PER_SOL
        
        // Check limits
        if (isOut && amountSol >= wallet.min_sol && amountSol <= wallet.max_sol && wallet.alert_out) {
          
          // Auto-add logic
          let extraText = ''
          if (wallet.auto_add_name) {
            let shouldAdd = false
            const isRange = wallet.auto_add_min !== null && wallet.auto_add_max !== null
            const isList = wallet.auto_add_list && wallet.auto_add_list.length > 0
            
            if (isRange) {
              if (amountSol >= wallet.auto_add_min! && amountSol <= wallet.auto_add_max!) shouldAdd = true
            } else if (isList) {
              for (const exact of wallet.auto_add_list!) {
                if (Math.abs(amountSol - exact) <= 0.05) shouldAdd = true
              }
            }
            
            if (shouldAdd) {
              const exists = wallets.some(w => w.address === toUser)
              if (!exists) {
                const newWallet: Wallet = {
                  address: toUser,
                  name: `${wallet.auto_add_name} (Auto)`,
                  min_sol: wallet.min_sol,
                  max_sol: wallet.max_sol,
                  is_active: true,
                  alert_in: true,
                  alert_out: true,
                  auto_add_min: null,
                  auto_add_max: null,
                  auto_add_list: null,
                  auto_add_name: null
                }
                wallets.push(newWallet)
                await saveWallets(wallets)
                extraText = `\n✅ <b>Hệ thống đã bắt được ví con và tự động lưu:</b> <code>${toUser}</code>\n`
              } else {
                extraText = `\n⚠️ <i>Đích đến <code>${toUser}</code> là ví cũ đã được lưu trước đó.</i>\n`
              }
            }
          }
          
          // Send alarm based on Combat Mode
          if (state.combat_mode) {
             const webUrl = process.env.VERCEL_URL ? `https://${process.env.VERCEL_URL}` : 'http://localhost:3000'
             const msg = `⚠️ <b>[THỰC CHIẾN] Dev vừa chuyển tiền ra ngoài!</b>\n\n` +
                         `👤 <b>Ví:</b> ${wallet.name} (<code>${wallet.address}</code>)\n` +
                         `💸 <b>Số lượng:</b> ${amountSol.toFixed(4)} SOL\n` +
                         `➡️ <b>Đích đến:</b> <code>${toUser}</code>\n` +
                         `${extraText}\n` +
                         `👉 <a href="${webUrl}">Mở Bản Đồ Mạng Nhện</a> để truy vết!`
             await sendMessage(adminId, msg)
          } else {
             const msg = `🚨 <b>BÁO ĐỘNG! Dev vừa tẩu tán SOL!</b> 🚨\n\n` +
                         `👤 <b>Ví:</b> ${wallet.name} (<code>${wallet.address}</code>)\n` +
                         `💸 <b>Số lượng:</b> ${amountSol.toFixed(4)} SOL\n` +
                         `➡️ <b>Đích đến:</b> <code>${toUser}</code>\n` +
                         `${extraText}`
             
             const markup = {
               inline_keyboard: [[{ text: "🛑 Dừng Báo Động 🛑", callback_data: "stop_alarm" }]]
             }
             
             // Set state to active so user knows it alarmed
             state.is_active = true
             await saveBotState(state)
             
             // Serverless Spam Simulation (Hú còi inh ỏi)
             // Vercel function timeout is 10-60s, we spam 5 times with 1.5s delay
             for (let i = 0; i < 5; i++) {
               await sendMessage(adminId, msg, markup)
               await new Promise(resolve => setTimeout(resolve, 1500))
             }
          }
        }
      }
    }
    
    return NextResponse.json({ ok: true })
  } catch (error) {
    console.error(error)
    return NextResponse.json({ ok: false })
  }
}
