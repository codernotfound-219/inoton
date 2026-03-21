import type { MicrogridState } from './types'

function getBackendHttpBase() {
  const host = import.meta.env.VITE_BACKEND_HOST ?? 'localhost'
  const port = import.meta.env.VITE_BACKEND_PORT ?? '8000'
  const proto = import.meta.env.VITE_BACKEND_HTTP_PROTO ?? 'http'
  return `${proto}://${host}:${port}`
}

function getBackendWsBase() {
  const host = import.meta.env.VITE_BACKEND_HOST ?? 'localhost'
  const port = import.meta.env.VITE_BACKEND_PORT ?? '8000'
  const proto = import.meta.env.VITE_BACKEND_WS_PROTO ?? 'ws'
  return `${proto}://${host}:${port}`
}

export async function fetchState(signal?: AbortSignal): Promise<MicrogridState> {
  const base = getBackendHttpBase()
  const res = await fetch(`${base}/api/state`, { signal })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return (await res.json()) as MicrogridState
}

export function connectStateWS(onState: (s: MicrogridState) => void) {
  const base = getBackendWsBase()
  const url = new URL(`${base}/ws`)
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
