import { NextResponse } from 'next/server'
import { getWallets, saveWallets } from '@/lib/kv'

export async function GET() {
  const wallets = await getWallets()
  return NextResponse.json(wallets)
}

export async function POST(req: Request) {
  try {
    const data = await req.json()
    await saveWallets(data)
    return NextResponse.json({ success: true })
  } catch (error) {
    return NextResponse.json({ success: false, error: 'Invalid data' }, { status: 400 })
  }
}
