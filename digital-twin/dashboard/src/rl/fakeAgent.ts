import type { MicrogridState } from '../types'

export type FakeRlAction = {
  label: string
  reason: string
}

function clamp(n: number, lo: number, hi: number) {
  return Math.max(lo, Math.min(hi, n))
}

function fmtW(w: number) {
  if (!Number.isFinite(w)) return '—'
  if (Math.abs(w) >= 1000) return `${(w / 1000).toFixed(1)} kW`
  return `${w.toFixed(0)} W`
}

export function getFakeRlAction(state: MicrogridState): FakeRlAction {
  // Purely visual “policy” for demo purposes.
  // Deterministic + stable unless inputs cross thresholds.

  const solar = Number.isFinite(state.solar_watts) ? state.solar_watts : 0
  const load = Number.isFinite(state.total_load) ? state.total_load : 0
  const soc = Number.isFinite(state.battery_soc) ? state.battery_soc : 0

  const relay1On = !!state.relay_load1
  const relay2On = !!state.relay_load2

  // If something is shed, highlight that the system is in a constrained mode.
  if (!relay1On || !relay2On) {
    const off = [!relay1On ? 'Load 1' : null, !relay2On ? 'Load 2' : null].filter(Boolean).join(' + ')
    return {
      label: 'Stability Mode (load shed)'
        + '',
      reason: `${off} disconnected → prioritize bus stability`,
    }
  }

  const deficit = load - solar // +ve means demand exceeds solar

  // SOC bands for a 1-minute demo (keeps outputs stable)
  const highSoc = soc >= 90
  const midSoc = soc >= 60 && soc < 90
  const lowSoc = soc < 60

  // Thresholds for “meaningful” mismatch to avoid flapping.
  // For the demo power range (tens of watts), a 15W minimum deadband makes the
  // policy look “stuck” in near-balance. Keep it responsive but stable.
  const deadbandW = clamp(load * 0.06, 4, 25) // ~6% of load, bounded

  if (deficit > deadbandW) {
    if (highSoc || midSoc) {
      return {
        label: 'Discharge Battery (cover deficit)',
        reason: `Load ${fmtW(load)} > Solar ${fmtW(solar)}; SoC ${soc.toFixed(0)}%`,
      }
    }
    // low SOC
    return {
      label: 'Conserve Battery (grid/import preferred)',
      reason: `Low SoC ${soc.toFixed(0)}% with deficit ${fmtW(deficit)}`,
    }
  }

  if (deficit < -deadbandW) {
    // Excess solar
    if (soc < 98) {
      return {
        label: 'Charge Battery (use excess solar)',
        reason: `Solar ${fmtW(solar)} > Load ${fmtW(load)}; SoC ${soc.toFixed(0)}%`,
      }
    }
    return {
      label: 'Curtail/hold (battery full)',
      reason: `SoC ${soc.toFixed(0)}% with solar surplus`,
    }
  }

  // Near-balance region
  if (highSoc) {
    return {
      label: 'Solar-First (hold battery)',
      reason: `Near balance; SoC ${soc.toFixed(0)}%`,
    }
  }

  if (midSoc) {
    return {
      label: 'Eco Mode (minimize switching)',
      reason: `Near balance; SoC ${soc.toFixed(0)}%`,
    }
  }

  if (lowSoc) {
    return {
      label: 'Recovery Mode (charge when possible)',
      reason: `Near balance; low SoC ${soc.toFixed(0)}%`,
    }
  }

  return {
    label: 'Policy Active',
    reason: 'Stable operating region',
  }
}
