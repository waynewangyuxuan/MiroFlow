/**
 * Design tokens — Nordic minimalist palette.
 *
 * Inspired by Scandinavian interiors:
 *   - Large white/off-white surfaces
 *   - Muted accent colors from nature (stone, forest, sea)
 *   - Precise, functional typography
 */

export const color = {
  // Backgrounds
  bg:        '#FAFAF8',   // warm off-white
  surface:   '#FFFFFF',
  surfaceAlt:'#F4F3F0',   // light warm grey
  border:    '#E8E6E1',   // subtle border
  borderAlt: '#D5D2CB',

  // Text
  text:      '#1A1A1A',   // near-black
  textMuted: '#6B6860',   // warm grey
  textLight: '#9E9A90',   // lighter warm grey

  // Accents — restrained, from Nordic nature
  accent:    '#2D5A47',   // deep forest green
  accentAlt: '#3D7A5F',   // softer green
  sea:       '#3B6B8A',   // nordic sea blue
  stone:     '#8B8477',   // warm stone grey
  berry:     '#7A3E48',   // lingonberry
  amber:     '#B8860B',   // amber/honey
  moss:      '#6B7F5B',   // moss green
  slate:     '#5A6470',   // blue-grey slate

  // Functional
  error:     '#9B3B3B',
  success:   '#3B7A4A',
  warning:   '#B8860B',
}

export const font = {
  sans: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif",
  mono: "'JetBrains Mono', 'SF Mono', 'Fira Code', monospace",
}

export const size = {
  xs: '11px',
  sm: '12px',
  base: '14px',
  md: '15px',
  lg: '18px',
  xl: '24px',
  xxl: '32px',
}

export const space = {
  xs: '4px',
  sm: '8px',
  md: '16px',
  lg: '24px',
  xl: '32px',
  xxl: '48px',
}

export const radius = {
  sm: '4px',
  md: '6px',
  lg: '8px',
}

// Category colors — muted, nature-derived
export const categoryColor = {
  'entities':                         color.sea,
  'scifacts-geo':                     color.accent,
  'scifacts-materials':               color.slate,
  'prior-art':                        color.amber,
  'novel-datasets-identi-extraction': color.berry,
  'novel-datasets-identification':    color.moss,
  'novel-datasets-peer':              color.stone,
  'flights':                          color.accentAlt,
}

export function getCategoryColor(cat) {
  return categoryColor[cat] || color.textLight
}
