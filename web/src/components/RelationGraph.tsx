import ForceGraph2D from 'react-force-graph-2d'
import type { GraphData } from '../api/client'

interface Props {
  data: GraphData
  onNodeClick: (id: string) => void
}

export default function RelationGraph({ data, onNodeClick }: Props) {
  const graphData = {
    nodes: data.nodes.map(n => ({ ...n, val: Math.max(n.post_count, 1) })),
    links: data.edges.map(e => ({
      source: e.source,
      target: e.target,
      affinity: e.affinity,
    })),
  }

  return (
    <ForceGraph2D
      graphData={graphData}
      nodeLabel={(n: any) => `@${n.id} (${n.emotion_kr})`}
      nodeAutoColorBy="id"
      linkWidth={(l: any) => Math.abs(l.affinity) * 4}
      linkColor={(l: any) => l.affinity < 0 ? '#ef4444' : '#94a3b8'}
      onNodeClick={(n: any) => onNodeClick(n.id)}
      width={600}
      height={500}
    />
  )
}
