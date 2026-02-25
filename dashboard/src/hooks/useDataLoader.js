import { useState, useCallback, useEffect } from 'react'

// Known datasets — served via /api/data/ middleware in vite.config.js
const KNOWN_DATASETS = [
  { name: 'LiveDRBench', path: '/api/data/livedrbench/raw_data.json' },
]

/**
 * Hook for loading benchmark data.
 * Auto-detects and loads available datasets on mount.
 * Falls back to manual file upload if nothing found.
 */
export function useDataLoader() {
  const [data, setData] = useState(null)
  const [fileName, setFileName] = useState('')
  const [error, setError] = useState(null)
  const [available, setAvailable] = useState([])
  const [loading, setLoading] = useState(true)

  // On mount: probe known paths, auto-load first found
  useEffect(() => {
    let cancelled = false
    async function probe() {
      const found = []
      for (const ds of KNOWN_DATASETS) {
        try {
          const res = await fetch(ds.path, { method: 'HEAD' })
          if (res.ok) found.push(ds)
        } catch {}
      }
      if (cancelled) return
      setAvailable(found)
      if (found.length > 0) {
        await loadFromPath(found[0])
      }
      setLoading(false)
    }
    probe()
    return () => { cancelled = true }
  }, [])

  async function loadFromPath(ds) {
    setError(null)
    try {
      const res = await fetch(ds.path)
      const text = await res.text()
      let parsed
      if (ds.path.endsWith('.jsonl')) {
        parsed = text.trim().split('\n').map(line => JSON.parse(line))
      } else {
        parsed = JSON.parse(text)
      }
      setData(Array.isArray(parsed) ? parsed : [parsed])
      setFileName(ds.name)
    } catch (err) {
      setError(`Failed to load ${ds.name}: ${err.message}`)
    }
  }

  const loadFile = useCallback((file) => {
    setError(null)
    const reader = new FileReader()
    reader.onload = (ev) => {
      try {
        const text = ev.target.result
        let parsed
        if (file.name.endsWith('.jsonl')) {
          parsed = text.trim().split('\n').map(line => JSON.parse(line))
        } else {
          parsed = JSON.parse(text)
        }
        setData(Array.isArray(parsed) ? parsed : [parsed])
        setFileName(file.name)
      } catch (err) {
        setError(`Failed to parse ${file.name}: ${err.message}`)
      }
    }
    reader.readAsText(file)
  }, [])

  const switchDataset = useCallback((ds) => {
    loadFromPath(ds)
  }, [])

  const reset = useCallback(() => {
    setData(null)
    setFileName('')
    setError(null)
  }, [])

  return { data, fileName, error, loading, available, loadFile, switchDataset, reset }
}
