type TooltipProps = {
  active?: boolean
  label?: string
  payload?: Array<{ name?: string; value?: number | string; color?: string }>
}

function colorToken(color: string | undefined) {
  // Map known chart colors to CSS tokens (keeps tooltip consistent and avoids inline styles).
  switch ((color ?? '').toLowerCase()) {
    case '#7c5cff':
    case 'rgba(124, 92, 255, 0.95)':
    case 'rgba(124,92,255,0.95)':
      return 'purple'
    case '#22d3ee':
    case 'rgba(34, 211, 238, 0.95)':
    case 'rgba(34,211,238,0.95)':
      return 'cyan'
    case '#39d98a':
    case 'rgba(57, 217, 138, 0.95)':
    case 'rgba(57,217,138,0.95)':
      return 'green'
    case '#ff5c7a':
    case 'rgba(255, 92, 122, 0.95)':
    case 'rgba(255,92,122,0.95)':
      return 'pink'
    case '#ffb020':
    case 'rgba(255, 176, 32, 0.92)':
    case 'rgba(255,176,32,0.92)':
      return 'amber'
    default:
      return 'muted'
  }
}

function formatValue(v: unknown) {
  if (typeof v === 'number' && Number.isFinite(v)) return v.toFixed(0)
  return String(v ?? '—')
}

export function ThemedTooltip({ active, label, payload }: TooltipProps) {
  if (!active || !payload?.length) return null

  return (
    <div className="chartTip">
      {label ? <div className="chartTipLabel">{label}</div> : null}
      {payload.map((p, idx) => (
        <div key={idx} className="chartTipRow">
          <span className="chartTipName">
            <span className={`chartTipDot chartTipDot--${colorToken(p.color)}`} />
            <span>{p.name ?? '—'}</span>
          </span>
          <span className="chartTipValue">{formatValue(p.value)}</span>
        </div>
      ))}
    </div>
  )
}
