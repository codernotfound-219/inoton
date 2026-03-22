export type MicrogridState = {
  solar_watts: number
  battery_soc: number
  battery_temp: number
  total_load: number
  current_a: number
  bus_v: number

  predicted_load: number
  predicted_solar: number
  anomaly_score: number

  relay_status: boolean
  relay_load1: boolean
  relay_load2: boolean
  active_source: string

  last_updated: number
}

export const defaultState: MicrogridState = {
  solar_watts: 0,
  battery_soc: 100,
  battery_temp: 25,
  total_load: 0,
  current_a: 0,
  bus_v: 0,
  predicted_load: 0,
  predicted_solar: 0,
  anomaly_score: 0,
  relay_status: true,
  relay_load1: true,
  relay_load2: true,
  active_source: 'Solar',
  last_updated: 0,
}
