import { useEffect, useMemo, useRef, useState } from 'react'
import { connectStateWS, fetchState } from '../api'
import type { MicrogridState } from '../types'
import { defaultState } from '../types'
import { loadHistory, saveHistory, trimToWindow, type HistoryPoint } from './history'

function splitLoads(total: number) {
  // Placeholder until separate load measurements exist.
  const load1 = total * 0.55
  const load2 = total * 0.45
  return { load1, load2 }
}

export type TwinDerived = {
  gridImportW: number
  load1W: number
  load2W: number
  connected: boolean
  mode: 'ws' | 'poll'
  setMode: (m: 'ws' | 'poll') => void
  history: HistoryPoint[]
}

const HISTORY_WINDOW_MS = 2 * 60 * 60 * 1000

export function useTwinState(): { state: MicrogridState; derived: TwinDerived } {
  const [state, setState] = useState<MicrogridState>(defaultState)
  const [connected, setConnected] = useState(false)
  const [mode, setMode] = useState<'ws' | 'poll'>('ws')

  const historyRef = useRef<HistoryPoint[]>(loadHistory())
  const lastSeen = useRef<number>(0)

  useEffect(() => {
    let ws: WebSocket | null = null
    let pollTimer: number | null = null
    let aborter: AbortController | null = null

    const onState = (s: MicrogridState) => {
      setState(s)
      setConnected(true)
      lastSeen.current = Date.now()

      const gridImportW = Math.max(0, s.total_load - s.solar_watts)
      const { load1, load2 } = splitLoads(s.total_load)

      const nextPoint: HistoryPoint = {
        t: Date.now(),
        solar_w: s.solar_watts,
        load_total_w: s.total_load,
        load1_w: load1,
        load2_w: load2,
        battery_soc: s.battery_soc,
        current_a: s.current_a,
        grid_import_w: gridImportW,
      }

      const next = trimToWindow([...historyRef.current, nextPoint], HISTORY_WINDOW_MS)
      historyRef.current = next
      saveHistory(next)
    }

    const startWS = () => {
      ws = connectStateWS(onState)
      ws.addEventListener('open', () => setConnected(true))
      ws.addEventListener('close', () => setConnected(false))
      ws.addEventListener('error', () => setConnected(false))
    }

    const startPoll = () => {
      const tick = async () => {
        aborter?.abort()
        aborter = new AbortController()
        try {
          const s = await fetchState(aborter.signal)
          onState(s)
        } catch {
          setConnected(false)
        }
      }
      void tick()
      pollTimer = window.setInterval(tick, 1000)
    }

    if (mode === 'ws') startWS()
    else startPoll()

    const staleTimer = window.setInterval(() => {
      if (Date.now() - lastSeen.current > 3500) setConnected(false)
    }, 800)

    return () => {
      if (ws) ws.close()
      if (pollTimer) window.clearInterval(pollTimer)
      if (staleTimer) window.clearInterval(staleTimer)
      aborter?.abort()
    }
  }, [mode])

  const derived = useMemo((): TwinDerived => {
    const gridImportW = Math.max(0, state.total_load - state.solar_watts)
    const { load1, load2 } = splitLoads(state.total_load)
    return {
      gridImportW,
      load1W: load1,
      load2W: load2,
      connected,
      mode,
      setMode,
      history: historyRef.current,
    }
  }, [state, connected, mode])

  return { state, derived }
}
