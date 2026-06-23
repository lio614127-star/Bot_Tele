'use client'

import { useState, useCallback } from 'react'
import useSWR from 'swr'
import { Activity, Settings, Zap, Shield, Search, Loader2, Edit3, Copy, CheckCircle2 } from 'lucide-react'
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
  const [copiedAddress, setCopiedAddress] = useState<string | null>(null)
  
  const handleCopy = (addr: string) => {
    navigator.clipboard.writeText(addr)
    setCopiedAddress(addr)
    setTimeout(() => setCopiedAddress(null), 2000)
  }

  const [showAddModal, setShowAddModal] = useState(false)
  const [newWallet, setNewWallet] = useState({ address: '', name: '', min_sol: 0.1, max_sol: 100 })

  const handleAddWallet = async () => {
    if (!newWallet.address || !wallets) return
    const updated = [...wallets, { ...newWallet, is_active: true, alert_in: true, alert_out: true, auto_add_min: null, auto_add_max: null, auto_add_list: null, auto_add_name: null }]
    mutateWallets(updated, false)
    await fetch('/api/wallets', { method: 'POST', body: JSON.stringify(updated) })
    mutateWallets()
    setShowAddModal(false)
    setNewWallet({ address: '', name: '', min_sol: 0.1, max_sol: 100 })
  }

  const handleRemoveWallet = async (addr: string) => {
    if (!wallets) return
    const updated = wallets.filter((w: any) => w.address !== addr)
    mutateWallets(updated, false)
    await fetch('/api/wallets', { method: 'POST', body: JSON.stringify(updated) })
    mutateWallets()
  }

  const [showEditModal, setShowEditModal] = useState(false)
  const [editWallet, setEditWallet] = useState<any>(null)

  const openEditModal = (w: any) => {
    setEditWallet({ ...w })
    setShowEditModal(true)
  }

  const handleSaveEdit = async () => {
    if (!wallets || !editWallet) return
    const updated = wallets.map((w: any) => w.address === editWallet.address ? editWallet : w)
    mutateWallets(updated, false)
    await fetch('/api/wallets', { method: 'POST', body: JSON.stringify(updated) })
    mutateWallets()
    setShowEditModal(false)
  }
  
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
                <button onClick={() => setShowAddModal(true)} className="bg-cyan-500 hover:bg-cyan-600 text-black font-semibold px-4 py-2 rounded-lg text-sm transition-colors shadow-[0_0_15px_rgba(6,182,212,0.3)] hover:shadow-[0_0_20px_rgba(6,182,212,0.5)]">
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
                        <div className="flex items-center space-x-2 mt-1">
                          <code className="text-xs text-gray-500">{w.address}</code>
                          <button onClick={() => handleCopy(w.address)} className="text-gray-500 hover:text-cyan-400 transition-colors" title="Copy">
                            {copiedAddress === w.address ? <CheckCircle2 className="w-3.5 h-3.5 text-green-500" /> : <Copy className="w-3.5 h-3.5" />}
                          </button>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-sm text-gray-400">Min: {w.min_sol} - Max: {w.max_sol} SOL</div>
                        <div className="text-xs text-cyan-500/70 mt-1 mb-3">
                          Trạng thái: <span className={w.is_active ? 'text-green-400' : 'text-red-400'}>{w.is_active ? 'BẬT' : 'TẮT'}</span> | Auto-Add: {w.auto_add_name ? 'Bật' : 'Tắt'}
                        </div>
                        <div className="flex space-x-2 justify-end">
                          <button onClick={() => openEditModal(w)} className="text-xs text-gray-300 hover:text-white font-semibold px-2 py-1 bg-gray-800 rounded flex items-center space-x-1">
                            <Edit3 className="w-3 h-3" />
                            <span>Cài đặt</span>
                          </button>
                          <button onClick={() => handleRemoveWallet(w.address)} className="text-xs text-red-500 hover:text-red-400 font-semibold px-2 py-1 bg-red-500/10 rounded">Xóa Ví</button>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>

            {showAddModal && (
              <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50">
                <div className="bg-gray-900 border border-gray-800 p-6 rounded-2xl w-full max-w-md space-y-4 shadow-2xl">
                  <h3 className="text-xl font-bold text-white">Thêm Ví Mới</h3>
                  <input type="text" placeholder="Địa chỉ ví (Address)" className="w-full bg-gray-800 text-white p-2 rounded-lg outline-none focus:ring-1 focus:ring-cyan-500" value={newWallet.address} onChange={e => setNewWallet({...newWallet, address: e.target.value})} />
                  <input type="text" placeholder="Tên gợi nhớ" className="w-full bg-gray-800 text-white p-2 rounded-lg outline-none focus:ring-1 focus:ring-cyan-500" value={newWallet.name} onChange={e => setNewWallet({...newWallet, name: e.target.value})} />
                  <div className="flex space-x-2">
                    <input type="number" placeholder="Min SOL" className="w-full bg-gray-800 text-white p-2 rounded-lg outline-none focus:ring-1 focus:ring-cyan-500" value={newWallet.min_sol} onChange={e => setNewWallet({...newWallet, min_sol: Number(e.target.value)})} />
                    <input type="number" placeholder="Max SOL" className="w-full bg-gray-800 text-white p-2 rounded-lg outline-none focus:ring-1 focus:ring-cyan-500" value={newWallet.max_sol} onChange={e => setNewWallet({...newWallet, max_sol: Number(e.target.value)})} />
                  </div>
                  <div className="flex justify-end space-x-2 pt-4">
                    <button onClick={() => setShowAddModal(false)} className="px-4 py-2 text-gray-400 hover:text-white transition-colors">Hủy</button>
                    <button onClick={handleAddWallet} className="px-4 py-2 bg-cyan-500 text-black font-semibold rounded-lg hover:bg-cyan-600 transition-colors">Lưu Ví</button>
                  </div>
                </div>
              </div>
            )}

            {showEditModal && editWallet && (
              <div className="fixed inset-0 bg-black/80 overflow-y-auto flex items-center justify-center z-50 py-10">
                <div className="bg-gray-900 border border-gray-800 p-6 rounded-2xl w-full max-w-lg space-y-4 shadow-2xl">
                  <h3 className="text-xl font-bold text-white border-b border-gray-800 pb-2">Cài đặt: {editWallet.name}</h3>
                  
                  <div className="space-y-4 max-h-[70vh] overflow-y-auto pr-2 custom-scrollbar">
                    {/* Toggles */}
                    <div className="grid grid-cols-2 gap-4">
                      <label className="flex items-center space-x-2 cursor-pointer bg-gray-800 p-3 rounded-xl border border-gray-700 hover:border-cyan-500/50 transition-colors">
                        <input type="checkbox" checked={editWallet.is_active} onChange={e => setEditWallet({...editWallet, is_active: e.target.checked})} className="rounded bg-gray-900 text-cyan-500 focus:ring-cyan-500 w-5 h-5" />
                        <span className="text-gray-200 text-sm font-medium">Bật Theo Dõi</span>
                      </label>
                      <label className="flex items-center space-x-2 cursor-pointer bg-gray-800 p-3 rounded-xl border border-gray-700 hover:border-cyan-500/50 transition-colors">
                        <input type="checkbox" checked={editWallet.alert_in} onChange={e => setEditWallet({...editWallet, alert_in: e.target.checked})} className="rounded bg-gray-900 text-cyan-500 focus:ring-cyan-500 w-5 h-5" />
                        <span className="text-gray-200 text-sm font-medium">Cảnh báo IN</span>
                      </label>
                      <label className="flex items-center space-x-2 cursor-pointer bg-gray-800 p-3 rounded-xl border border-gray-700 hover:border-cyan-500/50 transition-colors">
                        <input type="checkbox" checked={editWallet.alert_out} onChange={e => setEditWallet({...editWallet, alert_out: e.target.checked})} className="rounded bg-gray-900 text-cyan-500 focus:ring-cyan-500 w-5 h-5" />
                        <span className="text-gray-200 text-sm font-medium">Cảnh báo OUT</span>
                      </label>
                    </div>

                    <div className="bg-gray-800/50 p-4 rounded-xl border border-gray-800 space-y-3">
                      <p className="text-sm text-cyan-400 font-semibold mb-2">Giới hạn Báo Động (SOL)</p>
                      <div className="flex space-x-2">
                        <input type="number" placeholder="Min" className="w-full bg-gray-800 text-white p-2 rounded-lg outline-none focus:ring-1 focus:ring-cyan-500" value={editWallet.min_sol} onChange={e => setEditWallet({...editWallet, min_sol: Number(e.target.value)})} />
                        <input type="number" placeholder="Max" className="w-full bg-gray-800 text-white p-2 rounded-lg outline-none focus:ring-1 focus:ring-cyan-500" value={editWallet.max_sol} onChange={e => setEditWallet({...editWallet, max_sol: Number(e.target.value)})} />
                      </div>
                    </div>

                    <div className="bg-gray-800/50 p-4 rounded-xl border border-gray-800 space-y-3">
                      <p className="text-sm text-cyan-400 font-semibold mb-2">Auto-Add (Tự động thêm ví con)</p>
                      <div>
                        <label className="text-xs text-gray-500 mb-1 block">Tên đuôi cho ví con (Bỏ trống để tắt)</label>
                        <input type="text" placeholder="Ví dụ: Dev" className="w-full bg-gray-800 text-white p-2 rounded-lg outline-none focus:ring-1 focus:ring-cyan-500" value={editWallet.auto_add_name || ''} onChange={e => setEditWallet({...editWallet, auto_add_name: e.target.value})} />
                      </div>
                      
                      <div className="pt-2">
                        <label className="text-xs text-gray-500 mb-1 block">Hoặc bắt theo lượng SOL cố định (cách nhau bởi dấu phẩy, VD: 2.1, 3, 3.2)</label>
                        <input type="text" placeholder="2.1, 3, 3.2" className="w-full bg-gray-800 text-white p-2 rounded-lg outline-none focus:ring-1 focus:ring-cyan-500" 
                          value={editWallet.auto_add_list ? editWallet.auto_add_list.join(', ') : ''} 
                          onChange={e => {
                            const val = e.target.value
                            if (!val) setEditWallet({...editWallet, auto_add_list: null})
                            else {
                              const arr = val.split(',').map((x: string) => parseFloat(x.trim())).filter((x: number) => !isNaN(x))
                              setEditWallet({...editWallet, auto_add_list: arr})
                            }
                          }} 
                        />
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex justify-end space-x-2 pt-4 border-t border-gray-800 mt-4">
                    <button onClick={() => setShowEditModal(false)} className="px-4 py-2 text-gray-400 hover:text-white transition-colors">Hủy</button>
                    <button onClick={handleSaveEdit} className="px-4 py-2 bg-cyan-500 text-black font-semibold rounded-lg hover:bg-cyan-600 transition-colors">Lưu Thay Đổi</button>
                  </div>
                </div>
              </div>
            )}
            
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

              {errorMsg && (
                <div className="bg-red-500/20 text-red-400 text-sm px-4 py-2 rounded-lg border border-red-500/50 w-full text-center">
                  ⚠️ {errorMsg}
                </div>
              )}
              
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
