import { NextResponse } from 'next/server'

export async function POST(req: Request) {
  try {
    const { address, tokens, minAmount, maxAmount, startDate, endDate, flowDirection, centerX = 0, centerY = 0 } = await req.json()
    if (!address) return NextResponse.json({ error: 'Missing address' }, { status: 400 })

    const apiKey = process.env.HELIUS_API_KEY
    if (!apiKey) return NextResponse.json({ error: 'Missing Helius API Key' }, { status: 500 })

    // Convert dates to Unix timestamps (seconds)
    const startTimestamp = startDate ? new Date(startDate).getTime() / 1000 : 0
    const endTimestamp = endDate ? new Date(endDate).getTime() / 1000 : Infinity

    const url = `https://api.helius.xyz/v0/addresses/${address}/transactions?api-key=${apiKey}`
    const res = await fetch(url)
    const txs = await res.json()

    if (!Array.isArray(txs)) {
      return NextResponse.json({ error: 'Invalid response from Helius' }, { status: 500 })
    }

    const nodesMap = new Map()
    const edgesMap = new Map()

    // Aggregate volumes
    const volumeMap = new Map<string, { volume: number, isOut: boolean, symbol: string }>()

    for (const tx of txs) {
      // Filter by timestamp
      if (tx.timestamp < startTimestamp || tx.timestamp > endTimestamp) continue

      // Process Native SOL
      if (tokens.includes('SOL') && tx.nativeTransfers) {
        for (const t of tx.nativeTransfers) {
          if (t.fromUserAccount === address || t.toUserAccount === address) {
            const isOut = t.fromUserAccount === address
            // Flow Filter
            if (flowDirection === 'out' && !isOut) continue
            if (flowDirection === 'in' && isOut) continue

            const other = isOut ? t.toUserAccount : t.fromUserAccount
            const amount = t.amount / 1e9
            
            // Filter by amount
            if (minAmount && amount < minAmount) continue
            if (maxAmount && amount > maxAmount) continue
            if (!minAmount && amount < 0.01) continue // Default tiny dust filter

            if (!volumeMap.has(other)) volumeMap.set(other, { volume: 0, isOut, symbol: 'SOL' })
            volumeMap.get(other)!.volume += amount
          }
        }

        // Fallback for SOL transfers if nativeTransfers missed it (e.g. WITHDRAW FROM NONCE, System Program transfers)
        if (tx.nativeTransfers.length === 0 && tx.accountData) {
          const myData = tx.accountData.find((a: any) => a.account === address)
          if (myData && Math.abs(myData.nativeBalanceChange) > 1000000) { // Ignore small fees (< 0.001 SOL)
            const isOut = myData.nativeBalanceChange < 0
            
            if (flowDirection === 'out' && !isOut) continue
            if (flowDirection === 'in' && isOut) continue

            const counterpart = tx.accountData.find((a: any) => 
              a.account !== address && 
              a.account !== '11111111111111111111111111111111' && 
              a.account !== 'ComputeBudget111111111111111111111111111111' &&
              (isOut ? a.nativeBalanceChange > 0 : a.nativeBalanceChange < 0)
            )

            if (counterpart) {
              const other = counterpart.account
              const amount = Math.abs(isOut ? counterpart.nativeBalanceChange : myData.nativeBalanceChange) / 1e9
              
              if (!minAmount || amount >= minAmount) {
                if (!maxAmount || amount <= maxAmount) {
                  if (!volumeMap.has(other)) volumeMap.set(other, { volume: 0, isOut, symbol: 'SOL' })
                  volumeMap.get(other)!.volume += amount
                }
              }
            }
          }
        }
      }

      // Process SPL Tokens
      if (tx.tokenTransfers) {
        for (const t of tx.tokenTransfers) {
          let symbol = ''
          if (tokens.includes('USDC') && t.mint === 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v') symbol = 'USDC'
          if (tokens.includes('USDT') && t.mint === 'Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB') symbol = 'USDT'
          if (tokens.includes('wSOL') && t.mint === 'So11111111111111111111111111111111111111112') symbol = 'wSOL'

          if (symbol && (t.fromUserAccount === address || t.toUserAccount === address)) {
            const isOut = t.fromUserAccount === address
            // Flow Filter
            if (flowDirection === 'out' && !isOut) continue
            if (flowDirection === 'in' && isOut) continue

            const other = isOut ? t.toUserAccount : t.fromUserAccount
            const amount = t.tokenAmount
            
            // Filter by amount
            if (minAmount && amount < minAmount) continue
            if (maxAmount && amount > maxAmount) continue
            if (!minAmount && amount < 1) continue // Default tiny dust filter for tokens

            const current = volumeMap.get(other) || { volume: 0, isOut, symbol }
            current.volume += amount
            volumeMap.set(other, current)
          }
        }
      }
    }

    // Sort wallets by volume descending
    const sortedWallets = Array.from(volumeMap.entries()).sort((a, b) => b[1].volume - a[1].volume)
    
    // Add root node
    const rootX = Number(centerX)
    const rootY = Number(centerY)
    nodesMap.set(address, { 
      id: address, 
      type: 'bubble',
      data: { label: address, isRoot: true, volume: sortedWallets.reduce((acc, curr) => acc + curr[1].volume, 0) }, 
      position: { x: rootX, y: rootY }
    })

    // Orbit Layout
    let currentOrbit = 1
    let itemsInCurrentOrbit = 0
    let maxItemsInOrbit = 8

    sortedWallets.forEach(([other, data], index) => {
      // Calculate position
      if (itemsInCurrentOrbit >= maxItemsInOrbit) {
        currentOrbit++
        itemsInCurrentOrbit = 0
        maxItemsInOrbit = Math.floor(maxItemsInOrbit * 1.5) // Outer orbits can hold more
      }

      const radius = currentOrbit * 200
      const angle = (itemsInCurrentOrbit / maxItemsInOrbit) * Math.PI * 2
      const x = rootX + radius * Math.cos(angle)
      const y = rootY + radius * Math.sin(angle)
      
      nodesMap.set(other, { 
        id: other, 
        type: 'bubble',
        data: { label: other, isRoot: false, volume: data.volume }, 
        position: { x, y }
      })

      // Create aggregated edge
      const edgeId = `${address}-${other}-${data.symbol}`
      edgesMap.set(edgeId, {
        id: edgeId,
        source: data.isOut ? address : other,
        target: data.isOut ? other : address,
        label: `${data.volume.toFixed(2)} ${data.symbol}`,
        animated: false, // Turn off animation to fix lag
        style: { stroke: data.symbol === 'USDC' ? '#3b82f6' : data.symbol === 'USDT' ? '#22c55e' : '#a855f7', strokeDasharray: '5 5' }
      })

      itemsInCurrentOrbit++
    })

    return NextResponse.json({
      nodes: Array.from(nodesMap.values()),
      edges: Array.from(edgesMap.values())
    })
  } catch (error) {
    console.error(error)
    return NextResponse.json({ error: 'Failed to trace' }, { status: 500 })
  }
}
