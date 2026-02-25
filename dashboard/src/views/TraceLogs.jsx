import { Activity } from 'lucide-react'
import { color, size } from '../styles/tokens'

export default function TraceLogs() {
  return (
    <div style={{
      background: color.surface,
      border: `1px solid ${color.border}`,
      borderRadius: '8px',
      padding: '64px 32px',
      textAlign: 'center',
      maxWidth: '480px',
    }}>
      <Activity size={24} color={color.textLight} strokeWidth={1.2} style={{ marginBottom: '12px' }} />
      <div style={{ fontSize: size.md, fontWeight: 500, color: color.textMuted, marginBottom: '6px' }}>
        Trace Log Viewer
      </div>
      <div style={{ fontSize: size.sm, color: color.textLight, lineHeight: 1.5 }}>
        Visualize agent reasoning chains from the logs/ directory. Coming next.
      </div>
    </div>
  )
}
