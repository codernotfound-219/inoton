import type { MicrogridState } from './types'

export async function fetchState(signal?: AbortSignal): Promise<MicrogridState> {
  const res = await fetch('/api/state', { signal })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return (await res.json()) as MicrogridState
}

export function connectStateWS(onState: (s: MicrogridState) => void) {
  // Connect directly to backend WS in dev (avoids Vite WS proxy instability).
  // If you deploy behind a single origin later, switch this back to a relative URL.
  const url = new URL('ws://localhost:8000/ws')
  const ws = new WebSocket(url.toString())

  ws.addEventListener('message', (ev) => {
    try {
      onState(JSON.parse(ev.data) as MicrogridState)
    } catch {
      // ignore
    }
  })

  return ws
}
