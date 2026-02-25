# Dashboard

> Internal web app for exploring benchmark data, viewing agent traces, and comparing experiment results.

## Stack

| Layer | Technology | Notes |
|-------|-----------|-------|
| Framework | React 18 | SPA with react-router-dom |
| Build | Vite | Fast dev server, instant HMR |
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
│   │   └── TaskExplorer.jsx  ← Two-panel task list + detail
│   ├── views/
│   │   ├── BenchmarkData.jsx ← LiveDRBench data explorer
│   │   ├── TraceLogs.jsx     ← Agent trace viewer (placeholder)
│   │   └── Experiments.jsx   ← Experiment comparison (placeholder)
│   ├── hooks/
│   │   └── useDataLoader.js  ← File loading + parsing hook
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

### Trace Logs (planned)
- Load agent conversation traces from `logs/` directory
- Visualize: system prompt → LLM response → tool calls → tool results → next turn
- Show token usage, timing, context window pressure

### Experiments (planned)
- Compare benchmark scores across models and configs
- Side-by-side task-level comparison (which tasks did model A solve that B didn't)
- Score trends over time

## Adding a New View

1. Create `src/views/MyView.jsx`
2. Add route in `src/App.jsx`
3. Add nav item in `src/components/Layout.jsx` (`navItems` array)
