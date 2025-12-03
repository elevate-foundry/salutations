# VS Code Extension - Autonomous Git

## 🎯 Overview

Aider-style VS Code extension that brings autonomous Git directly into your editor.

## ✨ Features

### 1. **Status Bar Integration**
- Live agent status (Active/Inactive)
- Real-time fitness score with color coding
- Click to start/stop or check fitness

### 2. **Command Palette**
```
Autonomous Git: Start Agent
Autonomous Git: Stop Agent
Autonomous Git: Check Fitness
Autonomous Git: View BIFM Graph
Autonomous Git: Enable SCL Mode
```

### 3. **Activity Bar Panel**
Custom sidebar with three views:
- **Agent Status**: Current state, threshold, interval
- **Fitness Topology**: Live κ, σ, δ visualization
- **Commit History**: Recent SCL commits with Braille

### 4. **Webview Panels**
- **Fitness Details**: Full breakdown with expert scores
- **BIFM Graph**: Interactive visualization of fitness evolution
- **Neo4j Browser**: Query and explore the knowledge graph

## 🔧 Architecture

```
VS Code Extension (TypeScript)
    ↓
  Spawns agit process
    ↓
  Parses stdout/stderr
    ↓
  Updates UI + Neo4j
    ↓
  Shows notifications
```

## 📊 UI Components

### Status Bar
```
[🤖 Autonomous Git: Active] [📊 Fitness: 0.87]
```

### Activity Bar
```
🤖 AUTONOMOUS GIT
├─ Agent Status
│  ├─ Status: Active
│  ├─ Threshold: 0.7
│  └─ Interval: 300s
├─ Fitness Topology
│  ├─ κ: 2 (slight change)
│  ├─ σ: 1 (stable)
│  └─ δ: 1 (positive drift)
└─ Commit History
   ├─ ⠥⠏⠙.⠙⠕⠉.⡁
   ├─ ⠋⠊⠭.⠁⠥⠞⠓.⣯
   └─ ⠁⠙⠙.⠞⠑⠎⠞.⠉
```

### Notifications
```
ℹ️ Autonomous Git agent started
✅ Committed: ⠥⠏⠙.⠙⠕⠉.⡁
⚠️ High volatility detected (σ=6)
❌ Critical fitness (δ=3) - Review recommended
```

## 🎨 Webview: Fitness Details

```html
┌─────────────────────────────────────┐
│ Fitness Details                     │
├─────────────────────────────────────┤
│                                     │
│ Overall Score: 0.87                 │
│                                     │
│ Expert Breakdown:                   │
│ ├─ Syntax:    0.92 ✓               │
│ ├─ Logic:     0.85 ✓               │
│ └─ Semantic:  0.84 ✓               │
│                                     │
│ BIFM-64 Topology:                   │
│ ⡁                                   │
│ κ=1 σ=0 δ=1                        │
│ (slight change, rock solid,         │
│  positive drift)                    │
│                                     │
│ Recommendation: ✅ Safe to commit   │
└─────────────────────────────────────┘
```

## 🧠 Webview: BIFM Graph

```html
┌─────────────────────────────────────┐
│ BIFM-64 Graph                       │
├─────────────────────────────────────┤
│                                     │
│ Fitness Evolution (Last 50)         │
│                                     │
│ ⡁ ⡉ ⡑ ⡙ ⡡ ⡩ ⡱ ⡹ ⣁ ⣉              │
│ │  │  │  │  │  │  │  │  │  │       │
│ └──┴──┴──┴──┴──┴──┴──┴──┴──┘       │
│                                     │
│ Recent Commits:                     │
│ ┌─────────────────────────────────┐ │
│ │ ⠥⠏⠙.⠙⠕⠉.⡁                      │ │
│ │ κ=1 σ=0 δ=1                    │ │
│ │ 2025-12-03 02:19:00            │ │
│ └─────────────────────────────────┘ │
│                                     │
│ [Query Neo4j] [Export Data]        │
└─────────────────────────────────────┘
```

## 🔌 Neo4j Integration

### Connection
```typescript
// Auto-connect on activation
const driver = neo4j.driver(
  config.neo4jUri,
  neo4j.auth.basic(config.neo4jUser, config.neo4jPassword)
);
```

### Store Commits
```typescript
// On each commit, store in graph
await session.run(`
  MERGE (f:FitnessTopology {braille: $braille})
  CREATE (c:Commit {scl: $scl, timestamp: datetime()})
  CREATE (c)-[:HAS_FITNESS]->(f)
  MERGE (r:Repo {name: $repo})
  CREATE (r)-[:CONTAINS]->(c)
`, { braille, scl, repo });
```

### Query Patterns
```typescript
// Find similar commits
const similar = await session.run(`
  MATCH (c:Commit)-[:HAS_FITNESS]->(f:FitnessTopology)
  WHERE f.kappa = $kappa AND f.sigma = $sigma
  RETURN c.scl, c.timestamp
  LIMIT 10
`, { kappa, sigma });
```

## 🚀 Installation

### From VSIX
```bash
code --install-extension autonomous-git-0.1.0.vsix
```

### From Source
```bash
cd vscode-extension
npm install
npm run compile
npx vsce package
code --install-extension autonomous-git-0.1.0.vsix
```

## 🎯 User Flow

### 1. First Time Setup
```
1. Install extension
2. Open Git repo
3. Extension prompts: "Build agit binary?"
4. User clicks "Yes"
5. Extension runs: cargo build --release
6. Extension shows: "Ready to use!"
```

### 2. Daily Usage
```
1. User opens repo
2. Extension auto-starts (if enabled)
3. Status bar shows: "🤖 Active"
4. Agent commits automatically
5. Notifications show SCL commits
6. User can view graph anytime
```

### 3. Configuration
```
1. User opens settings
2. Searches "Autonomous Git"
3. Adjusts threshold, interval, etc.
4. Changes apply immediately
```

## 🎨 Theming

Extension respects VS Code theme:
- Dark themes: Use cyan/purple accents
- Light themes: Use blue/violet accents
- High contrast: Use bold colors

## 🔔 Notifications

### Success
```
✅ Committed: ⠥⠏⠙.⠙⠕⠉.⡁
   Fitness: 0.87 (slight change, stable, positive)
```

### Warning
```
⚠️ High volatility detected
   σ=6 - Consider reviewing changes
   [View Details]
```

### Error
```
❌ Critical fitness topology
   δ=3 (divergent/critical)
   κ=7 σ=5 - Manual review required
   [View Diff] [Disable Agent]
```

## 🎯 Next Steps

1. **Publish to Marketplace**
   ```bash
   npx vsce publish
   ```

2. **Add Telemetry**
   - Track usage patterns
   - Improve fitness algorithms
   - Learn from community

3. **Add More Views**
   - Diff viewer with fitness overlay
   - Commit timeline
   - Cross-repo comparison

4. **Add Commands**
   - Manual commit with SCL
   - Fitness prediction
   - Pattern suggestions

## 🌟 The Vision

**Aider-style integration where the agent becomes part of your workflow.**

- No context switching
- Real-time feedback
- Seamless automation
- Beautiful visualizations

**This is the future of Git in VS Code.** 🚀
