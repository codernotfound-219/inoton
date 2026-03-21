import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import TopBar from '../components/TopBar'
import { useTwinState } from '../state/useTwinState'
import { ThemedTooltip } from '../viz/ChartTooltip'

const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

function seedDaily() {
  // Placeholder analytics until backend/model provides aggregates.
  const base = 420
  return Array.from({ length: 7 }, (_, i) => {
    const solar = 40 + (i % 3) * 10
    const grid = base - solar + (i % 2) * 25
    const battery = 15 + (i % 4) * 6
    return { day: days[i], solar, battery, grid }
  })
}

export default function AnalyticsPage() {
  const { derived } = useTwinState()
  const daily = seedDaily()

  const loadDist = [
    { name: 'Load 1', value: derived.load1W },
    { name: 'Load 2', value: derived.load2W },
  ]

  return (
    <div className="page">
      <TopBar
        title="Energy Analytics"
        subtitle="Weekly energy breakdown & cost analysis (placeholders until model/backfill)"
        connected={derived.connected}
      />

      <div className="panel">
        <div className="panelHeader">
          <div className="panelTitle">Daily Energy Breakdown (kWh)</div>
          <div className="panelHint">Stacked bars: Solar / Battery / Grid Import</div>
        </div>
        <div className="chart chartTall">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={daily} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
              <CartesianGrid stroke="rgba(255,255,255,0.06)" vertical={false} />
              <XAxis dataKey="day" tick={{ fill: 'rgba(255,255,255,0.55)', fontSize: 11 }} />
              <YAxis tick={{ fill: 'rgba(255,255,255,0.55)', fontSize: 11 }} />
              <Tooltip cursor={{ fill: 'rgba(255,255,255,0.00)' }} content={<ThemedTooltip />} />
              <Legend wrapperStyle={{ color: 'rgba(255,255,255,0.62)' }} />
              <Bar dataKey="solar" stackId="a" fill="#7c5cff" radius={[6, 6, 0, 0]} />
              <Bar dataKey="battery" stackId="a" fill="#39d98a" />
              <Bar dataKey="grid" stackId="a" fill="#ff5c7a" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="grid2">
        <div className="panel">
          <div className="panelHeader">
            <div className="panelTitle">Cost Savings vs Baseline (₹)</div>
            <div className="panelHint">Placeholder until RL agent metrics exist</div>
          </div>
          <div className="chart">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={daily} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                <CartesianGrid stroke="rgba(255,255,255,0.06)" vertical={false} />
                <XAxis dataKey="day" tick={{ fill: 'rgba(255,255,255,0.55)', fontSize: 11 }} />
                <YAxis tick={{ fill: 'rgba(255,255,255,0.55)', fontSize: 11 }} />
                <Tooltip cursor={{ fill: 'rgba(255,255,255,0.00)' }} content={<ThemedTooltip />} />
                <Bar dataKey="grid" fill="#22d3ee" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="panel">
          <div className="panelHeader">
            <div className="panelTitle">Load Distribution</div>
            <div className="panelHint">Derived split until per-load telemetry arrives</div>
          </div>
          <div className="chart">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Tooltip content={<ThemedTooltip />} />
                <Pie data={loadDist} dataKey="value" nameKey="name" innerRadius={45} outerRadius={78}>
                  {loadDist.map((_, idx) => (
                    <Cell
                      key={idx}
                      fill={idx === 0 ? 'rgba(124, 92, 255, 0.95)' : 'rgba(34, 211, 238, 0.95)'}
                      stroke="rgba(255,255,255,0.15)"
                      strokeWidth={1}
                    />
                  ))}
                </Pie>
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="panelFooter">
            <div className="metric">Load 1</div>
            <div className="metric">Load 2</div>
          </div>
        </div>
      </div>
    </div>
  )
}
