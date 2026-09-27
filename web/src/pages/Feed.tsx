import { useCallback, useEffect, useState } from 'react'
import { fetchPosts, fetchAgents } from '../api/client'
import type { Post, Agent } from '../api/client'
import PostCard from '../components/PostCard'
import { useTickStream } from '../hooks/useTickStream'

export default function Feed() {
  const [posts, setPosts] = useState<Post[]>([])
  const [agents, setAgents] = useState<Agent[]>([])
  const [filterAgent, setFilterAgent] = useState<string>('')
  const [tickLabel, setTickLabel] = useState<string>('')
  const [ticks, setTicks] = useState(6)

  useEffect(() => {
    fetchAgents().then(setAgents)
  }, [])

  useEffect(() => {
    fetchPosts(filterAgent ? { agent_id: filterAgent } : undefined).then(setPosts)
  }, [filterAgent])

  const handleTick = useCallback((tick: number) => {
    setTickLabel(`tick ${tick} 진행 중...`)
    fetchPosts(filterAgent ? { agent_id: filterAgent } : undefined).then(setPosts)
  }, [filterAgent])

  const handleDone = useCallback(() => {
    setTickLabel('')
    fetchPosts(filterAgent ? { agent_id: filterAgent } : undefined).then(setPosts)
  }, [filterAgent])

  const { start, stop, running } = useTickStream(handleTick, handleDone)

  return (
    <div className="max-w-lg mx-auto px-4 py-6">
      <div className="flex gap-2 mb-4 flex-wrap">
        <button
          onClick={() => setFilterAgent('')}
          className={`px-3 py-1 rounded-full text-xs border ${!filterAgent ? 'bg-black text-white' : 'border-gray-300'}`}
        >
          전체
        </button>
        {agents.map(a => (
          <button
            key={a.id}
            onClick={() => setFilterAgent(a.id)}
            className={`px-3 py-1 rounded-full text-xs border ${filterAgent === a.id ? 'bg-black text-white' : 'border-gray-300'}`}
          >
            @{a.id}
          </button>
        ))}
      </div>
      <div className="flex items-center gap-3 mb-4">
        <button
          onClick={() => start(ticks)}
          disabled={running}
          className="px-4 py-1.5 rounded-full text-xs bg-black text-white disabled:opacity-40"
        >
          {running ? tickLabel || '실행 중...' : '시뮬레이션 실행'}
        </button>
        {running && (
          <button
            onClick={stop}
            className="px-4 py-1.5 rounded-full text-xs border border-gray-400 text-gray-600"
          >
            중단
          </button>
        )}
        <label className="flex items-center gap-1.5 text-xs text-gray-500">
          <input
            type="number"
            min={1}
            max={100}
            value={ticks}
            disabled={running}
            onChange={e => setTicks(Math.min(100, Math.max(1, Number(e.target.value))))}
            className="w-14 border border-gray-300 rounded px-1.5 py-0.5 text-center text-xs disabled:opacity-40"
          />
          ticks
        </label>
      </div>
      {posts.length === 0 && (
        <p className="text-gray-400 text-sm text-center py-12">포스트가 없습니다. 시뮬레이션 실행 후 새로고침하세요.</p>
      )}
      <div className="space-y-4">
        {posts.map(post => <PostCard key={post.id} post={post} />)}
      </div>
    </div>
  )
}
