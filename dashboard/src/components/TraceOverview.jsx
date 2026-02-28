import { useMemo } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend,
  AreaChart, Area,
} from 'recharts'
import { color, size, font, radius } from '../styles/tokens'
import { Clock, MessageSquare, Zap, CheckCircle, XCircle, AlertTriangle, Bot } from 'lucide-react'

const S = {
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
    gap: '12px',
    marginBottom: '24px',
  },
  statCard: {
    background: color.surface,
    border: `1px solid ${color.border}`,
    borderRadius: radius.lg,
    padding: '16px',
  },
  statLabel: {
    fontSize: size.xs,
    color: color.textLight,
    fontWeight: 500,
    textTransform: 'uppercase',
    letterSpacing: '0.04em',
    marginBottom: '6px',
  },
  statValue: {
    fontSize: size.xl,
    fontWeight: 600,
    color: color.text,
    letterSpacing: '-0.03em',
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  chartRow: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: '16px',
    marginBottom: '24px',
  },
  chartCard: {
    background: color.surface,
    border: `1px solid ${color.border}`,
    borderRadius: radius.lg,
    padding: '20px',
  },
  chartTitle: {
    fontSize: size.sm,
    fontWeight: 600,
    color: color.text,
    marginBottom: '16px',
    letterSpacing: '-0.01em',
  },
}

const STATUS_COLORS = {
  info: color.sea,
  success: color.success,
  warning: color.warning,
  failed: color.error,
  debug: color.stone,
}

const RESULT_COLORS = {
  CORRECT: color.success,
  INCORRECT: color.error,
  UNKNOWN: color.stone,
}

// eslint-disable-next-line no-unused-vars
function StatCard({ icon: Icon, label, value, iconColor }) {
  return (
    <div style={S.statCard}>
      <div style={S.statLabel}>{label}</div>
      <div style={S.statValue}>
        <Icon size={18} strokeWidth={1.6} color={iconColor || color.accent} />
        {value}
      </div>
    </div>
  )
}

/** Parse tool calls from assistant message content (XML-style <use_mcp_tool>) */
function extractToolCalls(content) {
  if (typeof content !== 'string') return []
  const regex = /<tool_name>(.*?)<\/tool_name>/gs
  const matches = []
  let m
  while ((m = regex.exec(content)) !== null) {
    matches.push(m[1].trim())
  }
  return matches
}

export default function TraceOverview({ trace }) {
  const stats = useMemo(() => {
    if (!trace) return null

    const msgs = trace.main_agent_message_history?.message_history || []
    const steps = trace.step_logs || []
    const subs = trace.sub_agent_message_history_sessions || {}

    // Duration
    const start = new Date(trace.start_time)
    const end = new Date(trace.end_time)
    const durationSec = Math.round((end - start) / 1000)

    // Count turns (assistant messages = turns)
    const assistantMsgs = msgs.filter(m => m.role === 'assistant')
    const mainTurns = assistantMsgs.length

    // Count tool calls
    const allToolCalls = []
    for (const m of assistantMsgs) {
      const content = typeof m.content === 'string' ? m.content : ''
      allToolCalls.push(...extractToolCalls(content))
    }

    // Sub-agent analysis
    const subSessions = Object.keys(subs)
    let subTurns = 0
    let subToolCalls = []
    for (const sid of subSessions) {
      const subMsgs = subs[sid]?.message_history || []
      const subAssistant = subMsgs.filter(m => m.role === 'assistant')
      subTurns += subAssistant.length
      for (const m of subAssistant) {
        const c = typeof m.content === 'string' ? m.content : ''
        subToolCalls.push(...extractToolCalls(c))
      }
    }

    // Step status breakdown
    const stepStatusCounts = {}
    for (const s of steps) {
      stepStatusCounts[s.status] = (stepStatusCounts[s.status] || 0) + 1
    }

    // Tool frequency map
    const toolFreq = {}
    for (const t of [...allToolCalls, ...subToolCalls]) {
      toolFreq[t] = (toolFreq[t] || 0) + 1
    }

    // Timeline data — step timestamps relative to start
    const timeline = steps.map((s, i) => ({
      index: i,
      name: s.step_name.replace(/_/g, ' '),
      time: Math.round((new Date(s.timestamp) - start) / 1000),
      status: s.status,
    }))

    return {
      durationSec,
      mainTurns,
      totalToolCalls: allToolCalls.length + subToolCalls.length,
      subSessions: subSessions.length,
      subTurns,
      judgeResult: trace.judge_result || 'UNKNOWN',
      status: trace.status,
      stepStatusCounts,
      toolFreq,
      timeline,
    }
  }, [trace])

  if (!stats) return null

  // Prepare chart data
  const stepStatusData = Object.entries(stats.stepStatusCounts).map(([name, value]) => ({
    name, value,
  }))

  const toolFreqData = Object.entries(stats.toolFreq)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 8)
    .map(([name, count]) => ({ name: name.length > 18 ? name.slice(0, 16) + '…' : name, count, fullName: name }))

  const formatDuration = (sec) => {
    if (sec < 60) return `${sec}s`
    const m = Math.floor(sec / 60)
    const s = sec % 60
    return s > 0 ? `${m}m ${s}s` : `${m}m`
  }

  return (
    <div>
      {/* Stat cards */}
      <div style={S.grid}>
        <StatCard icon={Clock} label="Duration" value={formatDuration(stats.durationSec)} iconColor={color.sea} />
        <StatCard icon={MessageSquare} label="Main Turns" value={stats.mainTurns} iconColor={color.accent} />
        <StatCard icon={Zap} label="Tool Calls" value={stats.totalToolCalls} iconColor={color.amber} />
        <StatCard icon={Bot} label="Sub-agents" value={stats.subSessions} iconColor={color.moss} />
        <StatCard
          icon={stats.judgeResult === 'CORRECT' ? CheckCircle : stats.judgeResult === 'INCORRECT' ? XCircle : AlertTriangle}
          label="Result"
          value={stats.judgeResult || stats.status}
          iconColor={RESULT_COLORS[stats.judgeResult] || color.stone}
        />
      </div>

      {/* Charts row */}
      <div style={S.chartRow}>
        {/* Step timeline */}
        <div style={S.chartCard}>
          <div style={S.chartTitle}>Execution Timeline</div>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={stats.timeline}>
              <defs>
                <linearGradient id="timeGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={color.sea} stopOpacity={0.15} />
                  <stop offset="95%" stopColor={color.sea} stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis
                dataKey="time"
                tick={{ fontSize: 10, fill: color.textLight }}
                tickFormatter={v => `${v}s`}
                axisLine={{ stroke: color.border }}
                tickLine={false}
              />
              <YAxis hide />
              <Tooltip
                contentStyle={{
                  background: color.surface,
                  border: `1px solid ${color.border}`,
                  borderRadius: radius.md,
                  fontSize: size.xs,
                  fontFamily: font.sans,
                }}
                formatter={(v, name, props) => [props.payload.name, 'Step']}
                labelFormatter={v => `${v}s elapsed`}
              />
              <Area
                type="stepAfter"
                dataKey="index"
                stroke={color.sea}
                strokeWidth={1.5}
                fill="url(#timeGrad)"
                dot={(props) => {
                  const s = stats.timeline[props.index]
                  if (!s) return null
                  return (
                    <circle
                      key={props.index}
                      cx={props.cx}
                      cy={props.cy}
                      r={3}
                      fill={STATUS_COLORS[s.status] || color.sea}
                      stroke="none"
                    />
                  )
                }}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Tool usage bar chart */}
        <div style={S.chartCard}>
          <div style={S.chartTitle}>Tool Usage</div>
          {toolFreqData.length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={toolFreqData} layout="vertical" margin={{ left: 10, right: 20 }}>
                <XAxis
                  type="number"
                  tick={{ fontSize: 10, fill: color.textLight }}
                  axisLine={{ stroke: color.border }}
                  tickLine={false}
                  allowDecimals={false}
                />
                <YAxis
                  type="category"
                  dataKey="name"
                  width={120}
                  tick={{ fontSize: 10, fill: color.textMuted, fontFamily: font.mono }}
                  axisLine={false}
                  tickLine={false}
                />
                <Tooltip
                  contentStyle={{
                    background: color.surface,
                    border: `1px solid ${color.border}`,
                    borderRadius: radius.md,
                    fontSize: size.xs,
                    fontFamily: font.sans,
                  }}
                  formatter={(v, name, props) => [v, props.payload.fullName]}
                />
                <Bar dataKey="count" fill={color.accent} radius={[0, 3, 3, 0]} barSize={14} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div style={{ fontSize: size.sm, color: color.textLight, padding: '40px 0', textAlign: 'center' }}>
              No tool calls recorded
            </div>
          )}
        </div>
      </div>

      {/* Step status breakdown (small pie) */}
      {stepStatusData.length > 1 && (
        <div style={{ ...S.chartCard, maxWidth: '320px', marginBottom: '24px' }}>
          <div style={S.chartTitle}>Step Status Breakdown</div>
          <ResponsiveContainer width="100%" height={160}>
            <PieChart>
              <Pie
                data={stepStatusData}
                cx="50%"
                cy="50%"
                innerRadius={35}
                outerRadius={55}
                paddingAngle={3}
                dataKey="value"
              >
                {stepStatusData.map((entry) => (
                  <Cell key={entry.name} fill={STATUS_COLORS[entry.name] || color.stone} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  background: color.surface,
                  border: `1px solid ${color.border}`,
                  borderRadius: radius.md,
                  fontSize: size.xs,
                }}
              />
              <Legend
                iconSize={8}
                wrapperStyle={{ fontSize: size.xs, fontFamily: font.sans }}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  )
}
