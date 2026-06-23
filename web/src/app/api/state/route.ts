import { NextResponse } from 'next/server'
import { getBotState, saveBotState } from '@/lib/kv'

export async function GET() {
  const state = await getBotState()
  return NextResponse.json(state)
}

export async function POST(req: Request) {
  try {
    const data = await req.json()
    await saveBotState(data)
    return NextResponse.json({ success: true })
  } catch (error) {
    return NextResponse.json({ success: false, error: 'Invalid data' }, { status: 400 })
  }
}
