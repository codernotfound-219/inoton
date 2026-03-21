import { useMemo } from 'react'
import { Cloud, CloudOff, ThermometerSun } from 'lucide-react'

export default function TopBar({
  title,
  subtitle,
  connected,
}: {
  title: string
  subtitle: string
  connected: boolean
}) {
  const status = useMemo(
    () =>
      connected
        ? { label: 'Connected', cls: 'ok', icon: <Cloud size={16} /> }
        : { label: 'Offline', cls: 'bad', icon: <CloudOff size={16} /> },
    [connected],
  )

  return (
    <div className="topbar">
      <div>
        <div className="pageTitle">{title}</div>
        <div className="pageSub">{subtitle}</div>
      </div>

      <div className="topbarRight">
        <div className={`chip ${status.cls}`}>
          {status.icon}
          <span>{status.label}</span>
        </div>
        <div className="chip muted">
          <ThermometerSun size={16} />
          <span>Local sim</span>
        </div>
      </div>
    </div>
  )
}
