import { getCategoryColor } from '../styles/tokens'

/**
 * Extract category from a data row (handles both raw and standardized formats).
 */
export function getCategory(row) {
  return row.category || row.metadata?.category || 'unknown'
}

/**
 * Extract the question/prompt text from a data row.
 */
export function getQuestion(row) {
  return row.question || row.Question || row.prompt || ''
}

/**
 * Extract task ID from a data row.
 */
export function getTaskId(row, index) {
  return row.task_id || row.id || String(index)
}

/**
 * Compute category distribution from dataset.
 */
export function getCategoryDistribution(data) {
  const dist = {}
  for (const row of data) {
    const cat = getCategory(row)
    dist[cat] = (dist[cat] || 0) + 1
  }
  return Object.entries(dist)
    .sort((a, b) => b[1] - a[1])
    .map(([name, count]) => ({ name, count, color: getCategoryColor(name) }))
}
