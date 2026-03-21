export type HistoryPoint = {
  t: number // epoch ms
  solar_w: number
  load_total_w: number
  load1_w: number
  load2_w: number
  battery_soc: number
  current_a: number
  grid_import_w: number
}

const KEY = 'dt.history.v1'

export function loadHistory(): HistoryPoint[] {
  try {
    const raw = localStorage.getItem(KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw) as HistoryPoint[]
    if (!Array.isArray(parsed)) return []
    return parsed.filter((p) => typeof p?.t === 'number')
  } catch {
    return []
  }
}

export function saveHistory(points: HistoryPoint[]) {
  try {
    localStorage.setItem(KEY, JSON.stringify(points))
  } catch {
    // ignore
  }
}

export function trimToWindow(points: HistoryPoint[], windowMs: number) {
  const cutoff = Date.now() - windowMs
  return points.filter((p) => p.t >= cutoff)
}
