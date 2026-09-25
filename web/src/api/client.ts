import axios from 'axios'

const api = axios.create({ baseURL: '' })

export interface Interaction {
  from_agent: string
  type: 'like' | 'comment'
  content: string | null
}

export interface Post {
  id: number
  agent_id: string
  caption: string
  image_url: string | null
  tick: number
  quality_score: number | null
  interactions: Interaction[]
}

export interface Agent {
  id: string
  emotion_kr: string
  post_frequency: number
}

export interface GraphNode {
  id: string
  emotion_kr: string
  post_count: number
}

export interface GraphEdge {
  source: string
  target: string
  affinity: number
}

export interface GraphData {
  nodes: GraphNode[]
  edges: GraphEdge[]
}

export type StatsData = Record<string, {
  post_count: number
  received_likes: number
  received_comments: number
}>

export const fetchPosts = (params?: {
  agent_id?: string
  since_tick?: number
  min_score?: number
}) => api.get<Post[]>('/api/posts', { params }).then(r => r.data)

export const fetchPost = (id: number) =>
  api.get<Post>(`/api/posts/${id}`).then(r => r.data)

export const updatePostScore = (id: number, score: number) =>
  api.patch(`/api/posts/${id}/score`, { score }).then(r => r.data)

export const fetchAgents = () =>
  api.get<Agent[]>('/api/agents').then(r => r.data)

export const fetchGraph = () =>
  api.get<GraphData>('/api/graph').then(r => r.data)

export const fetchStats = () =>
  api.get<StatsData>('/api/stats').then(r => r.data)
