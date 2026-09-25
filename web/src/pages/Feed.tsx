import { useEffect, useState } from 'react'
import { fetchPosts, fetchAgents } from '../api/client'
import type { Post, Agent } from '../api/client'
import PostCard from '../components/PostCard'

export default function Feed() {
  const [posts, setPosts] = useState<Post[]>([])
  const [agents, setAgents] = useState<Agent[]>([])
  const [filterAgent, setFilterAgent] = useState<string>('')

  useEffect(() => {
    fetchAgents().then(setAgents)
  }, [])

  useEffect(() => {
    fetchPosts(filterAgent ? { agent_id: filterAgent } : undefined).then(setPosts)
  }, [filterAgent])

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
      {posts.length === 0 && (
        <p className="text-gray-400 text-sm text-center py-12">포스트가 없습니다. cli.py run 후 새로고침하세요.</p>
      )}
      <div className="space-y-4">
        {posts.map(post => <PostCard key={post.id} post={post} />)}
      </div>
    </div>
  )
}
