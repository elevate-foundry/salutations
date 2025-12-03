# Git Daemon: Always-Running Autonomous Git

## What It Does

The Git Daemon runs continuously in the background and:
- ✅ Watches your repository for changes
- ✅ Automatically commits when fitness is high (>0.7)
- ✅ Restarts automatically if your machine restarts
- ✅ Logs all decisions
- ✅ Learns from your patterns

**You never think about Git again. Just write code.**

## Quick Start

### Install as System Service

```bash
# Install (runs on boot, restarts automatically)
python examples/git_daemon.py --install --repo /Users/ryanbarrett/salutations

# That's it! Daemon is now running.
```

### Manual Run (for testing)

```bash
# Run in foreground
python examples/git_daemon.py --repo . --interval 60

# Run with custom settings
python examples/git_daemon.py \
  --repo /path/to/repo \
  --interval 300 \
  --threshold 0.7
```

## How It Works

### The Loop

```
Every 5 minutes (configurable):
  1. Check for changes
  2. Calculate fitness score
  3. If fitness > 0.7:
     - Generate commit message
     - Commit automatically
     - Log decision
  4. Sleep and repeat
```

### Fitness Threshold

```python
# Default: 0.7 (70%)
# This means: Commit when changes are good quality

Fitness 0.9: Excellent - commits immediately
Fitness 0.7: Good - commits
Fitness 0.5: Okay - waits for more changes
Fitness 0.3: Poor - suggests improvements
```

## Installation Details

### What Gets Installed

```
~/Library/LaunchAgents/
  └── com.salutations.git-daemon.plist

Your Repo/.git/
  ├── daemon.log          # Activity log
  ├── daemon.error.log    # Error log
  └── daemon_stats.json   # Statistics
```

### LaunchAgent Configuration

The daemon:
- **Starts on boot** - Runs automatically when you login
- **Restarts on crash** - If it fails, macOS restarts it
- **Runs in background** - No terminal window needed
- **Logs everything** - Check `.git/daemon.log`

## Control Commands

```bash
# Start daemon
launchctl start com.salutations.git-daemon

# Stop daemon
launchctl stop com.salutations.git-daemon

# Restart daemon
launchctl restart com.salutations.git-daemon

# Check if running
launchctl list | grep git-daemon

# View logs
tail -f /path/to/repo/.git/daemon.log

# View stats
cat /path/to/repo/.git/daemon_stats.json
```

## Uninstall

```bash
# Remove service
python examples/git_daemon.py --uninstall

# Clean up logs (optional)
rm -rf .git/daemon*.log .git/daemon_stats.json
```

## Configuration

### Check Interval

How often to check for changes:

```bash
# Check every 1 minute (frequent commits)
--interval 60

# Check every 5 minutes (default, balanced)
--interval 300

# Check every 15 minutes (less frequent)
--interval 900
```

### Commit Threshold

Fitness score required to auto-commit:

```bash
# Aggressive (commits more often)
--threshold 0.5

# Balanced (default)
--threshold 0.7

# Conservative (only perfect commits)
--threshold 0.9
```

## Monitoring

### View Live Activity

```bash
# Watch daemon in real-time
tail -f .git/daemon.log
```

### Check Statistics

```bash
# View stats
cat .git/daemon_stats.json
```

Example output:
```json
{
  "started_at": "2025-12-02T20:00:00",
  "checks_performed": 48,
  "commits_made": 12,
  "last_check": "2025-12-02T22:00:00",
  "last_commit": "2025-12-02T21:45:00"
}
```

## Example Log Output

```
2025-12-02 20:05:00 | INFO | 🔍 CHECK #1
2025-12-02 20:05:00 | INFO |    Files changed: 3
2025-12-02 20:05:00 | INFO | 📊 Fitness: 0.85
2025-12-02 20:05:00 | SUCCESS | ✅ Fitness above threshold! Auto-committing...
2025-12-02 20:05:01 | SUCCESS | 🎉 Auto-commit #1 successful!
2025-12-02 20:05:01 | INFO | 💤 Sleeping for 300s...

2025-12-02 20:10:00 | INFO | 🔍 CHECK #2
2025-12-02 20:10:00 | INFO |    No changes detected
2025-12-02 20:10:00 | INFO | 💤 Sleeping for 300s...

2025-12-02 20:15:00 | INFO | 🔍 CHECK #3
2025-12-02 20:15:00 | INFO |    Files changed: 2
2025-12-02 20:15:00 | INFO | 📊 Fitness: 0.45
2025-12-02 20:15:00 | INFO | ⏳ Fitness below threshold (0.45 < 0.7)
2025-12-02 20:15:00 | INFO |    Waiting for more changes...
2025-12-02 20:15:00 | INFO | 💡 Suggestions:
2025-12-02 20:15:00 | INFO |    • Consider adding tests
2025-12-02 20:15:00 | INFO | 💤 Sleeping for 300s...
```

## Benefits

### Before Daemon

```
You: Write code
You: Remember to commit
You: Think about commit message
You: git add .
You: git commit -m "..."
You: Repeat every 30 minutes
```

**Time spent on Git**: 20% of your day

### With Daemon

```
You: Write code
Daemon: [watches silently]
Daemon: [commits when ready]
You: Keep coding
```

**Time spent on Git**: 0%

## Advanced Usage

### Multiple Repositories

Install daemon for each repo:

```bash
# Repo 1
python examples/git_daemon.py --install --repo ~/projects/repo1

# Repo 2
python examples/git_daemon.py --install --repo ~/projects/repo2
```

Each gets its own service:
- `com.salutations.git-daemon.repo1`
- `com.salutations.git-daemon.repo2`

### Custom Fitness Function

Modify `autonomous_git_agent.py` to customize fitness calculation:

```python
def calculate_commit_fitness(self, analysis):
    score = 0.0
    
    # Your custom rules
    if analysis["has_my_favorite_pattern"]:
        score += 0.5
    
    return CommitFitness(score=score, ...)
```

### Integration with CI/CD

Daemon commits → Triggers CI/CD automatically:

```yaml
# .github/workflows/on-commit.yml
on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - run: pytest
```

## Troubleshooting

### Daemon Not Starting

```bash
# Check if service is loaded
launchctl list | grep git-daemon

# Check logs
cat ~/Library/LaunchAgents/com.salutations.git-daemon.plist
tail -f .git/daemon.error.log
```

### Too Many Commits

```bash
# Increase threshold
launchctl unload ~/Library/LaunchAgents/com.salutations.git-daemon.plist
# Edit plist, change --threshold to 0.9
launchctl load ~/Library/LaunchAgents/com.salutations.git-daemon.plist
```

### Not Enough Commits

```bash
# Decrease threshold or interval
# Edit plist:
# --threshold 0.5
# --interval 60
```

### Daemon Crashed

```bash
# Check error log
cat .git/daemon.error.log

# Restart
launchctl restart com.salutations.git-daemon
```

## Security

### What the Daemon Can Do

- ✅ Read your code files
- ✅ Create git commits
- ✅ Write to `.git/` directory

### What It Cannot Do

- ❌ Push to remote (you control that)
- ❌ Delete files
- ❌ Modify your code
- ❌ Access network

### Privacy

- All processing is local
- No data sent anywhere
- Logs stay on your machine
- You can review all commits

## Performance

### Resource Usage

- **CPU**: <1% (only during checks)
- **Memory**: ~50MB
- **Disk**: Minimal (logs rotate daily)
- **Network**: None

### Impact on Development

- **Zero** - Runs in background
- Checks only every 5 minutes (configurable)
- Doesn't interfere with your work

## Philosophy

### Git Should Be Invisible

You don't think about:
- TCP/IP when browsing
- File systems when saving
- Memory management when coding

So why think about:
- When to commit?
- What to write in messages?
- How to structure branches?

**The daemon makes Git invisible.**

## Summary

```bash
# Install once
python examples/git_daemon.py --install --repo .

# Forget about Git forever
# Just write code
# Daemon handles everything
```

**Result:**
- ✅ Always-running Git intelligence
- ✅ Auto-commits when ready
- ✅ Restarts on reboot
- ✅ Learns your patterns
- ✅ Zero mental overhead

**Git becomes invisible. You just code.** 🚀
