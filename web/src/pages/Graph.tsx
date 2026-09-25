import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { fetchGraph } from '../api/client'
import type { GraphData } from '../api/client'
import RelationGraph from '../components/RelationGraph'

export default function Graph() {
  const [data, setData] = useState<GraphData | null>(null)
  const navigate = useNavigate()

  useEffect(() => { fetchGraph().then(setData) }, [])

  if (!data) return <div className="p-8 text-gray-400 text-sm">그래프 데이터를 불러오는 중...</div>

  return (
    <div className="max-w-3xl mx-auto px-4 py-6">
      <h1 className="text-lg font-bold mb-1">감정 관계 그래프</h1>
      <p className="text-xs text-gray-400 mb-4">엣지 굵기 = affinity 강도 · 빨간 선 = 부정적 관계 · 노드 크기 = 포스트 수</p>
      <div className="border border-gray-200 rounded-xl overflow-hidden">
        <RelationGraph data={data} onNodeClick={id => navigate(`/@${id}`)} />
      </div>
    </div>
  )
}
