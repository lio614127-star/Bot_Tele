'use client'

import { useState, useCallback } from 'react'
import useSWR from 'swr'
import { Activity, Settings, Zap, Shield, Search, Loader2 } from 'lucide-react'
import { ReactFlow, Background, Controls, useNodesState, useEdgesState, MarkerType } from '@xyflow/react'
import '@xyflow/react/dist/style.css'

const fetcher = (url: string) => fetch(url).then(res => res.json())

export default function App() {
  const [tab, setTab] = useState<'map' | 'settings'>('map')
  const { data: wallets, mutate: mutateWallets } = useSWR('/api/wallets', fetcher)
  const { data: botState, mutate: mutateState } = useSWR('/api/state', fetcher)
  
  // Tracer State
  const [searchAddr, setSearchAddr] = useState('')
  const [tokens, setTokens] = useState(['SOL', 'USDC', 'USDT', 'wSOL'])
  const [isLoading, setIsLoading] = useState(false)
  const [errorMsg, setErrorMsg] = useState('')
  const [nodes, setNodes, onNodesChange] = useNodesState([{ id: '1', position: { x: 250, y: 200 }, data: { label: 'Chưa có dữ liệu quét' } }])
  const [edges, setEdges, onEdgesChange] = useEdgesState([])
  
  const toggleCombatMode = async () => {
    if (!botState) return
    const newState = { ...botState, combat_mode: !botState.combat_mode }
    mutateState(newState, false) // Cập nhật UI ngay lập tức (Optimistic Update)
    await fetch('/api/state', { method: 'POST', body: JSON.stringify(newState) })
    mutateState()
  }

  const handleTrace = async () => {
    if (!searchAddr) return
    setIsLoading(true)
    setErrorMsg('')
    try {
      const res = await fetch('/api/trace', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ address: searchAddr, tokens })
      })
      const data = await res.json()
      
      if (data.error) {
        setErrorMsg(data.error)
        setNodes([{ id: 'err', position: { x: 250, y: 200 }, data: { label: `❌ Lỗi: ${data.error} (Thiếu Helius API Key?)` }, style: { backgroundColor: '#ef4444', color: '#fff' } } as any])
        setEdges([])
        return
      }

      if (data.nodes && data.nodes.length > 0) {
        // Add markerEnd to edges for arrows
        const formattedEdges = data.edges.map((e: any) => ({
          ...e,
          markerEnd: { type: MarkerType.ArrowClosed }
        }))
        setNodes(data.nodes)
        setEdges(formattedEdges)
      } else {
        setNodes([{ id: 'empty', position: { x: 250, y: 200 }, data: { label: 'Không tìm thấy giao dịch chuyển tiền nào!' }, style: { backgroundColor: '#f59e0b', color: '#fff' } } as any])
        setEdges([])
      }
    } catch (e: any) {
      setErrorMsg(e.message)
      console.error(e)
    } finally {
      setIsLoading(false)
    }
  }

  const toggleToken = (t: string) => {
    setTokens(prev => prev.includes(t) ? prev.filter(x => x !== t) : [...prev, t])
  }

  return (
    <div className="min-h-screen bg-black text-gray-100 flex flex-col font-sans selection:bg-cyan-500/30">
      {/* Header */}
      <header className="border-b border-gray-800 bg-gray-950/50 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Zap className="w-6 h-6 text-cyan-400 fill-cyan-400/20" />
            <h1 className="text-xl font-bold bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">
              Mạng Nhện Tracer
            </h1>
          </div>
          
          <div className="flex bg-gray-900 p-1 rounded-lg border border-gray-800">
            <button 
              onClick={() => setTab('map')}
              className={`px-4 py-1.5 rounded-md text-sm font-medium transition-all ${tab === 'map' ? 'bg-gray-800 text-white shadow-sm' : 'text-gray-400 hover:text-gray-200'}`}
            >
              <div className="flex items-center space-x-2">
                <Activity className="w-4 h-4" />
                <span>Bản Đồ</span>
              </div>
            </button>
            <button 
              onClick={() => setTab('settings')}
              className={`px-4 py-1.5 rounded-md text-sm font-medium transition-all ${tab === 'settings' ? 'bg-gray-800 text-white shadow-sm' : 'text-gray-400 hover:text-gray-200'}`}
            >
              <div className="flex items-center space-x-2">
                <Settings className="w-4 h-4" />
                <span>Quản Lý</span>
              </div>
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 flex flex-col">
        {tab === 'settings' && (
          <div className="max-w-4xl mx-auto w-full p-6 space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
            
            {/* Combat Mode Toggle */}
            <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-6 flex items-center justify-between">
              <div>
                <h2 className="text-lg font-semibold text-white flex items-center space-x-2">
                  <Shield className="w-5 h-5 text-cyan-400" />
                  <span>Chế độ Thực Chiến (Combat Mode)</span>
                </h2>
                <p className="text-gray-400 text-sm mt-1">Khi bật, bot sẽ không hú còi trên Telegram mà chỉ gửi thông báo im lặng.</p>
              </div>
              <button 
                onClick={toggleCombatMode}
                className={`relative inline-flex h-7 w-14 items-center rounded-full transition-colors focus:outline-none ${botState?.combat_mode ? 'bg-cyan-500' : 'bg-gray-700'}`}
              >
                <span className={`inline-block h-5 w-5 transform rounded-full bg-white transition-transform ${botState?.combat_mode ? 'translate-x-8' : 'translate-x-1'}`} />
              </button>
            </div>

            {/* Wallets List */}
            <div>
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-white">Danh sách Ví theo dõi</h2>
                <button className="bg-cyan-500 hover:bg-cyan-600 text-black font-semibold px-4 py-2 rounded-lg text-sm transition-colors shadow-[0_0_15px_rgba(6,182,212,0.3)] hover:shadow-[0_0_20px_rgba(6,182,212,0.5)]">
                  + Thêm Ví Mới
                </button>
              </div>
              
              <div className="space-y-3">
                {!wallets ? (
                  <div className="text-center text-gray-500 py-10">Đang tải dữ liệu...</div>
                ) : wallets.length === 0 ? (
                  <div className="text-center text-gray-500 py-10 border border-dashed border-gray-800 rounded-xl">Chưa có ví nào trong danh sách.</div>
                ) : (
                  wallets.map((w: any, idx: number) => (
                    <div key={idx} className="bg-gray-900 border border-gray-800 p-4 rounded-xl flex items-center justify-between hover:border-gray-700 transition-colors">
                      <div>
                        <h3 className="font-medium text-gray-200">{w.name || 'Ví chưa đặt tên'}</h3>
                        <code className="text-xs text-gray-500 mt-1 block">{w.address}</code>
                      </div>
                      <div className="text-right">
                        <div className="text-sm text-gray-400">Min: {w.min_sol} - Max: {w.max_sol} SOL</div>
                        <div className="text-xs text-cyan-500/70 mt-1">
                          Auto-Add: {w.auto_add_name ? 'Bật' : 'Tắt'}
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
            
          </div>
        )}

        {tab === 'map' && (
          <div className="flex-1 relative flex flex-col">
            {/* Search Bar Overlay */}
            <div className="absolute top-4 left-1/2 -translate-x-1/2 z-10 w-full max-w-2xl px-4 flex flex-col items-center space-y-2">
              <div className="bg-gray-900/80 backdrop-blur-md border border-gray-700 rounded-2xl shadow-2xl p-2 flex items-center space-x-2 focus-within:border-cyan-500/50 focus-within:ring-1 focus-within:ring-cyan-500/50 transition-all w-full">
                <Search className="w-5 h-5 text-gray-400 ml-2" />
                <input 
                  type="text" 
                  value={searchAddr}
                  onChange={e => setSearchAddr(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && handleTrace()}
                  placeholder="Nhập địa chỉ ví để truy vết..." 
                  className="bg-transparent border-none outline-none flex-1 text-white placeholder-gray-500 text-sm py-1"
                />
                <button 
                  onClick={handleTrace}
                  disabled={isLoading}
                  className="bg-cyan-500 hover:bg-cyan-600 disabled:bg-gray-700 text-black px-4 py-1.5 rounded-xl text-sm font-semibold transition-colors flex items-center space-x-2"
                >
                  {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <span>Quét</span>}
                </button>
              </div>
              
              {/* Token Filters */}
              <div className="flex items-center space-x-4 bg-gray-900/80 backdrop-blur-md px-4 py-1.5 rounded-full border border-gray-800 text-sm mt-2">
                <span className="text-gray-400 text-xs font-semibold mr-2">BỘ LỌC:</span>
                {['SOL', 'USDC', 'USDT', 'wSOL'].map(t => (
                  <label key={t} className="flex items-center space-x-1.5 cursor-pointer">
                    <input 
                      type="checkbox" 
                      checked={tokens.includes(t)}
                      onChange={() => toggleToken(t)}
                      className="rounded border-gray-700 text-cyan-500 focus:ring-cyan-500 bg-gray-800"
                    />
                    <span className={tokens.includes(t) ? 'text-gray-200' : 'text-gray-500'}>{t}</span>
                  </label>
                ))}
              </div>
            </div>

            <div className="flex-1 bg-black w-full h-[calc(100vh-64px)]">
              <ReactFlow 
                nodes={nodes} 
                edges={edges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                fitView
              >
                <Background color="#333" gap={16} />
                <Controls className="bg-gray-900 border-gray-800 fill-white" />
              </ReactFlow>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
