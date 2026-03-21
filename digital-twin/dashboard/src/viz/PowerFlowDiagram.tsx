import { useMemo } from 'react'

function clamp(n: number, min: number, max: number) {
  return Math.max(min, Math.min(max, n))
}

function fmtW(w: number) {
  if (!Number.isFinite(w)) return '—'
  if (Math.abs(w) >= 1000) return `${(w / 1000).toFixed(1)} kW`
  return `${w.toFixed(1)} W`
}

export default function PowerFlowDiagram({
  solarW,
  batterySoc,
  load1W,
  load2W,
  gridW,
}: {
  solarW: number
  batterySoc: number
  load1W: number
  load2W: number
  gridW: number
}) {
  const p1 = clamp(load1W / 200, 0, 1)
  const p2 = clamp(load2W / 200, 0, 1)
  const ps = clamp(solarW / 200, 0, 1)
  const pg = clamp(gridW / 200, 0, 1)

  const stroke1 = 2 + p1 * 4
  const stroke2 = 2 + p2 * 4
  const strokeS = 2 + ps * 4
  const strokeG = 2 + pg * 4

  const socPct = clamp(batterySoc / 100, 0, 1)

  const busGlow = useMemo(() => {
    const intensity = clamp((ps + pg) / 2, 0.12, 1)
    return 0.15 + intensity * 0.35
  }, [ps, pg])

  return (
    <div className="flowWrap">
      <svg className="flow" viewBox="0 0 980 360" preserveAspectRatio="xMidYMid meet">
        <defs>
          <linearGradient id="beam" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0" stopColor="rgba(124,92,255,0.95)" />
            <stop offset="1" stopColor="rgba(34,211,238,0.95)" />
          </linearGradient>
          <linearGradient id="grid" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0" stopColor="rgba(255,176,32,0.95)" />
            <stop offset="1" stopColor="rgba(255,92,122,0.95)" />
          </linearGradient>
          <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="3" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>

          <filter id="softShadow" x="-25%" y="-25%" width="150%" height="150%">
            <feDropShadow dx="0" dy="10" stdDeviation="10" floodColor="rgba(0,0,0,0.65)" />
          </filter>

          <pattern id="grid" width="28" height="28" patternUnits="userSpaceOnUse">
            <path d="M 28 0 L 0 0 0 28" fill="none" stroke="rgba(255,255,255,0.04)" strokeWidth="1" />
          </pattern>
        </defs>

        {/* Bus */}
        <rect x="466" y="84" width="48" height="192" rx="18" className="bus" />
        <rect
          x="472"
          y="96"
          width="36"
          height="168"
          rx="16"
          fill={`rgba(34,211,238,${busGlow})`}
          opacity="0.9"
        />

        {/* Solar -> Bus */}
        <path
          d="M 290 120 C 360 120, 400 120, 468 140"
          stroke="url(#beam)"
          strokeWidth={strokeS}
          fill="none"
          filter="url(#glow)"
          strokeDasharray="8 10"
          className="flowDash"
          strokeLinecap="round"
        />

        {/* Grid -> Bus (derived import) */}
        <path
          d="M 290 260 C 360 260, 400 260, 468 220"
          stroke="url(#grid)"
          strokeWidth={strokeG}
          fill="none"
          filter="url(#glow)"
          strokeDasharray="10 10"
          className="flowDashSlow"
          opacity={pg > 0 ? 1 : 0.35}
          strokeLinecap="round"
        />

        {/* Bus -> Load 1 */}
        <path
          d="M 512 150 C 600 130, 670 115, 750 120"
          stroke="rgba(255,255,255,0.80)"
          strokeWidth={stroke1}
          fill="none"
          strokeDasharray="10 12"
          className="flowDash"
          opacity={0.55 + p1 * 0.45}
          strokeLinecap="round"
        />

        {/* Bus -> Load 2 */}
        <path
          d="M 512 210 C 600 235, 670 250, 750 260"
          stroke="rgba(255,255,255,0.70)"
          strokeWidth={stroke2}
          fill="none"
          strokeDasharray="10 12"
          className="flowDash"
          opacity={0.5 + p2 * 0.5}
          strokeLinecap="round"
        />

        {/* Battery line */}
        <path
          d="M 360 190 C 420 190, 430 190, 468 180"
          stroke="rgba(57,217,138,0.75)"
          strokeWidth={2 + socPct * 3}
          fill="none"
          opacity={0.45 + socPct * 0.5}
          strokeLinecap="round"
        />
      </svg>

      {/* Fancy label cards overlay */}
      <div className="flowOverlay" aria-hidden>
        <div className="flowCard flowCardSolar">
          <div className="flowCardTitle">Solar PV</div>
          <div className="flowCardValue">{fmtW(solarW)}</div>
        </div>

        <div className="flowCard flowCardGrid">
          <div className="flowCardTitle">DC Grid</div>
          <div className="flowCardValue">{fmtW(gridW)}</div>
        </div>

        <div className="flowCard flowCardBattery">
          <div className="flowCardTitle">Battery</div>
          <div className="flowCardValue">{batterySoc.toFixed(1)}%</div>
        </div>

        <div className="flowCard flowCardLoad1">
          <div className="flowCardTitle">Load 1</div>
          <div className="flowCardValue">{fmtW(load1W)}</div>
        </div>

        <div className="flowCard flowCardLoad2">
          <div className="flowCardTitle">Load 2</div>
          <div className="flowCardValue">{fmtW(load2W)}</div>
        </div>
      </div>
    </div>
  )
}
