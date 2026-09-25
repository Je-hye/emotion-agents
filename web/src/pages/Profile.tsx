import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { fetchPosts, fetchAgents, fetchStats } from '../api/client'
import type { Post, Agent } from '../api/client'
import PostModal from '../components/PostModal'

export default function Profile() {
  const { agentId } = useParams<{ agentId: string }>()
  const [posts, setPosts] = useState<Post[]>([])
  const [agent, setAgent] = useState<Agent | null>(null)
  const [stats, setStats] = useState<{ post_count: number; received_likes: number; received_comments: number } | null>(null)
  const [selected, setSelected] = useState<Post | null>(null)
  const [sortByScore, setSortByScore] = useState(false)

  useEffect(() => {
    if (!agentId) return
    fetchAgents().then(list => setAgent(list.find(a => a.id === agentId) ?? null))
    fetchPosts({ agent_id: agentId }).then(setPosts)
    fetchStats().then(s => setStats(s[agentId] ?? null))
  }, [agentId])

  const sorted = sortByScore
    ? [...posts].sort((a, b) => (b.quality_score ?? -1) - (a.quality_score ?? -1))
    : posts

  if (!agent) return <div className="p-8 text-gray-400 text-sm">에이전트를 찾을 수 없습니다.</div>

  return (
    <div className="max-w-2xl mx-auto px-4 py-6">
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold">@{agent.id}</h1>
          <p className="text-gray-500 text-sm">{agent.emotion_kr}</p>
          {stats && (
            <div className="flex gap-4 mt-2 text-sm">
              <span><b>{stats.post_count}</b> posts</span>
              <span><b>{stats.received_likes}</b> likes</span>
              <span><b>{stats.received_comments}</b> comments</span>
            </div>
          )}
        </div>
        <Link to="/" className="text-xs text-gray-400 hover:text-black">← 피드</Link>
      </div>
      <div className="flex items-center gap-2 mb-3">
        <button
          onClick={() => setSortByScore(s => !s)}
          className={`text-xs px-3 py-1 rounded-full border ${sortByScore ? 'bg-black text-white' : 'border-gray-300'}`}
        >
          quality_score 순
        </button>
      </div>
      <div className="grid grid-cols-3 gap-1">
        {sorted.map(post => (
          <button
            key={post.id}
            onClick={() => setSelected(post)}
            className="aspect-square bg-gray-100 overflow-hidden relative group"
          >
            {post.image_url
              ? <img src={post.image_url} alt="" className="w-full h-full object-cover" />
              : <div className="w-full h-full flex items-center justify-center p-1 text-xs text-gray-500 text-center">{post.caption.slice(0, 20)}</div>
            }
            {post.quality_score !== null && (
              <span className="absolute bottom-1 right-1 bg-black/60 text-white text-xs px-1 rounded">
                {post.quality_score.toFixed(2)}
              </span>
            )}
          </button>
        ))}
      </div>
      {selected && <PostModal post={selected} onClose={() => setSelected(null)} />}
    </div>
  )
}
