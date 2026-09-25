import { renderHook, act } from '@testing-library/react'
import { vi } from 'vitest'
import { useTickStream } from '../hooks/useTickStream'

test('start calls POST /api/simulate', async () => {
  const mockWs = {
    onmessage: null as any,
    onclose: null as any,
    onopen: null as any,
    onerror: null as any,
    close: vi.fn(),
  }
  vi.stubGlobal('WebSocket', vi.fn(() => mockWs))

  const fetchSpy = vi.fn().mockResolvedValue({ ok: true })
  vi.stubGlobal('fetch', fetchSpy)

  const onTick = vi.fn()
  const onDone = vi.fn()
  const { result } = renderHook(() => useTickStream(onTick, onDone))

  await act(async () => {
    const startPromise = result.current.start(3)
    await Promise.resolve()
    if (mockWs.onopen) mockWs.onopen({})
    await startPromise
  })
  expect(fetchSpy).toHaveBeenCalledWith('/api/simulate', expect.objectContaining({ method: 'POST' }))

  vi.unstubAllGlobals()
})

test('onTick called when tick message received', async () => {
  const mockWs = {
    onmessage: null as any,
    onclose: null as any,
    onopen: null as any,
    onerror: null as any,
    close: vi.fn(),
  }
  vi.stubGlobal('WebSocket', vi.fn(() => mockWs))
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true }))

  const onTick = vi.fn()
  const onDone = vi.fn()
  const { result } = renderHook(() => useTickStream(onTick, onDone))

  await act(async () => {
    const startPromise = result.current.start(3)
    await Promise.resolve()
    if (mockWs.onopen) mockWs.onopen({})
    await startPromise
  })
  act(() => {
    mockWs.onmessage({ data: JSON.stringify({ type: 'tick', tick: 0 }) })
  })
  expect(onTick).toHaveBeenCalledWith(0)

  vi.unstubAllGlobals()
})
