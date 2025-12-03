# 🎯 Git Fitness Dashboard

## Real-Time Commit Fitness Tracking While You Code!

Watch your commit fitness score update **live** as you write code. No more guessing when to commit!

## 🚀 Quick Start

```bash
# Run the dashboard
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 5001

# Or with poetry
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 5001
```

Then open: **http://localhost:5001**

## 📊 What You'll See

### Live Fitness Score (0.00 - 1.00)
- **0.70+** ✅ Ready to commit!
- **0.40-0.69** ⏳ Keep improving...
- **< 0.40** ❌ Needs work

### Component Breakdown
- **File Metrics** - Optimal number of files (2-5 is best)
- **Code Complexity** - Cyclomatic complexity analysis
- **Coherence** - Are changes related?
- **Test Coverage** - Do you have tests?
- **Risk Assessment** - Security patterns, breaking changes
- **Documentation** - Comments and docs ratio

### Real-Time Updates
- **WebSocket connection** for instant updates
- **File watcher** detects changes automatically
- **2-second debounce** to avoid constant recalculation
- **Beautiful animations** showing score changes

### 8-Dot Braille Display
Watch the Braille change based on your fitness:
- **⠑⠝⠓.⣯** - High fitness (0.8+)
- **⠥⠏⠙.⢑** - Medium fitness (0.6-0.8)
- **⠋⠊⠭.⠑** - Low fitness (0.4-0.6)

## 🎨 Features

### 1. **Live Progress Ring**
Visual representation of your fitness score with gradient colors

### 2. **Smart Suggestions**
- "Consider adding tests for these changes"
- "Add documentation or comments"
- "Split into smaller, more focused commits"

### 3. **Component Analysis**
See exactly which aspects of your changes need improvement

### 4. **Click to Refresh**
Click the score circle to manually trigger a fitness check

## 🔧 How It Works

1. **File Watcher** monitors all code changes
2. **Rust Analyzer** (`agit check`) calculates fitness
3. **WebSocket** broadcasts updates to dashboard
4. **Real-time UI** updates without refresh

## 📡 API Endpoints

- `GET /` - Dashboard UI
- `GET /api/fitness` - Current fitness JSON
- `POST /api/refresh` - Trigger manual update
- `WS /ws` - WebSocket for real-time updates

## 🎯 Optimal Coding Flow

1. **Start the dashboard** before coding
2. **Watch fitness rise** as you add coherent changes
3. **See it drop** if changes become scattered
4. **Commit at peak fitness** (0.70+)
5. **Follow suggestions** to improve score

## 🌈 Visual Indicators

- **Green pulse** - Live connection active
- **Purple gradient** - High fitness
- **Yellow warnings** - Suggestions available
- **Red status** - Error state

## 🚦 Status Messages

- ✅ **"Ready to commit!"** - Fitness ≥ 0.70
- ⏳ **"Keep improving..."** - Fitness < 0.70
- 🔄 **"No changes detected"** - Clean working directory
- ❌ **"Error"** - Issue with analyzer

## 🔮 Pro Tips

1. **Keep dashboard visible** on second monitor
2. **Commit when green** for best quality
3. **Follow suggestions** to improve fitness
4. **Small, focused changes** score higher
5. **Tests boost fitness** significantly

## 🤖 Integration with Autonomous Git

The dashboard uses the same fitness analyzer as the autonomous agent:
- Same scoring algorithm
- Same component analysis
- Same recommendations
- Just presented in real-time!

## 🎉 Result

**Vibe coding with confidence!** You'll always know:
- When to commit
- What needs improvement
- How coherent your changes are
- Whether you have enough tests

No more bad commits. No more guessing. Just **pure coding flow** with real-time fitness feedback!

---

*The future of version control: See your commit fitness live while you code!* 🚀
