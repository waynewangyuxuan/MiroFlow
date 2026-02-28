import { useState } from 'react'
import { Activity, Loader, ArrowLeft, Upload, ChevronRight, Folder, FileText } from 'lucide-react'
import { color, size, font, radius } from '../styles/tokens'
import { useTraceLoader } from '../hooks/useTraceLoader'
import FileDropZone from '../components/FileDropZone'
import TraceOverview from '../components/TraceOverview'
import MessageTimeline from '../components/MessageTimeline'

// ─── Styles ──────────────────────────────────────────────────

const S = {
  header: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: '24px',
  },
  pageTitle: {
    fontSize: size.xl,
    fontWeight: 600,
    color: color.text,
    letterSpacing: '-0.03em',
  },
  backBtn: {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    padding: '5px 12px',
    borderRadius: radius.sm,
    border: `1px solid ${color.border}`,
    background: 'transparent',
    color: color.textMuted,
    fontSize: size.xs,
    fontWeight: 500,
    cursor: 'pointer',
    fontFamily: font.sans,
  },
  uploadBtn: {
    padding: '5px 12px',
    borderRadius: radius.sm,
    border: `1px solid ${color.border}`,
    background: 'transparent',
    color: color.textLight,
    fontSize: size.xs,
    cursor: 'pointer',
    fontFamily: font.sans,
    display: 'flex',
    alignItems: 'center',
    gap: '5px',
  },
  // Index view
  emptyCard: {
    background: color.surface,
    border: `1px solid ${color.border}`,
    borderRadius: radius.lg,
    padding: '32px',
    maxWidth: '560px',
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
  loading: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    padding: '40px 0',
    color: color.textLight,
    fontSize: size.sm,
  },
  // Benchmark index tree
  benchGroup: {
    marginBottom: '16px',
  },
  benchLabel: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    fontSize: size.sm,
    fontWeight: 600,
    color: color.text,
    padding: '6px 0',
    letterSpacing: '-0.01em',
  },
  configGroup: {
    marginLeft: '20px',
    marginBottom: '8px',
  },
  configLabel: {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    fontSize: size.sm,
    fontWeight: 500,
    color: color.textMuted,
    padding: '4px 0',
  },
  taskList: {
    marginLeft: '20px',
  },
  taskItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    padding: '5px 10px',
    borderRadius: radius.sm,
    cursor: 'pointer',
    fontSize: size.xs,
    fontFamily: font.mono,
    color: color.textMuted,
    transition: 'all 0.1s',
    border: '1px solid transparent',
  },
  taskItemHover: {
    background: `${color.accent}06`,
    border: `1px solid ${color.border}`,
    color: color.text,
  },
  // Trace detail
  taskMeta: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    marginBottom: '8px',
    flexWrap: 'wrap',
  },
  metaPill: (bg) => ({
    fontSize: '10px',
    fontWeight: 600,
    textTransform: 'uppercase',
    letterSpacing: '0.04em',
    color: '#fff',
    background: bg,
    padding: '2px 8px',
    borderRadius: '3px',
  }),
  metaText: {
    fontSize: size.xs,
    color: color.textLight,
    fontFamily: font.mono,
  },
  sectionDivider: {
    borderTop: `1px solid ${color.border}`,
    marginTop: '28px',
    paddingTop: '24px',
  },
  sectionTitle: {
    fontSize: size.md,
    fontWeight: 600,
    color: color.text,
    letterSpacing: '-0.02em',
    marginBottom: '16px',
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  taskDesc: {
    background: color.surfaceAlt,
    border: `1px solid ${color.border}`,
    borderRadius: radius.md,
    padding: '12px 16px',
    fontSize: size.sm,
    color: color.textMuted,
    lineHeight: 1.6,
    marginBottom: '24px',
    whiteSpace: 'pre-wrap',
  },
  answerBox: {
    background: color.surface,
    border: `1px solid ${color.border}`,
    borderRadius: radius.md,
    padding: '12px 16px',
    fontFamily: font.mono,
    fontSize: size.sm,
    color: color.text,
    lineHeight: 1.5,
    whiteSpace: 'pre-wrap',
    marginBottom: '16px',
  },
  answerLabel: {
    fontSize: size.xs,
    fontWeight: 600,
    color: color.textLight,
    textTransform: 'uppercase',
    letterSpacing: '0.04em',
    marginBottom: '6px',
  },
}

const STATUS_PILL_COLORS = {
  completed: color.success,
  running: color.sea,
  failed: color.error,
  interrupted: color.warning,
  pending: color.stone,
}

const RESULT_PILL_COLORS = {
  CORRECT: color.success,
  INCORRECT: color.error,
}

// ─── Index View ──────────────────────────────────────────────

function TraceIndex({ index, onSelect, onFile, error }) {
  const [hovered, setHovered] = useState(null)

  if (!index || index.length === 0) {
    return (
      <div style={S.emptyCard}>
        <div style={S.title}>No trace logs found</div>
        <div style={S.desc}>
          Run a benchmark task first, then the dashboard will discover logs automatically
          from the <code style={{ fontFamily: font.mono, fontSize: '12px' }}>logs/</code> directory.
        </div>
        <div style={{ ...S.desc, marginBottom: '12px' }}>Or drop a trace JSON file here:</div>
        <FileDropZone onFile={onFile} />
        {error && <div style={{ color: color.error, fontSize: size.sm, marginTop: '12px' }}>{error}</div>}
      </div>
    )
  }

  // Count total tasks
  const totalTasks = index.reduce((sum, b) => b.configs.reduce((s, c) => s + c.tasks.length, sum), 0)

  return (
    <div>
      <div style={S.header}>
        <div>
          <div style={S.pageTitle}>Trace Logs</div>
          <div style={{ fontSize: size.xs, color: color.textLight, marginTop: '4px' }}>
            {totalTasks} trace{totalTasks !== 1 ? 's' : ''} across {index.length} benchmark{index.length !== 1 ? 's' : ''}
          </div>
        </div>
        <label style={S.uploadBtn}>
          <Upload size={12} /> Upload
          <input
            type="file"
            accept=".json"
            style={{ display: 'none' }}
            onChange={(e) => e.target.files?.[0] && onFile(e.target.files[0])}
          />
        </label>
      </div>

      {index.map(bench => (
        <div key={bench.benchmark} style={S.benchGroup}>
          <div style={S.benchLabel}>
            <Folder size={14} strokeWidth={1.8} color={color.accent} />
            {bench.benchmark}
          </div>
          {bench.configs.map(cfg => (
            <div key={cfg.name} style={S.configGroup}>
              <div style={S.configLabel}>
                <Folder size={12} strokeWidth={1.5} color={color.textLight} />
                {cfg.name}
                <span style={{ fontSize: size.xs, color: color.textLight }}>({cfg.tasks.length})</span>
              </div>
              <div style={S.taskList}>
                {cfg.tasks.map(task => (
                  <div
                    key={task.id}
                    style={{
                      ...S.taskItem,
                      ...(hovered === task.id ? S.taskItemHover : {}),
                    }}
                    onMouseEnter={() => setHovered(task.id)}
                    onMouseLeave={() => setHovered(null)}
                    onClick={() => onSelect(task)}
                  >
                    <FileText size={11} strokeWidth={1.5} />
                    {task.name.replace('.json', '')}
                    <ChevronRight size={11} style={{ marginLeft: 'auto', opacity: hovered === task.id ? 1 : 0 }} />
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      ))}

      {error && <div style={{ color: color.error, fontSize: size.sm, marginTop: '12px' }}>{error}</div>}
    </div>
  )
}

// ─── Trace Detail View ───────────────────────────────────────

function TraceDetail({ trace, onBack }) {
  const taskDesc = trace.input?.task_description || ''
  const duration = (() => {
    const start = new Date(trace.start_time)
    const end = new Date(trace.end_time)
    const sec = Math.round((end - start) / 1000)
    if (sec < 60) return `${sec}s`
    const m = Math.floor(sec / 60)
    const s = sec % 60
    return s > 0 ? `${m}m ${s}s` : `${m}m`
  })()

  return (
    <div>
      {/* Header */}
      <div style={S.header}>
        <div>
          <div style={S.pageTitle}>{trace.task_name || trace.task_id}</div>
          <div style={S.taskMeta}>
            <span style={S.metaPill(STATUS_PILL_COLORS[trace.status] || color.stone)}>
              {trace.status}
            </span>
            {trace.judge_result && (
              <span style={S.metaPill(RESULT_PILL_COLORS[trace.judge_result] || color.stone)}>
                {trace.judge_result}
              </span>
            )}
            <span style={S.metaText}>{duration}</span>
            <span style={S.metaText}>
              {new Date(trace.start_time).toLocaleString('en-US', {
                month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
              })}
            </span>
            {trace.input?.metadata?.category && (
              <span style={S.metaText}>cat: {trace.input.metadata.category}</span>
            )}
          </div>
        </div>
        <button style={S.backBtn} onClick={onBack}>
          <ArrowLeft size={12} /> All traces
        </button>
      </div>

      {/* Task description */}
      {taskDesc && (
        <div style={S.taskDesc}>
          {taskDesc.length > 500 ? taskDesc.slice(0, 500) + '…' : taskDesc}
        </div>
      )}

      {/* Overview stats + charts */}
      <TraceOverview trace={trace} />

      {/* Answer section */}
      {trace.final_boxed_answer && (
        <div style={{ marginBottom: '8px' }}>
          <div style={S.answerLabel}>Final Answer</div>
          <div style={S.answerBox}>{trace.final_boxed_answer.trim()}</div>
        </div>
      )}

      {/* Message timeline */}
      <div style={S.sectionDivider}>
        <div style={S.sectionTitle}>
          <Activity size={16} strokeWidth={1.8} />
          Agent Execution
        </div>
        <MessageTimeline trace={trace} />
      </div>
    </div>
  )
}

// ─── Main Export ──────────────────────────────────────────────

export default function TraceLogs() {
  const { index, trace, loading, traceLoading, error, loadTrace, loadFile, clearTrace } = useTraceLoader()

  if (loading) {
    return (
      <div style={S.loading}>
        <Loader size={14} strokeWidth={1.5} style={{ animation: 'spin 1s linear infinite' }} />
        Discovering trace logs…
        <style>{`@keyframes spin { to { transform: rotate(360deg) } }`}</style>
      </div>
    )
  }

  if (traceLoading) {
    return (
      <div style={S.loading}>
        <Loader size={14} strokeWidth={1.5} style={{ animation: 'spin 1s linear infinite' }} />
        Loading trace…
        <style>{`@keyframes spin { to { transform: rotate(360deg) } }`}</style>
      </div>
    )
  }

  // Detail view
  if (trace) {
    return <TraceDetail trace={trace} onBack={clearTrace} />
  }

  // Index view
  return <TraceIndex index={index} onSelect={loadTrace} onFile={loadFile} error={error} />
}
