import TopBar from '../components/TopBar'
import { useTwinState } from '../state/useTwinState'

const tariff = [
  { period: 'Off-Peak', hours: '00:00 - 06:00', rate: '₹4.5', type: 'Off-Peak' },
  { period: 'Standard', hours: '06:00 - 09:00', rate: '₹6.8', type: 'Standard' },
  { period: 'Peak', hours: '09:00 - 12:00', rate: '₹9.2', type: 'Peak' },
  { period: 'Standard', hours: '12:00 - 17:00', rate: '₹7.5', type: 'Standard' },
  { period: 'Peak', hours: '17:00 - 21:00', rate: '₹9.8', type: 'Peak' },
  { period: 'Standard', hours: '21:00 - 23:00', rate: '₹6.8', type: 'Standard' },
  { period: 'Off-Peak', hours: '23:00 - 24:00', rate: '₹4.5', type: 'Off-Peak' },
]

const normalization = [
  { param: 'Solar Power', hw: '0–4095 ADC', real: '0–200 W', conv: '0.049 W/bit' },
  { param: 'Battery Voltage', hw: '0–4095 ADC', real: '40–58.4 V', conv: '4.49 mV/bit' },
  { param: 'Load Current', hw: '0–4095 ADC', real: '0–5 A', conv: '1.22 mA/bit' },
  { param: 'Temperature', hw: '0–4095 ADC', real: '-10–60 °C', conv: '0.017 °C/bit' },
  { param: 'SoC Estimation', hw: 'Coulomb count', real: '0–100%', conv: 'Kalman filter' },
]

export default function SystemConfigPage() {
  const { state, derived } = useTwinState()

  return (
    <div className="page">
      <TopBar
        title="System Configuration"
        subtitle="Microgrid parameters & connection status (read-only)"
        connected={derived.connected}
      />

      <div className="grid2">
        <div className="panel">
          <div className="panelHeader">
            <div className="panelTitle">System Parameters</div>
            <div className="panelHint">Read-only (wired later)</div>
          </div>
          <div className="kv">
            <div className="kvRow">
              <div>Solar Capacity</div>
              <div className="kvVal">200 W</div>
            </div>
            <div className="kvRow">
              <div>Battery Capacity</div>
              <div className="kvVal">—</div>
            </div>
            <div className="kvRow">
              <div>Battery SOC (live)</div>
              <div className="kvVal">{state.battery_soc.toFixed(1)}%</div>
            </div>
            <div className="kvRow">
              <div>Update Interval</div>
              <div className="kvVal">1000 ms</div>
            </div>
          </div>
        </div>

        <div className="panel">
          <div className="panelHeader">
            <div className="panelTitle">Connection Status</div>
            <div className="panelHint">Live where available</div>
          </div>
          <div className="kv">
            <div className="kvRow">
              <div>Operating Mode</div>
              <div className="badge ok">Simulation</div>
            </div>
            <div className="kvRow">
              <div>MQTT Broker</div>
              <div className={`badge ${derived.connected ? 'ok' : 'bad'}`}>{derived.connected ? 'Connected' : 'Disconnected'}</div>
            </div>
            <div className="kvRow">
              <div>ESP32 Node</div>
              <div className="badge bad">Not connected</div>
            </div>
            <div className="kvRow">
              <div>Relay Control</div>
              <div className="badge muted">Future</div>
            </div>
          </div>
          <div className="note">
            Control will be added as a command endpoint publishing to the ESP32 control MQTT topic.
          </div>
        </div>
      </div>

      <div className="panel">
        <div className="panelHeader">
          <div className="panelTitle">Tariff Schedule</div>
          <div className="panelHint">Placeholder</div>
        </div>
        <div className="table">
          <div className="tableRow head">
            <div>Period</div>
            <div>Hours</div>
            <div>Rate</div>
            <div>Type</div>
          </div>
          {tariff.map((t) => (
            <div className="tableRow" key={`${t.period}-${t.hours}`}>
              <div>{t.period}</div>
              <div className="muted">{t.hours}</div>
              <div>{t.rate}</div>
              <div className={`tag ${t.type.toLowerCase().replace('-', '')}`}>{t.type}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="panel">
        <div className="panelHeader">
          <div className="panelTitle">ESP32 Data Normalization — HW vs Real-World</div>
          <div className="panelHint">Placeholder table</div>
        </div>
        <div className="table">
          <div className="tableRow head">
            <div>Parameter</div>
            <div>HW Scale</div>
            <div>Real-World Scale</div>
            <div>Conversion</div>
          </div>
          {normalization.map((n) => (
            <div className="tableRow" key={n.param}>
              <div>{n.param}</div>
              <div className="muted">{n.hw}</div>
              <div className="accent">{n.real}</div>
              <div className="muted">{n.conv}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
