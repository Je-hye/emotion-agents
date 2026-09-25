import { useState } from 'react'
import { updatePostScore } from '../api/client'

interface Props {
  postId: number
  initialScore: number | null
}

export default function QualitySlider({ postId, initialScore }: Props) {
  const [score, setScore] = useState<number>(initialScore ?? 0)

  const handleChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = parseFloat(e.target.value)
    setScore(val)
    await updatePostScore(postId, val)
  }

  return (
    <div className="flex items-center gap-2 mt-1">
      <span className="text-xs text-gray-400">Q</span>
      <input
        type="range"
        min="0"
        max="1"
        step="0.01"
        value={score}
        onChange={handleChange}
        className="w-24 accent-black"
      />
      <span className="text-xs text-gray-500">{score.toFixed(2)}</span>
    </div>
  )
}
