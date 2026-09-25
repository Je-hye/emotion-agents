import { Link } from 'react-router-dom'
import type { Post } from '../api/client'
import QualitySlider from './QualitySlider'

interface Props {
  post: Post
}

export default function PostCard({ post }: Props) {
  return (
    <article className="border border-gray-200 rounded-lg overflow-hidden bg-white">
      {post.image_url && (
        <img src={post.image_url} alt="generated" className="w-full aspect-square object-cover" />
      )}
      <div className="p-3">
        <Link to={`/@${post.agent_id}`} className="text-sm font-semibold hover:underline">
          @{post.agent_id}
        </Link>
        <span className="ml-2 text-xs text-gray-400">tick {post.tick}</span>
        <p className="mt-1 text-sm text-gray-800">{post.caption}</p>
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
      </div>
    </article>
  )
}
