import { useState, useRef, useCallback } from 'react'

export function useTickStream(
  onTick: (tick: number) => void,
  onDone: () => void,
) {
  const [running, setRunning] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)

  const start = useCallback(async (ticks: number) => {
    if (running) return

    const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const ws = new WebSocket(`${proto}//${window.location.host}/ws/ticks`)
    wsRef.current = ws

    ws.onmessage = (e) => {
      const msg = JSON.parse(e.data)
      if (msg.type === 'tick') onTick(msg.tick)
      if (msg.type === 'done') {
        setRunning(false)
        onDone()
        ws.close()
      }
      if (msg.type === 'error') {
        setRunning(false)
        ws.close()
      }
    }

    ws.onclose = () => setRunning(false)
    ws.onerror = () => {
      setRunning(false)
      wsRef.current = null
    }

    await new Promise<void>((resolve) => { ws.onopen = () => resolve() })

    setRunning(true)
    await fetch('/api/simulate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ticks }),
    })
  }, [running, onTick, onDone])

  return { start, running }
}
