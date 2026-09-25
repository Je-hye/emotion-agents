import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { vi } from 'vitest'
import QualitySlider from '../components/QualitySlider'
import * as client from '../api/client'

test('renders slider', () => {
  render(<QualitySlider postId={1} initialScore={null} />)
  expect(screen.getByRole('slider')).toBeInTheDocument()
})

test('calls updatePostScore on change', async () => {
  const spy = vi.spyOn(client, 'updatePostScore').mockResolvedValue(undefined)
  render(<QualitySlider postId={1} initialScore={null} />)
  fireEvent.change(screen.getByRole('slider'), { target: { value: '0.8' } })
  await waitFor(() => expect(spy).toHaveBeenCalledWith(1, 0.8))
  spy.mockRestore()
})
