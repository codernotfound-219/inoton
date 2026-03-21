import { NavLink, Outlet } from 'react-router-dom'
import {
  Activity,
  ChartColumnBig,
  Cpu,
  LayoutDashboard,
  Settings,
  Zap,
} from 'lucide-react'

function Item({ to, label, icon }: { to: string; label: string; icon: JSX.Element }) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) => `navItem ${isActive ? 'active' : ''}`}
      end
    >
      <span className="navIcon">{icon}</span>
      <span>{label}</span>
    </NavLink>
  )
}

export default function AppShell() {
  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <div className="brandMark">
            <Zap size={18} />
          </div>
          <div className="brandText">
            <div className="brandName">DC Microgrid</div>
            <div className="brandSub">Digital Twin v1.0</div>
          </div>
        </div>

        <nav className="nav">
          <Item to="/dashboard" label="Dashboard" icon={<LayoutDashboard size={18} />} />
          <Item to="/analytics" label="Analytics" icon={<ChartColumnBig size={18} />} />
          <Item to="/rl-agent" label="RL Agent" icon={<Cpu size={18} />} />
          <Item to="/system-config" label="System Config" icon={<Settings size={18} />} />
        </nav>

        <div className="sidebarFooter">
          <div className="simDot" />
          <div>
            <div className="simTitle">Simulation Active</div>
            <div className="simSub">MQTT + Twin state feed</div>
          </div>
          <Activity size={16} className="simIcon" />
        </div>
      </aside>

      <main className="main">
        <Outlet />
      </main>
    </div>
  )
}
