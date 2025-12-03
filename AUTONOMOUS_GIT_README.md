# Autonomous Git

**Git that manages itself using AI and fitness functions.**

## 🚀 Quick Start

### Rust (Production - Recommended)
```bash
cd rust
cargo build --release
./target/release/agit check
```

### Python (Prototype)
```bash
python examples/git_daemon.py --repo . --interval 300
```

## 📖 Documentation

- **[rust/README.md](rust/README.md)** - Rust implementation (single binary, fast, production-ready)
- **[AUTONOMOUS_GIT.md](AUTONOMOUS_GIT.md)** - Concept and philosophy
- **[GIT_DAEMON.md](GIT_DAEMON.md)** - Python daemon details
- **[Website](https://ryanbarrett.github.io/salutations/)** - Interactive demo and guide

## 🧬 Architecture

```
MetaBraider (Brain) → EntangledAgent (Body) → CommitFitness (Conscience)
```

That's it. Three components, one goal: **Make Git invisible.**

## 🎯 Usage

```bash
# Check if you should commit
agit check

# Run autonomous agent
agit run

# Install as system service
agit install
```

## 📊 How It Works

1. **Perceive**: Detect changes in your repo
2. **Calculate**: Fitness score (0-1) based on file count, tests, docs, coherence
3. **Decide**: Commit if fitness > 0.7
4. **Execute**: Auto-commit with AI-generated message

**You just write code. The agent handles Git.**

---

For detailed docs, see the files above. For quick start, just run `agit check`.
