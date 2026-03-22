import { useMemo } from 'react'
import {
  Area,
  AreaChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { useTwinState } from '../state/useTwinState'
import TopBar from '../components/TopBar'
import PowerFlowDiagram from '../viz/PowerFlowDiagram'
import { ThemedTooltip } from '../viz/ChartTooltip'
import { setBatteryMode, setRelays, shedLoad } from '../api'
import { getFakeRlAction } from '../rl/fakeAgent'

function fmtW(w: number) {
  if (!Number.isFinite(w)) return '—'
  if (Math.abs(w) >= 1000) return `${(w / 1000).toFixed(1)} kW`
  return `${w.toFixed(1)} W`
}

function fmtPct(n: number) {
  if (!Number.isFinite(n)) return '—'
  return `${n.toFixed(1)}%`
}

function fmtA(a: number) {
  if (!Number.isFinite(a)) return '—'
  return `${a.toFixed(2)} A`
}

function fmtTime(t: number) {
  const d = new Date(t)
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

export default function DashboardPage() {
  const { state, derived } = useTwinState()

  const canControl = derived.connected

  const doSetRelay = async (which: 'relay1' | 'relay2', value: boolean) => {
    try {
      await setRelays({ [which]: value })
    } catch {
      // ignore for now
    }
  }

  const doShed = async () => {
    try {
      await shedLoad()
    } catch {
      // ignore
    }
  }

  const doBatteryMode = async (mode: 'CHARGE' | 'DISCHARGE' | 'IDLE' | 'AUTO') => {
    try {
      await setBatteryMode(mode)
    } catch {
      // ignore
    }
  }

  const chartData = useMemo(
    () =>
      derived.history.map((p) => ({
        t: p.t,
        time: fmtTime(p.t),
        solar: p.solar_w,
        load: p.load_total_w,
        grid: p.grid_import_w,
        soc: p.battery_soc,
      })),
    [derived.history],
  )

  const actionText = useMemo(() => {
    return getFakeRlAction(state)
  }, [state])

  return (
    <div className="page">
      <TopBar
        title="System Overview"
        subtitle="Campus DC Microgrid — Digital Twin (live telemetry)"
        connected={derived.connected}
      />

      <div className="kpiRow">
        <div className="kpiCard">
          <div className="kpiTop">
            <div className="kpiTitle">Solar Generation</div>
          </div>
          <div className="kpiBig">{fmtW(state.solar_watts)}</div>
          <div className="kpiSub">0 kWh today</div>
        </div>

        <div className="kpiCard">
          <div className="kpiTop">
            <div className="kpiTitle">Battery SoC</div>
            <div className="kpiPill">Status: nominal</div>
          </div>
          <div className="kpiBig">{fmtPct(state.battery_soc)}</div>
          <div className="kpiSub">Temp: {state.battery_temp.toFixed(1)}°C</div>
        </div>

        <div className="kpiCard">
          <div className="kpiTop">
            <div className="kpiTitle">Grid Import (derived)</div>
          </div>
          <div className="kpiBig">{fmtW(derived.gridImportW)}</div>
          <div className="kpiSub">max(0, load − solar)</div>
        </div>

        <div className="kpiCard">
          <div className="kpiTop">
            <div className="kpiTitle">RL Agent Action</div>
          </div>
          <div className="kpiBig kpiAccent">{actionText.label}</div>
          <div className="kpiSub">{actionText.reason}</div>
        </div>
      </div>

      <div className="panel">
        <div className="panelHeader">
          <div className="panelTitle">Animated Power Flow — Digital Twin</div>
          <div className="panelHint">Solar PV • Battery • DC Bus • Load 1 • Load 2</div>
        </div>
        <PowerFlowDiagram
          solarW={state.solar_watts}
          batterySoc={state.battery_soc}
          load1W={derived.load1W}
          load2W={derived.load2W}
          gridW={derived.gridImportW}
        />
      </div>

      <div className="grid2">
        <div className="panel">
          <div className="panelHeader">
            <div className="panelTitle">Battery Control</div>
            <div className="panelHint">Manual override (safe dead-time enforced on ESP)</div>
          </div>
          <div className="panelFooter">
            <div className="metric">SoC: {fmtPct(state.battery_soc)}</div>
            <div className="metric">Bus V: {state.bus_v ? `${state.bus_v.toFixed(2)} V` : '—'}</div>
          </div>
          <div className="bottomBar">
            <div className="bottomLeft">
              <button className="btn" disabled={!canControl} onClick={() => doBatteryMode('CHARGE')} title="Force battery controller into CHARGE mode">
                Charge
              </button>
              <button className="btn" disabled={!canControl} onClick={() => doBatteryMode('DISCHARGE')} title="Force battery controller into DISCHARGE mode">
                Discharge
              </button>
              <button className="btn" disabled={!canControl} onClick={() => doBatteryMode('IDLE')} title="Force battery controller into IDLE (both relays off)">
                Idle
              </button>
              <button className="btn" disabled={!canControl} onClick={() => doBatteryMode('AUTO')} title="Return battery controller to automatic voltage-based control">
                Auto
              </button>
            </div>
            <div className="hint">Targets `battery` ESP</div>
          </div>
        </div>

        <div className="panel">
          <div className="panelHeader">
            <div className="panelTitle">Load Control</div>
            <div className="panelHint">Relay actions reflected in schematic</div>
          </div>
          <div className="panelFooter">
            <div className="metric">Load 1: {state.relay_load1 ? fmtW(derived.load1W) : 'OFF'}</div>
            <div className="metric">Load 2: {state.relay_load2 ? fmtW(derived.load2W) : 'OFF'}</div>
            <div className="metric">Total: {fmtW(state.total_load)}</div>
          </div>
          <div className="bottomBar">
            <div className="bottomLeft">
              <button className="btn" disabled={!canControl} onClick={() => doSetRelay('relay1', !state.relay_load1)} title="Toggle Load 1 relay">
                Toggle Load 1
              </button>
              <button className="btn" disabled={!canControl} onClick={() => doSetRelay('relay2', !state.relay_load2)} title="Toggle Load 2 relay">
                Toggle Load 2
              </button>
              <button className="btn danger" disabled={!canControl} onClick={doShed} title="Shed the smaller load (backend chooses)">
                Shed Smaller Load
              </button>
            </div>
            <div className="hint">Requires ESP ACK on `microgrid/control/ack`</div>
          </div>
        </div>
      </div>

      <div className="grid2">
        <div className="panel">
          <div className="panelHeader">
            <div className="panelTitle">Power Overview — Last 2 Hours</div>
            <div className="panelHint">Solar vs Load vs Grid Import</div>
          </div>
          <div className="chart">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                <CartesianGrid stroke="rgba(255,255,255,0.06)" vertical={false} />
                <XAxis dataKey="time" tick={{ fill: 'rgba(255,255,255,0.55)', fontSize: 11 }} />
                <YAxis tick={{ fill: 'rgba(255,255,255,0.55)', fontSize: 11 }} />
                <Tooltip cursor={{ fill: 'rgba(255,255,255,0.00)' }} content={<ThemedTooltip />} />
                <Line type="monotone" dataKey="solar" stroke="#7c5cff" dot={false} strokeWidth={2} />
                <Line type="monotone" dataKey="load" stroke="#22d3ee" dot={false} strokeWidth={2} />
                <Line type="monotone" dataKey="grid" stroke="#ffb020" dot={false} strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <div className="panelFooter">
            <div className="metric">Line current: {fmtA(state.current_a)}</div>
            <div className="metric">Relay: {state.relay_status ? 'ON' : 'OFF'}</div>
            <div className="metric">Source: {state.active_source}</div>
          </div>
        </div>

        <div className="panel">
          <div className="panelHeader">
            <div className="panelTitle">Battery State of Charge — Last 2 Hours</div>
            <div className="panelHint">Rolling history stored locally</div>
          </div>
          <div className="chart">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                <CartesianGrid stroke="rgba(255,255,255,0.06)" vertical={false} />
                <XAxis dataKey="time" tick={{ fill: 'rgba(255,255,255,0.55)', fontSize: 11 }} />
                <YAxis domain={[0, 100]} tick={{ fill: 'rgba(255,255,255,0.55)', fontSize: 11 }} />
                <Tooltip cursor={{ fill: 'rgba(255,255,255,0.00)' }} content={<ThemedTooltip />} />
                <Area
                  type="monotone"
                  dataKey="soc"
                  stroke="#39d98a"
                  fill="rgba(57,217,138,0.20)"
                  strokeWidth={2}
                  dot={false}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
          <div className="panelFooter">
            <div className="metric">Load 1: {fmtW(derived.load1W)}</div>
            <div className="metric">Load 2: {fmtW(derived.load2W)}</div>
            <div className="metric">Total: {fmtW(state.total_load)}</div>
          </div>
        </div>
      </div>

      <div className="bottomBar">
        <div className="bottomLeft">
          <span className="label">Mode</span>
          <select
            className="select"
            value={derived.mode}
            onChange={(e) => derived.setMode(e.target.value as any)}
            title="Select data transport mode"
          >
            <option value="ws">WebSocket</option>
            <option value="poll">HTTP Poll</option>
          </select>
          <span className="hint">History persisted in localStorage</span>
        </div>
      </div>
    </div>
  )
}
