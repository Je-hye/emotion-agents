import { render } from '@testing-library/react'
import { vi } from 'vitest'
import RelationGraph from '../components/RelationGraph'
import type { GraphData } from '../api/client'

vi.mock('react-force-graph-2d', () => ({
  default: ({ graphData }: { graphData: { nodes: unknown[]; links: unknown[] } }) => (
    <div data-testid="graph">nodes:{graphData.nodes.length} links:{graphData.links.length}</div>
  ),
}))

const mockData: GraphData = {
  nodes: [
    { id: 'anxiety', emotion_kr: '불안', post_count: 5 },
    { id: 'excitement', emotion_kr: '설렘', post_count: 3 },
  ],
  edges: [{ source: 'anxiety', target: 'excitement', affinity: 0.4 }],
}

test('renders graph with correct node/link count', () => {
  const { getByTestId } = render(
    <RelationGraph data={mockData} onNodeClick={() => {}} />
  )
  expect(getByTestId('graph').textContent).toContain('nodes:2')
  expect(getByTestId('graph').textContent).toContain('links:1')
})
