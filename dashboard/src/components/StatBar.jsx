import { color, size, radius } from '../styles/tokens'
import { getCategoryDistribution } from '../utils/data'

const S = {
  bar: {
    display: 'flex',
    gap: '1px',
    background: color.border,
    borderRadius: radius.lg,
    overflow: 'hidden',
    marginBottom: '24px',
  },
  cell: {
    flex: 1,
    background: color.surface,
    padding: '20px 16px',
    textAlign: 'center',
  },
  num: (c) => ({
    fontSize: '22px',
    fontWeight: 600,
    color: c || color.text,
    letterSpacing: '-0.03em',
    lineHeight: 1,
    marginBottom: '6px',
  }),
  label: {
    fontSize: size.xs,
    color: color.textLight,
    letterSpacing: '0.02em',
  },
}

export default function StatBar({ data }) {
  const dist = getCategoryDistribution(data)
  const fields = data[0] ? Object.keys(data[0]) : []

  return (
    <div style={S.bar}>
      <div style={S.cell}>
        <div style={S.num()}>{data.length}</div>
        <div style={S.label}>Tasks</div>
      </div>
      <div style={S.cell}>
        <div style={S.num()}>{dist.length}</div>
        <div style={S.label}>Categories</div>
      </div>
      <div style={S.cell}>
        <div style={S.num()}>{fields.length}</div>
        <div style={S.label}>Fields</div>
      </div>
      {dist.slice(0, 5).map(({ name, count, color: c }) => (
        <div key={name} style={S.cell}>
          <div style={S.num(c)}>{count}</div>
          <div style={S.label}>{name}</div>
        </div>
      ))}
    </div>
  )
}
