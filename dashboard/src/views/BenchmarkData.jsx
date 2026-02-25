import { color, size, font } from '../styles/tokens'
import { useDataLoader } from '../hooks/useDataLoader'
import FileDropZone from '../components/FileDropZone'
import StatBar from '../components/StatBar'
import TaskExplorer from '../components/TaskExplorer'
import { Database, Loader } from 'lucide-react'

const S = {
  emptyCard: {
    background: color.surface,
    border: `1px solid ${color.border}`,
    borderRadius: '8px',
    padding: '32px',
    maxWidth: '520px',
  },
  title: {
    fontSize: size.lg,
    fontWeight: 600,
    color: color.text,
    letterSpacing: '-0.02em',
    marginBottom: '8px',
  },
  desc: {
    fontSize: size.sm,
    color: color.textMuted,
    lineHeight: 1.5,
    marginBottom: '20px',
  },
  code: {
    display: 'block',
    background: color.surfaceAlt,
    border: `1px solid ${color.border}`,
    borderRadius: '6px',
    padding: '12px 14px',
    fontSize: '12px',
    fontFamily: font.mono,
    color: color.textMuted,
    lineHeight: 1.5,
    whiteSpace: 'pre',
    overflowX: 'auto',
    marginBottom: '20px',
  },
  loadedHeader: {
    display: 'flex',
    alignItems: 'baseline',
    justifyContent: 'space-between',
    marginBottom: '20px',
  },
  pageTitle: {
    fontSize: size.xl,
    fontWeight: 600,
    color: color.text,
    letterSpacing: '-0.03em',
  },
  meta: {
    fontSize: size.xs,
    color: color.textLight,
  },
  headerRight: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  dsBtn: (active) => ({
    padding: '4px 10px',
    borderRadius: '4px',
    border: `1px solid ${active ? color.accent : color.border}`,
    background: active ? `${color.accent}08` : 'transparent',
    color: active ? color.accent : color.textMuted,
    fontSize: '11px',
    fontWeight: 500,
    cursor: 'pointer',
    fontFamily: font.sans,
  }),
  uploadBtn: {
    padding: '4px 10px',
    borderRadius: '4px',
    border: `1px solid ${color.border}`,
    background: 'transparent',
    color: color.textLight,
    fontSize: '11px',
    cursor: 'pointer',
    fontFamily: font.sans,
  },
  loading: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    padding: '40px 0',
    color: color.textLight,
    fontSize: size.sm,
  },
}

export default function BenchmarkData() {
  const { data, fileName, error, loading, available, loadFile, switchDataset, reset } = useDataLoader()

  // Loading state
  if (loading) {
    return (
      <div style={S.loading}>
        <Loader size={14} strokeWidth={1.5} style={{ animation: 'spin 1s linear infinite' }} />
        Loading datasets...
        <style>{`@keyframes spin { to { transform: rotate(360deg) } }`}</style>
      </div>
    )
  }

  // No data loaded and none found automatically
  if (!data) {
    return (
      <div style={S.emptyCard}>
        <div style={S.title}>No dataset found</div>
        <div style={S.desc}>
          Download the LiveDRBench dataset first, then the dashboard will pick it up automatically.
        </div>
        <code style={S.code}>
{`cd MiroFlow
uv run python -c "
  from utils.prepare_benchmark.gen_livedrbench \\
    import gen_livedrbench
  gen_livedrbench('data/livedrbench')
"`}
        </code>
        <div style={{ ...S.desc, marginBottom: '12px' }}>Or drop a JSON/JSONL file here:</div>
        <FileDropZone onFile={loadFile} />
        {error && <div style={{ color: color.error, fontSize: size.sm, marginTop: '12px' }}>{error}</div>}
      </div>
    )
  }

  return (
    <>
      <div style={S.loadedHeader}>
        <div>
          <div style={S.pageTitle}>{fileName}</div>
          <div style={S.meta}>{data.length} tasks</div>
        </div>
        <div style={S.headerRight}>
          {/* Dataset selector — if multiple datasets become available */}
          {available.map((ds) => (
            <button
              key={ds.name}
              style={S.dsBtn(fileName === ds.name)}
              onClick={() => switchDataset(ds)}
            >
              {ds.name}
            </button>
          ))}
          {/* Manual upload as fallback */}
          <label style={S.uploadBtn}>
            Upload
            <input
              type="file"
              accept=".json,.jsonl"
              style={{ display: 'none' }}
              onChange={(e) => e.target.files?.[0] && loadFile(e.target.files[0])}
            />
          </label>
        </div>
      </div>
      <StatBar data={data} />
      <TaskExplorer data={data} />
    </>
  )
}
