import { useState, useMemo } from 'react'
import { color, size, font, radius } from '../styles/tokens'
import {
  User, Bot, Wrench, ChevronDown, ChevronRight,
  MessageSquare, Terminal, AlertCircle, Copy, Check,
  Layers,
} from 'lucide-react'

// ─── Styles ──────────────────────────────────────────────────

const S = {
  container: {
    position: 'relative',
  },
  // Vertical timeline rail
  rail: {
    position: 'absolute',
    left: '19px',
    top: '0',
    bottom: '0',
    width: '2px',
    background: color.border,
  },
  turn: {
    position: 'relative',
    paddingLeft: '48px',
    marginBottom: '4px',
  },
  dot: (roleColor) => ({
    position: 'absolute',
    left: '12px',
    top: '14px',
    width: '16px',
    height: '16px',
    borderRadius: '50%',
    background: roleColor,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 1,
  }),
  bubble: (isAssistant) => ({
    background: isAssistant ? color.surface : color.surfaceAlt,
    border: `1px solid ${color.border}`,
    borderRadius: radius.lg,
    padding: '12px 16px',
    cursor: 'pointer',
    transition: 'border-color 0.12s',
  }),
  bubbleHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    marginBottom: '4px',
  },
  roleTag: (bg) => ({
    fontSize: '10px',
    fontWeight: 600,
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
    color: '#fff',
    background: bg,
    padding: '1px 6px',
    borderRadius: '3px',
  }),
  turnNum: {
    fontSize: size.xs,
    color: color.textLight,
    fontFamily: font.mono,
  },
  preview: {
    fontSize: size.sm,
    color: color.textMuted,
    lineHeight: 1.5,
    whiteSpace: 'pre-wrap',
    wordBreak: 'break-word',
    maxHeight: '120px',
    overflow: 'hidden',
    position: 'relative',
  },
  expanded: {
    fontSize: size.sm,
    color: color.textMuted,
    lineHeight: 1.6,
    whiteSpace: 'pre-wrap',
    wordBreak: 'break-word',
    maxHeight: 'none',
    fontFamily: font.sans,
  },
  fade: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    height: '40px',
    background: 'linear-gradient(transparent, rgba(255,255,255,0.95))',
    pointerEvents: 'none',
  },
  fadeAlt: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    height: '40px',
    background: `linear-gradient(transparent, ${color.surfaceAlt}f2)`,
    pointerEvents: 'none',
  },
  toolCall: {
    margin: '8px 0 4px',
    background: `${color.amber}08`,
    border: `1px solid ${color.amber}30`,
    borderRadius: radius.md,
    padding: '8px 12px',
  },
  toolLabel: {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    fontSize: size.xs,
    fontWeight: 600,
    color: color.amber,
    marginBottom: '4px',
  },
  toolArgs: {
    fontSize: '11px',
    fontFamily: font.mono,
    color: color.textMuted,
    lineHeight: 1.4,
    maxHeight: '80px',
    overflow: 'hidden',
    whiteSpace: 'pre-wrap',
    wordBreak: 'break-all',
  },
  toolResult: {
    margin: '4px 0 8px',
    background: `${color.sea}06`,
    border: `1px solid ${color.sea}25`,
    borderRadius: radius.md,
    padding: '8px 12px',
    fontSize: '11px',
    fontFamily: font.mono,
    color: color.textMuted,
    lineHeight: 1.4,
    maxHeight: '120px',
    overflow: 'hidden',
    whiteSpace: 'pre-wrap',
    wordBreak: 'break-all',
    position: 'relative',
  },
  subAgentBanner: {
    margin: '16px 0 8px',
    marginLeft: '48px',
    background: `${color.moss}0A`,
    border: `1px solid ${color.moss}30`,
    borderRadius: radius.lg,
    padding: '12px 16px',
    cursor: 'pointer',
  },
  subAgentTitle: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    fontSize: size.sm,
    fontWeight: 600,
    color: color.moss,
  },
  subAgentMeta: {
    fontSize: size.xs,
    color: color.textLight,
    marginTop: '4px',
  },
  subAgentBody: {
    marginLeft: '64px',
    borderLeft: `2px solid ${color.moss}40`,
    paddingLeft: '16px',
    marginBottom: '12px',
  },
  copyBtn: {
    position: 'absolute',
    top: '8px',
    right: '8px',
    background: 'none',
    border: 'none',
    cursor: 'pointer',
    color: color.textLight,
    padding: '2px',
  },
  sectionTitle: {
    fontSize: size.sm,
    fontWeight: 600,
    color: color.text,
    marginBottom: '12px',
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  tabRow: {
    display: 'flex',
    gap: '4px',
    marginBottom: '16px',
  },
  tab: (active) => ({
    padding: '5px 12px',
    borderRadius: radius.sm,
    border: `1px solid ${active ? color.accent : color.border}`,
    background: active ? `${color.accent}0A` : 'transparent',
    color: active ? color.accent : color.textMuted,
    fontSize: size.xs,
    fontWeight: 500,
    cursor: 'pointer',
    fontFamily: font.sans,
    display: 'flex',
    alignItems: 'center',
    gap: '5px',
  }),
}

// ─── Helpers ──────────────────────────────────────────────────

function extractTextContent(content) {
  if (typeof content === 'string') return content
  if (Array.isArray(content)) {
    return content
      .filter(c => c.type === 'text')
      .map(c => c.text)
      .join('\n')
  }
  return JSON.stringify(content)
}

function parseToolCall(text) {
  const serverMatch = text.match(/<server_name>([\s\S]*?)<\/server_name>/)
  const toolMatch = text.match(/<tool_name>([\s\S]*?)<\/tool_name>/)
  const argsMatch = text.match(/<arguments>([\s\S]*?)<\/arguments>/)
  if (!toolMatch) return null
  return {
    server: serverMatch ? serverMatch[1].trim() : '',
    tool: toolMatch[1].trim(),
    args: argsMatch ? argsMatch[1].trim() : '',
  }
}

function splitAssistantContent(text) {
  // Split into reasoning + tool call
  const toolIdx = text.indexOf('<use_mcp_tool>')
  if (toolIdx === -1) return { reasoning: text, toolCall: null }
  return {
    reasoning: text.slice(0, toolIdx).trim(),
    toolCall: parseToolCall(text.slice(toolIdx)),
  }
}

// ─── Copy Button ──────────────────────────────────────────────

function CopyButton({ text }) {
  const [copied, setCopied] = useState(false)
  const handleCopy = (e) => {
    e.stopPropagation()
    navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }
  return (
    <button style={S.copyBtn} onClick={handleCopy} title="Copy">
      {copied ? <Check size={12} /> : <Copy size={12} />}
    </button>
  )
}

// ─── Single Message Bubble ───────────────────────────────────

function MessageBubble({ msg, turnNumber }) {
  const [expanded, setExpanded] = useState(false)
  const isAssistant = msg.role === 'assistant'
  const isSystem = msg.role === 'system'
  const text = extractTextContent(msg.content)

  const roleColor = isSystem ? color.stone : isAssistant ? color.accent : color.sea
  const roleLabel = isSystem ? 'SYS' : isAssistant ? 'AI' : 'USR'
  const RoleIcon = isSystem ? Terminal : isAssistant ? Bot : User

  // Parse tool call from assistant messages
  const { reasoning, toolCall } = isAssistant ? splitAssistantContent(text) : { reasoning: text, toolCall: null }

  // For user messages that are tool results, detect them
  const isToolResult = !isAssistant && !isSystem && text.startsWith('[')

  const displayText = reasoning || text
  const isLong = displayText.length > 300

  return (
    <div style={S.turn}>
      <div style={S.dot(roleColor)}>
        <RoleIcon size={10} color="#fff" strokeWidth={2.5} />
      </div>
      <div
        style={S.bubble(isAssistant)}
        onClick={() => setExpanded(!expanded)}
      >
        <div style={S.bubbleHeader}>
          <span style={S.roleTag(roleColor)}>{roleLabel}</span>
          {turnNumber != null && <span style={S.turnNum}>Turn {turnNumber}</span>}
          {isToolResult && (
            <span style={{ ...S.roleTag(color.sea), fontSize: '9px' }}>TOOL RESULT</span>
          )}
          <span style={{ marginLeft: 'auto', color: color.textLight }}>
            {expanded ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
          </span>
        </div>

        {/* Message body */}
        <div style={{ position: 'relative' }}>
          <div style={expanded ? S.expanded : S.preview}>
            {displayText}
          </div>
          {!expanded && isLong && (
            <div style={isAssistant ? S.fade : S.fadeAlt} />
          )}
        </div>

        {/* Tool call block */}
        {toolCall && (
          <div style={S.toolCall}>
            <div style={S.toolLabel}>
              <Wrench size={11} />
              {toolCall.server && <span style={{ fontWeight: 400, color: color.textLight }}>{toolCall.server} /</span>}
              {toolCall.tool}
            </div>
            {toolCall.args && (
              <div style={S.toolArgs}>
                {toolCall.args.length > 200 && !expanded
                  ? toolCall.args.slice(0, 200) + '…'
                  : toolCall.args}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

// ─── Sub-Agent Session ───────────────────────────────────────

function SubAgentSession({ sessionId, session }) {
  const [expanded, setExpanded] = useState(false)
  const msgs = session?.message_history || []
  const assistantCount = msgs.filter(m => m.role === 'assistant').length

  return (
    <>
      <div style={S.subAgentBanner} onClick={() => setExpanded(!expanded)}>
        <div style={S.subAgentTitle}>
          <Layers size={14} />
          Sub-Agent: {sessionId}
          <span style={{ marginLeft: 'auto' }}>
            {expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
          </span>
        </div>
        <div style={S.subAgentMeta}>
          {assistantCount} turns · {msgs.length} messages
        </div>
      </div>
      {expanded && (
        <div style={S.subAgentBody}>
          {msgs.filter(m => m.role !== 'system').map((m, i) => (
            <MessageBubble key={i} msg={m} index={i} turnNumber={m.role === 'assistant' ? Math.ceil((i) / 2) : null} />
          ))}
        </div>
      )}
    </>
  )
}

// ─── Step Log List ───────────────────────────────────────────

function StepLogList({ steps }) {
  if (!steps || steps.length === 0) return null

  const statusDot = (status) => ({
    width: '7px',
    height: '7px',
    borderRadius: '50%',
    background: STATUS_COLORS[status] || color.stone,
    flexShrink: 0,
  })

  const STATUS_COLORS = {
    info: color.sea,
    success: color.success,
    warning: color.warning,
    failed: color.error,
    debug: color.stone,
  }

  return (
    <div style={{
      background: color.surface,
      border: `1px solid ${color.border}`,
      borderRadius: radius.lg,
      overflow: 'hidden',
    }}>
      {steps.map((s, i) => (
        <div
          key={i}
          style={{
            display: 'flex',
            alignItems: 'flex-start',
            gap: '10px',
            padding: '8px 14px',
            borderBottom: i < steps.length - 1 ? `1px solid ${color.border}` : 'none',
            fontSize: size.xs,
          }}
        >
          <div style={{ ...statusDot(s.status), marginTop: '5px' }} />
          <div style={{ minWidth: '60px', color: color.textLight, fontFamily: font.mono, flexShrink: 0 }}>
            {new Date(s.timestamp).toLocaleTimeString('en-US', { hour12: false })}
          </div>
          <div style={{
            color: color.textMuted,
            fontFamily: font.mono,
            fontWeight: 500,
            minWidth: '180px',
            flexShrink: 0,
          }}>
            {s.step_name}
          </div>
          <div style={{ color: color.textLight, flex: 1, lineHeight: 1.4, wordBreak: 'break-word' }}>
            {s.message.length > 200 ? s.message.slice(0, 200) + '…' : s.message}
          </div>
        </div>
      ))}
    </div>
  )
}

// ─── Main Export ──────────────────────────────────────────────

export default function MessageTimeline({ trace }) {
  const [view, setView] = useState('messages')  // 'messages' | 'steps'

  const { mainMessages, subSessions } = useMemo(() => {
    if (!trace) return { mainMessages: [], subSessions: {} }
    const msgs = trace.main_agent_message_history?.message_history || []
    const subs = trace.sub_agent_message_history_sessions || {}
    return { mainMessages: msgs, subSessions: subs }
  }, [trace])

  // Compute turn numbers for assistant messages
  const messagesWithTurns = useMemo(() => {
    let turn = 0
    return mainMessages.map(m => {
      if (m.role === 'assistant') {
        turn++
        return { ...m, turnNumber: turn }
      }
      return { ...m, turnNumber: null }
    })
  }, [mainMessages])

  const subSessionEntries = Object.entries(subSessions)
  const stepLogs = useMemo(() => trace?.step_logs || [], [trace])

  // Build interleaved timeline: inject sub-agent sessions after the step that started them
  const interleavedTimeline = useMemo(() => {
    if (subSessionEntries.length === 0) {
      // No sub-agents, just show messages
      return messagesWithTurns
        .filter(m => m.role !== 'system')
        .map((m, i) => ({ type: 'message', data: m, key: `msg-${i}` }))
    }

    // Build: messages + sub-agent banners interleaved
    const items = []
    const nonSystemMsgs = messagesWithTurns.filter(m => m.role !== 'system')

    // Map sub-agent sessions to approximate insertion points
    const subInsertAfter = {}
    for (const [sid] of subSessionEntries) {
      // Find the step_log that starts this session
      const startStep = stepLogs.find(s => s.step_name.includes('session_start') && s.metadata?.session_id === sid)
      if (startStep) {
        // Insert after last main message (approximate position)
        const insertIdx = nonSystemMsgs.length - 1
        subInsertAfter[insertIdx] = subInsertAfter[insertIdx] || []
        subInsertAfter[insertIdx].push(sid)
      } else {
        // Fallback: insert at end
        const lastIdx = nonSystemMsgs.length - 1
        subInsertAfter[lastIdx] = subInsertAfter[lastIdx] || []
        subInsertAfter[lastIdx].push(sid)
      }
    }

    for (let i = 0; i < nonSystemMsgs.length; i++) {
      items.push({ type: 'message', data: nonSystemMsgs[i], key: `msg-${i}` })
      if (subInsertAfter[i]) {
        for (const sid of subInsertAfter[i]) {
          items.push({ type: 'subagent', sessionId: sid, data: subSessions[sid], key: `sub-${sid}` })
        }
      }
    }

    return items
  }, [messagesWithTurns, subSessionEntries, stepLogs, subSessions])

  return (
    <div>
      {/* Tab selector */}
      <div style={S.tabRow}>
        <button style={S.tab(view === 'messages')} onClick={() => setView('messages')}>
          <MessageSquare size={12} /> Messages ({mainMessages.filter(m => m.role !== 'system').length})
        </button>
        <button style={S.tab(view === 'steps')} onClick={() => setView('steps')}>
          <Terminal size={12} /> Step Logs ({stepLogs.length})
        </button>
        {subSessionEntries.length > 0 && (
          <div style={{ fontSize: size.xs, color: color.moss, display: 'flex', alignItems: 'center', gap: '4px', marginLeft: '8px' }}>
            <Layers size={11} /> {subSessionEntries.length} sub-agent session{subSessionEntries.length > 1 ? 's' : ''}
          </div>
        )}
      </div>

      {/* Message timeline */}
      {view === 'messages' && (
        <div style={S.container}>
          <div style={S.rail} />
          {interleavedTimeline.map(item => {
            if (item.type === 'message') {
              return <MessageBubble key={item.key} msg={item.data} turnNumber={item.data.turnNumber} />
            }
            if (item.type === 'subagent') {
              return <SubAgentSession key={item.key} sessionId={item.sessionId} session={item.data} />
            }
            return null
          })}
        </div>
      )}

      {/* Step logs */}
      {view === 'steps' && <StepLogList steps={stepLogs} />}
    </div>
  )
}
