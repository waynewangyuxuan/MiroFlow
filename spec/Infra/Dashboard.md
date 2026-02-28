# Dashboard

> Internal web app for exploring benchmark data, viewing agent traces, and comparing experiment results.

## Stack

| Layer | Technology | Notes |
|-------|-----------|-------|
| Framework | React 19 | SPA with react-router-dom |
| Build | Vite 7 | Fast dev server, instant HMR |
| Charts | recharts | Trace analytics (area, bar, pie) |
| Icons | lucide-react | Consistent, minimal iconography |
| Styling | Inline JS objects | Token-based, no CSS framework |
| Design | Nordic minimalist | Inter + JetBrains Mono, muted earth tones, high whitespace |

## Quick Start

```bash
cd dashboard
npm install
npm run dev       # → http://localhost:5173
```

Production build:
```bash
npm run build     # outputs to dashboard/dist/
```

## Architecture

```
dashboard/
├── src/
│   ├── main.jsx              ← Entry point
│   ├── App.jsx               ← Router setup
│   ├── styles/
│   │   ├── tokens.js         ← Design tokens (colors, fonts, spacing)
│   │   └── global.css        ← Base reset + typography
│   ├── components/
│   │   ├── Layout.jsx        ← Shell: nav bar + content outlet
│   │   ├── FileDropZone.jsx  ← Drag-and-drop JSON loader
│   │   ├── StatBar.jsx       ← Overview stats strip
│   │   ├── TaskExplorer.jsx  ← Two-panel task list + detail
│   │   ├── TraceOverview.jsx ← Stats cards + recharts analytics
│   │   └── MessageTimeline.jsx ← Conversation timeline with tool calls
│   ├── views/
│   │   ├── BenchmarkData.jsx ← LiveDRBench data explorer
│   │   ├── TraceLogs.jsx     ← Agent trace viewer (fully implemented)
│   │   └── Experiments.jsx   ← Experiment comparison (placeholder)
│   ├── hooks/
│   │   ├── useDataLoader.js  ← File loading + parsing hook
│   │   └── useTraceLoader.js ← Trace log discovery + loading hook
│   └── utils/
│       └── data.js           ← Data extraction helpers
└── package.json
```

## Design System

Tokens are defined in `src/styles/tokens.js`. The palette is Nordic/Scandinavian-inspired:

- **Backgrounds**: warm off-white (`#FAFAF8`), clean white surfaces
- **Text**: near-black primary, warm grey secondary
- **Accents**: forest green, nordic sea blue, amber, lingonberry — used sparingly for categories
- **Typography**: Inter (UI), JetBrains Mono (code/data)
- **Spacing**: generous whitespace, restrained borders

Category colors map to `categoryColor` in tokens.js and are consistent across all views.

## Views

### Benchmark Data (current)
- Load `raw_data.json` or `standardized_data.jsonl` via drag-and-drop
- Stats overview: task count, category distribution, field count
- Two-panel explorer: searchable/filterable task list + full detail view

### Trace Logs (implemented)
- Auto-discovers traces from `logs/` directory via Vite middleware (`/api/logs/`)
- Tree-based index: benchmark → config → task files, with upload fallback
- **TraceOverview**: stat cards (duration, turns, tool calls, sub-agents, judge result) + recharts analytics (execution timeline area chart, tool usage bar chart, step status pie chart)
- **MessageTimeline**: vertical timeline with role-colored bubbles (SYS/AI/USR), collapsible content, XML tool-call parsing (`<use_mcp_tool>` → server/tool/args display), tool result blocks, sub-agent session expansion
- Step log table with status-colored dots and timestamps
- Task metadata pills (status, judge result, category, duration)

### Experiments (planned)
- Compare benchmark scores across models and configs
- Side-by-side task-level comparison (which tasks did model A solve that B didn't)
- Score trends over time

## Adding a New View

1. Create `src/views/MyView.jsx`
2. Add route in `src/App.jsx`
3. Add nav item in `src/components/Layout.jsx` (`navItems` array)
