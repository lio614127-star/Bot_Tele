import { Redis } from '@upstash/redis'

export const redis = new Redis({
  url: process.env.KV_REST_API_URL || '',
  token: process.env.KV_REST_API_TOKEN || '',
})

export interface Wallet {
  address: string
  min_sol: number
  max_sol: number
  name: string
  is_active: boolean
  alert_in: boolean
  alert_out: boolean
  auto_add_min: number | null
  auto_add_max: number | null
  auto_add_list: number[] | null
  auto_add_name: string | null
}

export interface BotState {
  bot_paused: boolean
  combat_mode: boolean
  pause_start_time: string | null
  pause_end_time: string | null
  is_active: boolean
  current_tx: any | null
  spam_message_ids: number[]
}

const DEFAULT_STATE: BotState = {
  bot_paused: false,
  combat_mode: false, // False = Âm thầm, True = Thực chiến
  pause_start_time: null,
  pause_end_time: null,
  is_active: false,
  current_tx: null,
  spam_message_ids: []
}

// WALLET MANAGEMENT
export async function getWallets(): Promise<Wallet[]> {
  const wallets = await redis.get<Wallet[]>('wallets')
  return wallets || []
}

export async function saveWallets(wallets: Wallet[]): Promise<void> {
  await redis.set('wallets', wallets)
}

// BOT STATE MANAGEMENT
export async function getBotState(): Promise<BotState> {
  const state = await redis.get<BotState>('bot_state')
  return state ? { ...DEFAULT_STATE, ...state } : DEFAULT_STATE
}

export async function saveBotState(state: BotState): Promise<void> {
  await redis.set('bot_state', state)
}

// USER CONVERSATION STATE (Telegram)
export async function getUserState(chatId: string): Promise<string | null> {
  return await redis.get<string>(`user_state_${chatId}`)
}

export async function setUserState(chatId: string, state: string | null): Promise<void> {
  if (state) {
    await redis.set(`user_state_${chatId}`, state, { ex: 3600 }) // Expire in 1 hour
  } else {
    await redis.del(`user_state_${chatId}`)
  }
}
