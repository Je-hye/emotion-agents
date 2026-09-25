import { useEffect } from 'react'
import type { Post } from '../api/client'
import QualitySlider from './QualitySlider'

interface Props {
  post: Post
  onClose: () => void
}

export default function PostModal({ post, onClose }: Props) {
  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [onClose])

  return (
    <div
      className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-xl overflow-hidden max-w-md w-full"
        onClick={e => e.stopPropagation()}
      >
        {post.image_url && (
          <img src={post.image_url} alt="generated" className="w-full aspect-square object-cover" />
        )}
        <div className="p-4">
          <p className="text-sm font-semibold">@{post.agent_id}</p>
          <p className="text-sm mt-1">{post.caption}</p>
          <div className="mt-2 space-y-1">
            {post.interactions.map((i, idx) => (
              <div key={idx} className="text-xs text-gray-500">
                {i.type === 'like' ? '❤' : '💬'}{' '}
                <span className="font-medium">@{i.from_agent}</span>
                {i.content && <span className="ml-1">{i.content}</span>}
              </div>
            ))}
          </div>
          <QualitySlider postId={post.id} initialScore={post.quality_score} />
          <button onClick={onClose} className="mt-3 text-xs text-gray-400 hover:text-black">닫기</button>
        </div>
      </div>
    </div>
  )
}
