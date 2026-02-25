import { useState, useRef } from 'react'
import { Upload } from 'lucide-react'
import { color, radius } from '../styles/tokens'

const S = {
  zone: (active) => ({
    border: `1.5px dashed ${active ? color.accent : color.borderAlt}`,
    borderRadius: radius.lg,
    padding: '56px 32px',
    textAlign: 'center',
    cursor: 'pointer',
    transition: 'all 0.15s ease',
    background: active ? '#2D5A4706' : 'transparent',
  }),
  icon: {
    color: color.textLight,
    marginBottom: '12px',
  },
  title: {
    fontSize: '14px',
    fontWeight: 500,
    color: color.text,
    marginBottom: '6px',
  },
  hint: {
    fontSize: '12px',
    color: color.textLight,
  },
}

export default function FileDropZone({ onFile }) {
  const [dragging, setDragging] = useState(false)
  const inputRef = useRef()

  function handle(e) {
    e.preventDefault()
    setDragging(false)
    const file = e.dataTransfer?.files?.[0] || e.target?.files?.[0]
    if (file) onFile(file)
  }

  return (
    <div
      style={S.zone(dragging)}
      onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
      onDragLeave={() => setDragging(false)}
      onDrop={handle}
      onClick={() => inputRef.current?.click()}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".json,.jsonl"
        style={{ display: 'none' }}
        onChange={handle}
      />
      <Upload size={20} style={S.icon} strokeWidth={1.5} />
      <div style={S.title}>Drop raw_data.json here</div>
      <div style={S.hint}>or click to browse</div>
    </div>
  )
}
