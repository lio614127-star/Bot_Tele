import TelegramBot from 'node-telegram-bot-api'

const token = process.env.TELEGRAM_BOT_TOKEN || ''
export const bot = new TelegramBot(token)

export async function sendMessage(chatId: string | number, text: string, replyMarkup?: any) {
  try {
    const options: any = { parse_mode: 'HTML', disable_web_page_preview: true }
    if (replyMarkup) {
      options.reply_markup = replyMarkup
    }
    const msg = await bot.sendMessage(chatId, text, options)
    return msg.message_id
  } catch (error) {
    console.error('Failed to send message:', error)
    return null
  }
}

export async function editMessage(chatId: string | number, messageId: number, text: string, replyMarkup?: any) {
  try {
    const options: any = {
      chat_id: chatId,
      message_id: messageId,
      parse_mode: 'HTML',
      disable_web_page_preview: true
    }
    if (replyMarkup) {
      options.reply_markup = replyMarkup
    }
    await bot.editMessageText(text, options)
  } catch (error) {
    console.error('Failed to edit message:', error)
  }
}

export async function answerCallbackQuery(callbackQueryId: string, text: string = '') {
  try {
    await bot.answerCallbackQuery(callbackQueryId, { text })
  } catch (error) {
    console.error('Failed to answer callback query:', error)
  }
}
