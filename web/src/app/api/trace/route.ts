import { NextResponse } from 'next/server'

export async function POST(req: Request) {
  try {
    const { address, tokens } = await req.json()
    const apiKey = process.env.HELIUS_API_KEY
    if (!apiKey) return NextResponse.json({ error: 'Missing Helius API Key' }, { status: 500 })

    const url = `https://api.helius.xyz/v0/addresses/${address}/transactions?api-key=${apiKey}`
    const res = await fetch(url)
    const txs = await res.json()

    if (!Array.isArray(txs)) {
      return NextResponse.json({ error: 'Invalid response from Helius' }, { status: 500 })
    }

    const nodesMap = new Map()
    const edgesMap = new Map()

    // Add root node
    nodesMap.set(address, { id: address, data: { label: `[Root]\n${address.slice(0,4)}...${address.slice(-4)}` }, position: { x: 400, y: 300 }, style: { backgroundColor: '#06b6d4', color: '#000', fontWeight: 'bold' } })

    let xOff = 100
    let yOff = 100

    for (const tx of txs) {
      if (tx.type !== 'TRANSFER' && tx.type !== 'UNKNOWN') continue

      // Process Native SOL
      if (tokens.includes('SOL') && tx.nativeTransfers) {
        for (const t of tx.nativeTransfers) {
          if (t.fromUserAccount === address || t.toUserAccount === address) {
            const isOut = t.fromUserAccount === address
            const other = isOut ? t.toUserAccount : t.fromUserAccount
            const amount = t.amount / 1e9
            
            if (amount < 0.01) continue // Skip tiny fees

            if (!nodesMap.has(other)) {
              nodesMap.set(other, { id: other, data: { label: `${other.slice(0,4)}...${other.slice(-4)}` }, position: { x: xOff, y: yOff }, style: { backgroundColor: '#1f2937', color: '#fff' } })
              xOff += 150
              if (xOff > 800) { xOff = 100; yOff += 100 }
            }

            const edgeId = `${t.fromUserAccount}-${t.toUserAccount}-SOL`
            edgesMap.set(edgeId, {
              id: edgeId,
              source: t.fromUserAccount,
              target: t.toUserAccount,
              label: `${amount.toFixed(2)} SOL`,
              animated: true,
              style: { stroke: '#06b6d4' }
            })
          }
        }
      }

      // Process Tokens (USDC, USDT, wSOL)
      if (tx.tokenTransfers) {
        for (const t of tx.tokenTransfers) {
          // Token mint checks
          const isUSDC = t.mint === 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v'
          const isUSDT = t.mint === 'Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB'
          const isWSOL = t.mint === 'So11111111111111111111111111111111111111112'

          let symbol = ''
          if (isUSDC && tokens.includes('USDC')) symbol = 'USDC'
          else if (isUSDT && tokens.includes('USDT')) symbol = 'USDT'
          else if (isWSOL && tokens.includes('wSOL')) symbol = 'wSOL'
          else continue

          if (t.fromUserAccount === address || t.toUserAccount === address) {
            const isOut = t.fromUserAccount === address
            const other = isOut ? t.toUserAccount : t.fromUserAccount
            const amount = t.tokenAmount

            if (!nodesMap.has(other)) {
              nodesMap.set(other, { id: other, data: { label: `${other.slice(0,4)}...${other.slice(-4)}` }, position: { x: xOff, y: yOff }, style: { backgroundColor: '#1f2937', color: '#fff' } })
              xOff += 150
              if (xOff > 800) { xOff = 100; yOff += 100 }
            }

            const edgeId = `${t.fromUserAccount}-${t.toUserAccount}-${symbol}`
            edgesMap.set(edgeId, {
              id: edgeId,
              source: t.fromUserAccount,
              target: t.toUserAccount,
              label: `${amount} ${symbol}`,
              animated: true,
              style: { stroke: symbol === 'USDC' ? '#3b82f6' : symbol === 'USDT' ? '#22c55e' : '#a855f7' }
            })
          }
        }
      }
    }

    return NextResponse.json({
      nodes: Array.from(nodesMap.values()),
      edges: Array.from(edgesMap.values())
    })
  } catch (error) {
    console.error(error)
    return NextResponse.json({ error: 'Failed to trace' }, { status: 500 })
  }
}
