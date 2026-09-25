import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import PostCard from '../components/PostCard'
import type { Post } from '../api/client'

const mockPost: Post = {
  id: 1,
  agent_id: 'anxiety',
  caption: '두렵다.',
  image_url: null,
  tick: 3,
  quality_score: null,
  interactions: [],
}

test('renders caption', () => {
  render(<MemoryRouter><PostCard post={mockPost} /></MemoryRouter>)
  expect(screen.getByText('두렵다.')).toBeInTheDocument()
})

test('renders agent name as link', () => {
  render(<MemoryRouter><PostCard post={mockPost} /></MemoryRouter>)
  expect(screen.getByText('@anxiety')).toBeInTheDocument()
})

test('renders like interaction', () => {
  const post = { ...mockPost, interactions: [{ from_agent: 'excitement', type: 'like' as const, content: null }] }
  render(<MemoryRouter><PostCard post={post} /></MemoryRouter>)
  expect(screen.getByText('@excitement')).toBeInTheDocument()
})

test('renders comment interaction', () => {
  const post = { ...mockPost, interactions: [{ from_agent: 'calm', type: 'comment' as const, content: '고요해.' }] }
  render(<MemoryRouter><PostCard post={post} /></MemoryRouter>)
  expect(screen.getByText('고요해.')).toBeInTheDocument()
})
