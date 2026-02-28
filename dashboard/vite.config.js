import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import fs from 'fs'
import path from 'path'

// Serve project-level /data and /logs as static files under /api/data and /api/logs
function serveProjectFiles() {
  const projectRoot = path.resolve(__dirname, '..')
  return {
    name: 'serve-project-files',
    configureServer(server) {
      server.middlewares.use((req, res, next) => {
        // Map /api/data/* → ../data/*
        if (req.url?.startsWith('/api/data/')) {
          const filePath = path.join(projectRoot, 'data', req.url.slice('/api/data/'.length))
          return serveFile(filePath, res, next)
        }
        // Map /api/logs/* → ../logs/*
        if (req.url?.startsWith('/api/logs/')) {
          const filePath = path.join(projectRoot, 'logs', req.url.slice('/api/logs/'.length))
          return serveFile(filePath, res, next)
        }
        next()
      })
    },
  }
}

function serveFile(filePath, res, next) {
  // Prevent directory traversal
  const resolved = path.resolve(filePath)
  try {
    if (!fs.existsSync(resolved)) {
      res.statusCode = 404
      res.end('Not found')
      return
    }
    // Directory listing support — returns JSON array of entries
    if (fs.statSync(resolved).isDirectory()) {
      const entries = fs.readdirSync(resolved, { withFileTypes: true }).map(e => ({
        name: e.name,
        type: e.isDirectory() ? 'dir' : 'file',
      }))
      res.setHeader('Content-Type', 'application/json')
      res.end(JSON.stringify(entries))
      return
    }
    const content = fs.readFileSync(resolved)
    const ext = path.extname(resolved)
    const mimeTypes = { '.json': 'application/json', '.jsonl': 'application/jsonl', '.txt': 'text/plain' }
    res.setHeader('Content-Type', mimeTypes[ext] || 'application/octet-stream')
    res.end(content)
  } catch {
    res.statusCode = 500
    res.end('Error reading file')
  }
}

export default defineConfig({
  plugins: [react(), serveProjectFiles()],
})
