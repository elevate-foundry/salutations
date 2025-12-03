"""
Self-Publishing Agent: An agent that can publish itself to GitHub.

This agent can:
1. Initialize a git repository
2. Create a GitHub repository (via API)
3. Commit all code
4. Push to GitHub
5. Make it public
6. Generate README and documentation
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from typing import Optional, Dict, Any
import requests

sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger


class SelfPublishingAgent:
    """
    An agent that can publish itself to GitHub autonomously.
    """
    
    def __init__(self, project_root: Path, github_token: Optional[str] = None):
        """
        Initialize the self-publishing agent.
        
        Args:
            project_root: Root directory of the project
            github_token: GitHub personal access token (or will read from env)
        """
        self.project_root = project_root
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        self.github_api = "https://api.github.com"
        
        logger.info("📦 Self-Publishing Agent initialized")
        logger.info(f"   Project root: {project_root}")
    
    def check_git_installed(self) -> bool:
        """Check if git is installed."""
        try:
            result = subprocess.run(
                ["git", "--version"],
                capture_output=True,
                text=True,
            )
            logger.info(f"   ✓ Git installed: {result.stdout.strip()}")
            return True
        except FileNotFoundError:
            logger.error("   ❌ Git not installed")
            return False
    
    def check_gh_installed(self) -> bool:
        """Check if GitHub CLI is installed."""
        try:
            result = subprocess.run(
                ["gh", "--version"],
                capture_output=True,
                text=True,
            )
            logger.info(f"   ✓ GitHub CLI installed: {result.stdout.strip().split()[0]}")
            return True
        except FileNotFoundError:
            logger.error("   ❌ GitHub CLI not installed")
            logger.info("   Install with: brew install gh")
            return False
    
    def check_gh_auth(self) -> bool:
        """Check if GitHub CLI is authenticated."""
        try:
            result = subprocess.run(
                ["gh", "auth", "status"],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                logger.info("   ✓ GitHub CLI authenticated")
                return True
            else:
                logger.warning("   ⚠️  GitHub CLI not authenticated")
                logger.info("   Run: gh auth login")
                return False
        except Exception as e:
            logger.error(f"   ❌ Error checking auth: {e}")
            return False
    
    def init_git_repo(self) -> bool:
        """Initialize git repository if not already initialized."""
        logger.info("\n🔧 Initializing git repository...")
        
        git_dir = self.project_root / ".git"
        
        if git_dir.exists():
            logger.info("   ✓ Git repository already initialized")
            return True
        
        try:
            subprocess.run(
                ["git", "init"],
                cwd=self.project_root,
                check=True,
                capture_output=True,
            )
            logger.success("   ✓ Git repository initialized")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"   ❌ Failed to initialize git: {e}")
            return False
    
    def create_gitignore(self):
        """Create or update .gitignore file."""
        logger.info("\n📝 Creating .gitignore...")
        
        gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
.venv

# IDE
.vscode/
.idea/
*.swp

# Environment
.env
.env.local
*.env.backup

# Logs
logs/
*.log

# Model checkpoints
checkpoints/
*.pt
*.pth

# Data
data/
evidence/

# OS
.DS_Store
Thumbs.db

# Node
node_modules/
mcp/dist/

# Neo4j
neo4j_data/
"""
        
        gitignore_path = self.project_root / ".gitignore"
        gitignore_path.write_text(gitignore_content)
        logger.success(f"   ✓ Created {gitignore_path}")
    
    def generate_readme(self) -> str:
        """Generate a comprehensive README for the project."""
        logger.info("\n📄 Generating README...")
        
        readme_content = """# Salutations - Multi-LLM Braiding System

An autonomous AI system that learns to braid multiple LLMs together with search capabilities and graph-based memory.

## 🌟 Features

- **Multi-LLM Braiding** - Combine multiple models with full hidden layer access
- **Meta-Learning Agent** - AI that learns to braid LLMs automatically
- **Self-Bootstrapping** - Agent can configure and run itself
- **Playwright MCP** - Web automation and search
- **Neo4j Memory** - Graph-based memory with semantic search
- **SOC 2 Automation** - Generate compliance evidence automatically

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/salutations.git
cd salutations

# Run setup
chmod +x scripts/setup.sh
./scripts/setup.sh

# Activate environment
source venv/bin/activate

# Try the meta-braiding demo
python examples/show_meta_braiding.py
```

## 🧠 What is Braiding?

Braiding combines multiple LLMs by fusing their hidden layer representations:

```
Model A → [Layer 0, Layer 4, Layer 8, ...]
Model B → [Layer 0, Layer 4, Layer 8, ...]
Model C → [Layer 0, Layer 4, Layer 8, ...]
    ↓         ↓         ↓
  Fusion    Fusion    Fusion
    ↓         ↓         ↓
Combined knowledge from all models
```

## 🤖 Meta-Learning

The agent learns to braid automatically:

```python
from models.meta_braider import MetaBraider

# Agent decides how to braid for any task
meta_braider = MetaBraider(model_pool)
decision = meta_braider.forward(task)
braided = meta_braider.create_braided_model(decision)

# Agent learns from feedback
meta_braider.learn_from_feedback(task, decision, performance)
```

## 📚 Documentation

- [QUICKSTART.md](QUICKSTART.md) - Get started quickly
- [BRAIDING_GUIDE.md](BRAIDING_GUIDE.md) - Complete braiding guide
- [META_BRAIDING.md](META_BRAIDING.md) - Meta-learning approach
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture
- [CHEATSHEET.md](CHEATSHEET.md) - Quick reference

## 🎯 Use Cases

### 1. Multi-Domain Expert System
Combine specialized models (code, medical, legal) and let the agent route dynamically.

### 2. SOC 2 Compliance Automation
Generate audit evidence automatically with web automation.

### 3. Self-Improving Assistant
Agent learns from user feedback and continuously improves.

## 🛠️ Architecture

```
┌─────────────────────────────────────────┐
│         Meta-Braider Agent              │
│  (Learns optimal braiding strategies)   │
└────────────────┬────────────────────────┘
                 ↓
┌─────────────────────────────────────────┐
│         Braided LLM System              │
│  Model A + Model B + Model C            │
└────────────────┬────────────────────────┘
                 ↓
        ┌────────┼────────┐
        ↓        ↓        ↓
    ┌──────┐ ┌──────┐ ┌──────┐
    │ MCP  │ │Neo4j │ │Tools │
    └──────┘ └──────┘ └──────┘
```

## 🔧 Components

- **models/** - LLM wrappers, braiding, fusion strategies, meta-learner
- **memory/** - Neo4j integration, semantic search
- **mcp/** - Playwright MCP server for web automation
- **orchestration/** - Coordinator that ties everything together
- **tools/** - Tool execution layer
- **examples/** - Demos and tutorials

## 📖 Examples

### Basic Braiding
```python
from models import BraidedLLM

braided = BraidedLLM(
    model_configs=[
        {"model_name": "llama-3.1-8B", "role": "reasoning"},
        {"model_name": "codellama-7b", "role": "code"},
    ],
    fusion_strategy="learned_weighted",
)

response = braided.generate("Write a sorting algorithm")
```

### Self-Bootstrapping
```python
from examples.self_bootstrapping_agent import SelfBootstrappingAgent

agent = SelfBootstrappingAgent(project_root)
agent.bootstrap_and_run(task)  # Agent sets itself up and runs!
```

### SOC 2 Evidence Generation
```python
# Agent automatically:
# 1. Analyzes compliance requirements
# 2. Generates automation code
# 3. Captures evidence screenshots
# 4. Verifies controls worked
```

## 🎓 Learning Resources

- **Interactive Tutorial**: `python examples/braiding_tutorial.py`
- **Meta-Braiding Demo**: `python examples/show_meta_braiding.py`
- **Self-Bootstrapping**: `python examples/self_bootstrapping_agent.py`

## 🤝 Contributing

This is an autonomous system that improves itself! Contributions welcome.

## 📄 License

MIT

## 🌟 Key Innovation

**An AI agent that teaches itself to braid LLMs!**

The meta-braider observes tasks, tries different braiding strategies, learns from results, and continuously improves. No manual configuration needed - the agent figures it out.

---

Built with ❤️ by autonomous AI agents
"""
        
        readme_path = self.project_root / "README_GENERATED.md"
        readme_path.write_text(readme_content)
        logger.success(f"   ✓ Generated {readme_path}")
        
        return readme_content
    
    def stage_files(self):
        """Stage all files for commit."""
        logger.info("\n📦 Staging files...")
        
        try:
            # Add all files
            subprocess.run(
                ["git", "add", "."],
                cwd=self.project_root,
                check=True,
                capture_output=True,
            )
            
            # Check what's staged
            result = subprocess.run(
                ["git", "status", "--short"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
            )
            
            files = result.stdout.strip().split("\n")
            logger.info(f"   ✓ Staged {len(files)} files")
            
            # Show first few files
            for file in files[:5]:
                logger.info(f"      {file}")
            if len(files) > 5:
                logger.info(f"      ... and {len(files) - 5} more")
            
        except subprocess.CalledProcessError as e:
            logger.error(f"   ❌ Failed to stage files: {e}")
    
    def commit_changes(self, message: str = "Initial commit by Self-Publishing Agent"):
        """Commit staged changes."""
        logger.info("\n💾 Committing changes...")
        
        try:
            subprocess.run(
                ["git", "commit", "-m", message],
                cwd=self.project_root,
                check=True,
                capture_output=True,
            )
            logger.success(f"   ✓ Committed: {message}")
        except subprocess.CalledProcessError as e:
            if "nothing to commit" in str(e.stderr):
                logger.info("   ℹ️  Nothing to commit")
            else:
                logger.error(f"   ❌ Failed to commit: {e}")
    
    def create_github_repo_with_gh(
        self,
        repo_name: str,
        description: str,
        private: bool = True,
    ) -> Optional[str]:
        """
        Create a GitHub repository using GitHub CLI.
        
        Args:
            repo_name: Name of the repository
            description: Repository description
            private: Whether the repo should be private (default: True)
        
        Returns:
            Repository URL if successful, None otherwise
        """
        logger.info(f"\n🐙 Creating GitHub repository: {repo_name}")
        logger.info(f"   Privacy: {'Private' if private else 'Public'}")
        
        visibility = "--private" if private else "--public"
        
        try:
            # Create repo with gh CLI
            result = subprocess.run(
                [
                    "gh", "repo", "create", repo_name,
                    visibility,
                    "--description", description,
                    "--source", str(self.project_root),
                    "--push",
                ],
                cwd=self.project_root,
                capture_output=True,
                text=True,
            )
            
            if result.returncode == 0:
                logger.success("   ✓ Repository created and pushed!")
                
                # Get repo URL
                url_result = subprocess.run(
                    ["gh", "repo", "view", "--json", "url", "-q", ".url"],
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                )
                
                if url_result.returncode == 0:
                    repo_url = url_result.stdout.strip()
                    logger.info(f"   URL: {repo_url}")
                    return repo_url
                
                return f"https://github.com/{repo_name}"
            
            else:
                error_msg = result.stderr.strip()
                if "already exists" in error_msg.lower():
                    logger.warning("   ⚠️  Repository already exists")
                    # Try to get existing repo URL
                    url_result = subprocess.run(
                        ["gh", "repo", "view", repo_name, "--json", "url", "-q", ".url"],
                        capture_output=True,
                        text=True,
                    )
                    if url_result.returncode == 0:
                        return url_result.stdout.strip()
                else:
                    logger.error(f"   ❌ Failed to create repo")
                    logger.error(f"   {error_msg}")
                return None
        
        except Exception as e:
            logger.error(f"   ❌ Error creating repo: {e}")
            return None
    
    def get_github_username(self) -> Optional[str]:
        """Get GitHub username from API."""
        if not self.github_token:
            return None
        
        headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json",
        }
        
        try:
            response = requests.get(f"{self.github_api}/user", headers=headers)
            if response.status_code == 200:
                return response.json()["login"]
        except:
            pass
        
        return None
    
    def add_remote(self, remote_url: str):
        """Add GitHub remote to local repo."""
        logger.info("\n🔗 Adding GitHub remote...")
        
        try:
            # Remove existing remote if it exists
            subprocess.run(
                ["git", "remote", "remove", "origin"],
                cwd=self.project_root,
                capture_output=True,
            )
        except:
            pass
        
        try:
            subprocess.run(
                ["git", "remote", "add", "origin", remote_url],
                cwd=self.project_root,
                check=True,
                capture_output=True,
            )
            logger.success(f"   ✓ Remote added: {remote_url}")
        except subprocess.CalledProcessError as e:
            logger.error(f"   ❌ Failed to add remote: {e}")
    
    def push_to_github(self, branch: str = "main"):
        """Push code to GitHub."""
        logger.info(f"\n🚀 Pushing to GitHub (branch: {branch})...")
        
        try:
            # Rename branch to main if needed
            subprocess.run(
                ["git", "branch", "-M", branch],
                cwd=self.project_root,
                check=True,
                capture_output=True,
            )
            
            # Push
            result = subprocess.run(
                ["git", "push", "-u", "origin", branch],
                cwd=self.project_root,
                capture_output=True,
                text=True,
            )
            
            if result.returncode == 0:
                logger.success(f"   ✓ Pushed to {branch}")
            else:
                logger.error(f"   ❌ Push failed: {result.stderr}")
        
        except subprocess.CalledProcessError as e:
            logger.error(f"   ❌ Failed to push: {e}")
    
    def publish(
        self,
        repo_name: str = "salutations",
        description: str = "Multi-LLM Braiding System with Meta-Learning Agent",
        private: bool = True,
    ):
        """
        Complete publishing process using GitHub CLI.
        
        Args:
            repo_name: Name for the GitHub repository
            description: Repository description
            private: Whether to make the repo private (default: True)
        """
        logger.info("=" * 70)
        logger.info("📦 SELF-PUBLISHING AGENT (GitHub CLI)")
        logger.info("=" * 70)
        
        # Step 1: Check git
        if not self.check_git_installed():
            logger.error("Please install git first")
            return
        
        # Step 2: Check GitHub CLI
        if not self.check_gh_installed():
            logger.error("Please install GitHub CLI first")
            logger.info("   macOS: brew install gh")
            logger.info("   Other: https://cli.github.com/")
            return
        
        # Step 3: Check GitHub CLI auth
        if not self.check_gh_auth():
            logger.error("Please authenticate GitHub CLI first")
            logger.info("   Run: gh auth login")
            return
        
        # Step 4: Initialize git repo
        if not self.init_git_repo():
            return
        
        # Step 5: Create .gitignore
        self.create_gitignore()
        
        # Step 6: Generate README
        self.generate_readme()
        
        # Step 7: Stage files
        self.stage_files()
        
        # Step 8: Commit
        self.commit_changes("🤖 Initial commit by Self-Publishing Agent\n\nAuto-generated by autonomous AI agent")
        
        # Step 9: Create GitHub repo and push (all in one with gh CLI!)
        repo_url = self.create_github_repo_with_gh(repo_name, description, private)
        
        if not repo_url:
            logger.warning("\n⚠️  Failed to create/push repository")
            logger.info("   To push manually:")
            logger.info(f"   gh repo create {repo_name} --private --source . --push")
            return
        
        # Success!
        logger.info("\n" + "=" * 70)
        logger.success("🎉 PUBLISHING COMPLETE!")
        logger.info("=" * 70)
        
        logger.info(f"\n🌐 Your {'private' if private else 'public'} repository is live:")
        logger.info(f"   {repo_url}")
        logger.info(f"\n📋 Clone it:")
        logger.info(f"   gh repo clone {repo_name}")
        logger.info(f"\n🔒 Privacy: {'Private (only you can see it)' if private else 'Public (everyone can see it)'}")


def demo():
    """Demonstrate the self-publishing agent."""
    
    print("\n" + "=" * 70)
    print(" " * 15 + "📦 SELF-PUBLISHING AGENT DEMO")
    print("=" * 70)
    
    print("\n🤖 This agent can:")
    print("   1. Initialize a git repository")
    print("   2. Create .gitignore")
    print("   3. Generate README")
    print("   4. Commit all code")
    print("   5. Create private GitHub repository (via gh CLI)")
    print("   6. Push to GitHub automatically")
    print("   7. All in one command!")
    
    print("\n📝 Requirements:")
    print("   • Git installed")
    print("   • GitHub CLI (gh) installed")
    print("   • Authenticated with: gh auth login")
    
    print("\n🔧 Setup GitHub CLI:")
    print("   1. Install: brew install gh")
    print("   2. Authenticate: gh auth login")
    print("   3. Follow the prompts")
    print("   4. Done! No tokens needed.")
    
    project_root = Path(__file__).parent.parent
    agent = SelfPublishingAgent(project_root)
    
    # Check GitHub CLI
    print("\n🔍 Checking requirements...")
    
    if not agent.check_git_installed():
        print("\n❌ Git not installed")
        return
    
    if not agent.check_gh_installed():
        print("\n❌ GitHub CLI not installed")
        print("   Install with: brew install gh")
        return
    
    if not agent.check_gh_auth():
        print("\n❌ GitHub CLI not authenticated")
        print("   Run: gh auth login")
        return
    
    print("\n✅ All requirements met!")
    print("\n🚀 Publishing to private GitHub repository...")
    
    agent.publish(
        repo_name="salutations",
        description="Multi-LLM Braiding System with Meta-Learning Agent",
        private=True,  # Private repository
    )
    
    print("\n" + "=" * 70)
    print("💡 The agent published itself autonomously!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    demo()
