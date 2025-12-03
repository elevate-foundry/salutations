# Autonomous Git - VS Code Extension

**Git that manages itself, right in your editor.**

## 🌟 Features

- **🤖 Autonomous Commits**: Agent watches your code and commits when fitness threshold is met
- **🔤 SCL (Semantic Compression Language)**: Commits in Braille, rendered in any language
- **📊 BIFM-64 Fitness Topology**: 3D fitness visualization (κ, σ, δ)
- **🧠 Neo4j Integration**: Store fitness in knowledge graph for swarm learning
- **🌍 Multi-Language**: English, Spanish, Chinese, Japanese, French, German
- **📈 Real-Time Fitness**: Live fitness score in status bar
- **📊 Graph Visualization**: View BIFM-64 graph in webview

## 🚀 Quick Start

1. Install the extension
2. Open a Git repository
3. Run command: `Autonomous Git: Start Agent`
4. Watch it commit autonomously!

## ⚙️ Configuration

```json
{
  "autonomousGit.enabled": true,
  "autonomousGit.threshold": 0.7,
  "autonomousGit.interval": 300,
  "autonomousGit.autoPush": false,
  "autonomousGit.sclEnabled": true,
  "autonomousGit.language": "en",
  "autonomousGit.neo4jUri": "bolt://localhost:7687",
  "autonomousGit.neo4jUser": "neo4j",
  "autonomousGit.neo4jPassword": "your-password"
}
```

## 📊 Status Bar

- **🤖 Autonomous Git**: Shows agent status (Active/Inactive)
- **📊 Fitness**: Shows current fitness score with color coding
  - Green (≥0.8): Ready to commit
  - Yellow (≥0.6): Approaching threshold
  - Red (<0.6): Not ready

## 🔤 SCL Mode

When enabled, commits are created in Semantic Compression Language:

```
🔤 ⠋⠊⠭.⠁⠥⠞⠓.⠑⠙⠛⠑.⣯
🌍 English translation: fix: authentication edge case
📊 κ=7 σ=5 δ=3 (maximum deformation, high volatility, critical)
```

## 🧠 Neo4j Integration

Connect to Neo4j to enable:
- **Pattern Recognition**: Learn from commit history
- **Swarm Intelligence**: Share knowledge across repos
- **Fitness Evolution**: Track fitness over time
- **Cross-Repo Learning**: Find similar patterns

## 📋 Commands

- `Autonomous Git: Start Agent` - Start autonomous commits
- `Autonomous Git: Stop Agent` - Stop the agent
- `Autonomous Git: Check Fitness` - Check current fitness
- `Autonomous Git: View BIFM Graph` - View fitness graph
- `Autonomous Git: Enable SCL Mode` - Enable semantic commits

## 🎯 Requirements

- Rust toolchain (for building `agit` binary)
- Neo4j database (optional, for graph features)
- Git repository

## 🔧 Building from Source

```bash
# Build the Rust binary
cd rust
cargo build --release

# Install extension dependencies
cd ../vscode-extension
npm install

# Compile TypeScript
npm run compile

# Package extension
npx vsce package
```

## 📖 Learn More

- [GitHub Repository](https://github.com/elevate-foundry/salutations)
- [Documentation](https://elevate-foundry.github.io/salutations/)
- [SCL + BIFM Guide](https://elevate-foundry.github.io/salutations/scl-bifm.html)

## 🤝 Contributing

Contributions welcome! See [CONTRIBUTING.md](../CONTRIBUTING.md)

## 📄 License

MIT License - see [LICENSE](../LICENSE)

---

**Built with 🤖 by [Elevate Foundry](https://github.com/elevate-foundry)**
