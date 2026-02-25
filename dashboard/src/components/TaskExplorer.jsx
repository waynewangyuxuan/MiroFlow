import { useState, useMemo } from 'react'
import { Search } from 'lucide-react'
import { color, size, radius, font } from '../styles/tokens'
import { getCategoryColor } from '../styles/tokens'
import { getCategory, getQuestion, getTaskId, getCategoryDistribution } from '../utils/data'

const S = {
  grid: {
    display: 'grid',
    gridTemplateColumns: '340px 1fr',
    gap: '16px',
    height: 'calc(100vh - 220px)',
  },
  panel: {
    background: color.surface,
    border: `1px solid ${color.border}`,
    borderRadius: radius.lg,
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden',
    minHeight: 0,   /* allow flex children to shrink for scroll */
  },
  searchWrap: {
    position: 'relative',
    padding: '12px 14px 0',
  },
  searchIcon: {
    position: 'absolute',
    left: '24px',
    top: '22px',
    color: color.textLight,
    pointerEvents: 'none',
  },
  input: {
    width: '100%',
    padding: '7px 10px 7px 30px',
    borderRadius: radius.md,
    border: `1px solid ${color.border}`,
    background: color.surfaceAlt,
    color: color.text,
    fontSize: size.sm,
    fontFamily: font.sans,
    outline: 'none',
    transition: 'border-color 0.12s',
  },
  filters: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '3px',
    padding: '8px 14px',
    borderBottom: `1px solid ${color.border}`,
  },
  filterBtn: (active, c) => ({
    padding: '3px 8px',
    borderRadius: '4px',
    fontSize: '10px',
    fontWeight: 500,
    fontFamily: font.sans,
    cursor: 'pointer',
    border: 'none',
    transition: 'all 0.1s',
    background: active ? `${c}12` : 'transparent',
    color: active ? c : color.textLight,
    letterSpacing: '0.01em',
  }),
  count: {
    fontSize: size.xs,
    color: color.textLight,
    padding: '6px 14px',
    borderBottom: `1px solid ${color.border}`,
  },
  list: {
    flex: 1,
    overflowY: 'auto',
    padding: '4px',
  },
  row: (selected) => ({
    padding: '9px 10px',
    borderRadius: radius.md,
    cursor: 'pointer',
    background: selected ? color.surfaceAlt : 'transparent',
    borderLeft: selected ? `2px solid ${color.accent}` : '2px solid transparent',
    transition: 'all 0.08s',
    marginBottom: '1px',
  }),
  rowCat: (c) => ({
    display: 'inline-block',
    fontSize: '10px',
    fontWeight: 500,
    color: c,
    letterSpacing: '0.02em',
  }),
  rowId: {
    fontSize: '10px',
    color: color.textLight,
    marginLeft: '8px',
  },
  rowQ: {
    fontSize: size.sm,
    color: color.textMuted,
    marginTop: '3px',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap',
    lineHeight: 1.3,
  },
  // Detail panel
  detailPad: {
    padding: '24px',
    overflowY: 'auto',
    flex: 1,
    minHeight: 0,
  },
  detailHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    marginBottom: '24px',
  },
  detailId: {
    fontSize: size.lg,
    fontWeight: 600,
    color: color.text,
    letterSpacing: '-0.02em',
  },
  badge: (c) => ({
    display: 'inline-block',
    padding: '2px 8px',
    borderRadius: '4px',
    fontSize: '10px',
    fontWeight: 500,
    background: `${c}10`,
    color: c,
  }),
  sectionLabel: {
    fontSize: size.xs,
    fontWeight: 500,
    color: color.textLight,
    textTransform: 'uppercase',
    letterSpacing: '0.06em',
    marginBottom: '8px',
  },
  questionText: {
    fontSize: size.base,
    lineHeight: 1.65,
    color: color.text,
    whiteSpace: 'pre-wrap',
    marginBottom: '28px',
  },
  pre: {
    background: color.surfaceAlt,
    padding: '16px',
    borderRadius: radius.md,
    fontSize: size.sm,
    fontFamily: font.mono,
    lineHeight: 1.55,
    overflowX: 'auto',
    whiteSpace: 'pre-wrap',
    wordBreak: 'break-word',
    color: color.textMuted,
    border: `1px solid ${color.border}`,
  },
}

export default function TaskExplorer({ data }) {
  const [search, setSearch] = useState('')
  const [selectedIdx, setSelectedIdx] = useState(0)
  const [filterCat, setFilterCat] = useState('all')

  const categories = useMemo(() => getCategoryDistribution(data), [data])

  const filtered = useMemo(() => {
    return data.filter((d) => {
      const cat = getCategory(d)
      if (filterCat !== 'all' && cat !== filterCat) return false
      if (search) {
        const text = JSON.stringify(d).toLowerCase()
        if (!text.includes(search.toLowerCase())) return false
      }
      return true
    })
  }, [data, search, filterCat])

  const selected = filtered[selectedIdx] || filtered[0]

  return (
    <div style={S.grid}>
      {/* Left: list */}
      <div style={S.panel}>
        <div style={S.searchWrap}>
          <Search size={13} style={S.searchIcon} strokeWidth={1.8} />
          <input
            style={S.input}
            placeholder="Search tasks..."
            value={search}
            onChange={(e) => { setSearch(e.target.value); setSelectedIdx(0) }}
          />
        </div>
        <div style={S.filters}>
          <button
            style={S.filterBtn(filterCat === 'all', color.accent)}
            onClick={() => { setFilterCat('all'); setSelectedIdx(0) }}
          >
            All
          </button>
          {categories.map(({ name, color: c }) => (
            <button
              key={name}
              style={S.filterBtn(filterCat === name, c)}
              onClick={() => { setFilterCat(name); setSelectedIdx(0) }}
            >
              {name}
            </button>
          ))}
        </div>
        <div style={S.count}>{filtered.length} tasks</div>
        <div style={S.list}>
          {filtered.map((d, i) => {
            const cat = getCategory(d)
            const catColor = getCategoryColor(cat)
            return (
              <div
                key={i}
                style={S.row(i === selectedIdx)}
                onClick={() => setSelectedIdx(i)}
              >
                <div>
                  <span style={S.rowCat(catColor)}>{cat}</span>
                  <span style={S.rowId}>#{getTaskId(d, i)}</span>
                </div>
                <div style={S.rowQ}>{getQuestion(d).slice(0, 100)}</div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Right: detail */}
      <div style={S.panel}>
        {selected ? (
          <div style={S.detailPad}>
            <div style={S.detailHeader}>
              <span style={S.detailId}>Task {getTaskId(selected, selectedIdx)}</span>
              <span style={S.badge(getCategoryColor(getCategory(selected)))}>
                {getCategory(selected)}
              </span>
            </div>

            <div style={S.sectionLabel}>Question</div>
            <div style={S.questionText}>{getQuestion(selected)}</div>

            <div style={S.sectionLabel}>Raw Data</div>
            <pre style={S.pre}>{JSON.stringify(selected, null, 2)}</pre>
          </div>
        ) : (
          <div style={{ color: color.textLight, textAlign: 'center', padding: '80px 0' }}>
            No task selected
          </div>
        )}
      </div>
    </div>
  )
}
