import { useState, useCallback, useEffect } from 'react'

/**
 * Hook for discovering and loading trace log files.
 *
 * Walks /api/logs/ recursively to find *_attempt_*.json files,
 * groups them by benchmark/config, and loads selected traces.
 */
export function useTraceLoader() {
  const [index, setIndex] = useState(null)        // { benchmark, configs: [{ name, tasks }] }[]
  const [trace, setTrace] = useState(null)         // loaded trace JSON
  const [traceId, setTraceId] = useState('')       // "benchmark/config/filename"
  const [loading, setLoading] = useState(true)
  const [traceLoading, setTraceLoading] = useState(false)
  const [error, setError] = useState(null)

  // Discover log structure on mount
  useEffect(() => {
    let cancelled = false
    async function discover() {
      try {
        // List benchmarks
        const benchRes = await fetch('/api/logs/')
        if (!benchRes.ok) { setLoading(false); return }
        const benchmarks = await benchRes.json()
        const dirs = benchmarks.filter(e => e.type === 'dir')

        const result = []
        for (const bench of dirs) {
          // List configs under each benchmark
          const cfgRes = await fetch(`/api/logs/${bench.name}/`)
          if (!cfgRes.ok) continue
          const configs = (await cfgRes.json()).filter(e => e.type === 'dir')

          const cfgEntries = []
          for (const cfg of configs) {
            // List trace files under each config
            const taskRes = await fetch(`/api/logs/${bench.name}/${cfg.name}/`)
            if (!taskRes.ok) continue
            const files = (await taskRes.json())
              .filter(e => e.type === 'file' && e.name.endsWith('.json'))
              .map(e => ({
                name: e.name,
                path: `/api/logs/${bench.name}/${cfg.name}/${e.name}`,
                id: `${bench.name}/${cfg.name}/${e.name}`,
              }))
              .sort((a, b) => a.name.localeCompare(b.name, undefined, { numeric: true }))

            if (files.length > 0) {
              cfgEntries.push({ name: cfg.name, tasks: files })
            }
          }

          if (cfgEntries.length > 0) {
            result.push({ benchmark: bench.name, configs: cfgEntries })
          }
        }

        if (!cancelled) {
          setIndex(result)
          setLoading(false)
        }
      } catch (err) {
        if (!cancelled) {
          setError(`Failed to discover logs: ${err.message}`)
          setLoading(false)
        }
      }
    }
    discover()
    return () => { cancelled = true }
  }, [])

  const loadTrace = useCallback(async (taskEntry) => {
    setTraceLoading(true)
    setError(null)
    try {
      const res = await fetch(taskEntry.path)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      setTrace(data)
      setTraceId(taskEntry.id)
    } catch (err) {
      setError(`Failed to load trace: ${err.message}`)
    } finally {
      setTraceLoading(false)
    }
  }, [])

  const loadFile = useCallback((file) => {
    setError(null)
    setTraceLoading(true)
    const reader = new FileReader()
    reader.onload = (ev) => {
      try {
        const data = JSON.parse(ev.target.result)
        setTrace(data)
        setTraceId(file.name)
      } catch (err) {
        setError(`Failed to parse ${file.name}: ${err.message}`)
      } finally {
        setTraceLoading(false)
      }
    }
    reader.readAsText(file)
  }, [])

  const clearTrace = useCallback(() => {
    setTrace(null)
    setTraceId('')
  }, [])

  return { index, trace, traceId, loading, traceLoading, error, loadTrace, loadFile, clearTrace }
}
