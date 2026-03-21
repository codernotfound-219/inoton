import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import TopBar from '../components/TopBar'
import { useTwinState } from '../state/useTwinState'
import { ThemedTooltip } from '../viz/ChartTooltip'

function makeReward() {
  // Placeholder curve.
  return Array.from({ length: 60 }, (_, i) => ({
    t: i,
    reward: -50 - i * 2 - Math.sin(i / 4) * 18,
  }))
}

export default function RlAgentPage() {
  const { derived } = useTwinState()
  const data = makeReward()

  return (
    <div className="page">
      <TopBar
        title="RL Agent Monitor"
        subtitle="Agent telemetry (UI ready; waiting for model integration)"
        connected={derived.connected}
      />

      <div className="grid3">
        <div className="panel">
          <div className="panelHeader">
            <div className="panelTitle">Q-Values — Current State</div>
            <div className="panelHint">Placeholder</div>
          </div>
          <div className="emptyState">Model not connected</div>
        </div>

        <div className="panel">
          <div className="panelHeader">
            <div className="panelTitle">Action Distribution</div>
            <div className="panelHint">Placeholder</div>
          </div>
          <div className="emptyState">Model not connected</div>
        </div>

        <div className="panel">
          <div className="panelHeader">
            <div className="panelTitle">Cumulative Reward</div>
            <div className="panelHint">Demo curve</div>
          </div>
          <div className="chart">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                <CartesianGrid stroke="rgba(255,255,255,0.06)" vertical={false} />
                <XAxis dataKey="t" tick={{ fill: 'rgba(255,255,255,0.55)', fontSize: 11 }} />
                <YAxis tick={{ fill: 'rgba(255,255,255,0.55)', fontSize: 11 }} />
                <Tooltip cursor={{ fill: 'rgba(255,255,255,0.00)' }} content={<ThemedTooltip />} />
                <Legend wrapperStyle={{ color: 'rgba(255,255,255,0.62)' }} />
                <Line type="monotone" dataKey="reward" stroke="#22d3ee" dot={false} strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="panel">
        <div className="panelHeader">
          <div className="panelTitle">Agent Action Log — Recent Decisions</div>
          <div className="panelHint">Placeholder table</div>
        </div>
        <div className="table">
          <div className="tableRow head">
            <div>Time</div>
            <div>State</div>
            <div>Action</div>
            <div>Reward</div>
          </div>
          {Array.from({ length: 7 }, (_, i) => (
            <div className="tableRow" key={i}>
              <div>—</div>
              <div>SoC=— Solar=— Load=—</div>
              <div className="accent">—</div>
              <div className="muted">—</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
