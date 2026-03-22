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

export async function setRelays(body: { relay1?: boolean; relay2?: boolean; target?: string }) {
  const base = getBackendHttpBase()
  const res = await fetch(`${base}/api/control/relays`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return (await res.json()) as { ok: boolean; command_id: string }
}

export async function shedLoad() {
  const base = getBackendHttpBase()
  const res = await fetch(`${base}/api/control/shed`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({}),
  })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return (await res.json()) as { ok: boolean; command_id: string; which: string }
}

export async function setBatteryMode(mode: 'CHARGE' | 'DISCHARGE' | 'IDLE' | 'AUTO') {
  const base = getBackendHttpBase()
  const res = await fetch(`${base}/api/control/battery_mode`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ mode }),
  })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return (await res.json()) as { ok: boolean; command_id: string; mode: string }
}

export async function simulateShortCircuitFault(reason?: string) {
  const base = getBackendHttpBase()
  const res = await fetch(`${base}/api/control/fault/short_circuit`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(reason ? { reason } : {}),
  })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return (await res.json()) as {
    ok: boolean
    fault_active: boolean
    fault_code: string
    command_id_relays: string
    command_id_battery: string
  }
}

export async function clearFault() {
  const base = getBackendHttpBase()
  const res = await fetch(`${base}/api/control/fault/clear`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({}),
  })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return (await res.json()) as { ok: boolean; fault_active: boolean }
}
