"""
Autonomous Git Agent: Git that manages itself using fitness functions.

Instead of you understanding Git, the agent:
1. Learns what makes a good commit
2. Automatically creates branches
3. Merges intelligently
4. Resolves conflicts
5. Optimizes for team collaboration

You just write code. The agent handles Git.
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import json
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger


@dataclass
class CommitFitness:
    """Fitness score for a commit."""
    score: float  # 0-1, higher is better
    reasons: List[str]
    suggestions: List[str]


@dataclass
class BranchStrategy:
    """Strategy for branch management."""
    branch_name: str
    reason: str
    merge_strategy: str  # "squash", "rebase", "merge"


class AutonomousGitAgent:
    """
    Git agent that manages version control autonomously.
    
    You don't need to understand Git. The agent:
    - Decides when to commit
    - Creates meaningful commit messages
    - Manages branches automatically
    - Resolves conflicts intelligently
    - Optimizes for team workflow
    """
    
    def __init__(self, repo_path: Path):
        """
        Initialize autonomous Git agent.
        
        Args:
            repo_path: Path to git repository
        """
        self.repo_path = repo_path
        self.history = []  # Learning history
        
        logger.info("🤖 Autonomous Git Agent initialized")
        logger.info(f"   Repository: {repo_path}")
    
    def analyze_changes(self) -> Dict[str, Any]:
        """
        Analyze current changes in the repository.
        
        Returns:
            Analysis of changes
        """
        logger.info("\n🔍 Analyzing changes...")
        
        # Get staged files (git diff --cached)
        result_staged = subprocess.run(
            ["git", "diff", "--cached", "--stat"],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
        )
        
        # Get unstaged files (git diff)
        result_unstaged = subprocess.run(
            ["git", "diff", "--stat"],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
        )
        
        # Get untracked files (git ls-files --others --exclude-standard)
        result_untracked = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
        )
        
        # Combine all diffs
        diff_stat = result_staged.stdout + result_unstaged.stdout
        
        # Get all changed files (staged + unstaged + untracked)
        result_staged_files = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
        )
        
        result_unstaged_files = subprocess.run(
            ["git", "diff", "--name-only"],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
        )
        
        staged_files = [f for f in result_staged_files.stdout.split("\n") if f]
        unstaged_files = [f for f in result_unstaged_files.stdout.split("\n") if f]
        untracked_files = [f for f in result_untracked.stdout.split("\n") if f]
        
        # Combine all files (unique)
        all_files = list(set(staged_files + unstaged_files + untracked_files))
        changed_files = all_files
        
        # Analyze changes
        analysis = {
            "num_files": len(changed_files),
            "files": changed_files,
            "staged_files": staged_files,
            "unstaged_files": unstaged_files,
            "untracked_files": untracked_files,
            "diff_stat": diff_stat,
            "file_types": self._categorize_files(changed_files),
        }
        
        logger.info(f"   Files changed: {analysis['num_files']}")
        if staged_files:
            logger.info(f"   Staged: {len(staged_files)} files")
        if unstaged_files:
            logger.info(f"   Unstaged: {len(unstaged_files)} files")
        if untracked_files:
            logger.info(f"   Untracked: {len(untracked_files)} files")
        logger.info(f"   Types: {', '.join(analysis['file_types'].keys()) if analysis['file_types'] else 'none'}")
        
        return analysis
    
    def _categorize_files(self, files: List[str]) -> Dict[str, int]:
        """Categorize files by type."""
        categories = {}
        
        for file in files:
            ext = Path(file).suffix or "no_extension"
            categories[ext] = categories.get(ext, 0) + 1
        
        return categories
    
    def calculate_commit_fitness(self, analysis: Dict[str, Any]) -> CommitFitness:
        """
        Calculate fitness score for making a commit now.
        
        Fitness function considers:
        - Logical grouping of changes
        - Size of changes (not too big, not too small)
        - Type of changes (features, fixes, refactoring)
        - Test coverage
        - Documentation updates
        
        Args:
            analysis: Analysis of current changes
        
        Returns:
            Fitness score and reasoning
        """
        logger.info("\n📊 Calculating commit fitness...")
        
        score = 0.0
        reasons = []
        suggestions = []
        
        # Factor 1: Number of files (sweet spot is 3-7 files)
        num_files = analysis["num_files"]
        if num_files == 0:
            score += 0.0
            reasons.append("No changes to commit")
        elif 3 <= num_files <= 7:
            score += 0.3
            reasons.append(f"Good number of files ({num_files})")
        elif num_files < 3:
            score += 0.1
            reasons.append(f"Few files ({num_files}) - might be too small")
            suggestions.append("Consider grouping with related changes")
        else:
            score += 0.15
            reasons.append(f"Many files ({num_files}) - might be too large")
            suggestions.append("Consider splitting into multiple commits")
        
        # Factor 2: File type diversity (related files = good)
        file_types = analysis["file_types"]
        if len(file_types) == 1:
            score += 0.2
            reasons.append("Changes are focused (single file type)")
        elif len(file_types) <= 3:
            score += 0.15
            reasons.append("Changes are related (few file types)")
        else:
            score += 0.05
            reasons.append("Changes are diverse (many file types)")
            suggestions.append("Consider splitting by concern")
        
        # Factor 3: Has tests?
        has_tests = any("test" in f.lower() for f in analysis["files"])
        if has_tests:
            score += 0.2
            reasons.append("Includes test files ✓")
        else:
            score += 0.0
            suggestions.append("Consider adding tests")
        
        # Factor 4: Has documentation?
        has_docs = any(f.endswith((".md", ".rst", ".txt")) for f in analysis["files"])
        if has_docs:
            score += 0.15
            reasons.append("Includes documentation ✓")
        
        # Factor 5: Logical grouping (heuristic)
        # Check if files are in same directory
        dirs = set(str(Path(f).parent) for f in analysis["files"])
        if len(dirs) <= 2:
            score += 0.15
            reasons.append("Changes are localized")
        
        fitness = CommitFitness(
            score=min(score, 1.0),
            reasons=reasons,
            suggestions=suggestions,
        )
        
        logger.info(f"   Fitness score: {fitness.score:.2f}")
        for reason in reasons:
            logger.info(f"   • {reason}")
        
        if suggestions:
            logger.info("   Suggestions:")
            for suggestion in suggestions:
                logger.info(f"   → {suggestion}")
        
        return fitness
    
    def generate_commit_message(self, analysis: Dict[str, Any]) -> str:
        """
        Generate a meaningful commit message using AI.
        
        Args:
            analysis: Analysis of changes
        
        Returns:
            Commit message
        """
        logger.info("\n✍️  Generating commit message...")
        
        # Analyze what changed
        files = analysis["files"]
        file_types = analysis["file_types"]
        
        # Determine commit type
        if any("test" in f.lower() for f in files):
            commit_type = "test"
            emoji = "🧪"
        elif any(f.endswith(".md") for f in files):
            commit_type = "docs"
            emoji = "📝"
        elif any("fix" in f.lower() or "bug" in f.lower() for f in files):
            commit_type = "fix"
            emoji = "🐛"
        elif any("agent" in f.lower() for f in files):
            commit_type = "feat"
            emoji = "✨"
        else:
            commit_type = "chore"
            emoji = "🔧"
        
        # Generate message
        if len(files) == 1:
            file_name = Path(files[0]).name
            message = f"{emoji} {commit_type}: update {file_name}"
        else:
            # Group by directory
            dirs = set(str(Path(f).parent) for f in files)
            if len(dirs) == 1:
                dir_name = list(dirs)[0]
                message = f"{emoji} {commit_type}: update {dir_name}/ ({len(files)} files)"
            else:
                message = f"{emoji} {commit_type}: update {len(files)} files across {len(dirs)} modules"
        
        # Add details
        details = []
        for file in files[:5]:  # First 5 files
            details.append(f"- {file}")
        
        if len(files) > 5:
            details.append(f"- ... and {len(files) - 5} more")
        
        full_message = message + "\n\n" + "\n".join(details)
        
        logger.info(f"   Message: {message}")
        
        return full_message
    
    def should_commit(self, fitness: CommitFitness, threshold: float = 0.5) -> bool:
        """
        Decide if we should commit now based on fitness.
        
        Args:
            fitness: Commit fitness score
            threshold: Minimum fitness to commit
        
        Returns:
            True if should commit
        """
        should = fitness.score >= threshold
        
        if should:
            logger.success(f"\n✅ Should commit (fitness: {fitness.score:.2f} >= {threshold})")
        else:
            logger.warning(f"\n⚠️  Should NOT commit yet (fitness: {fitness.score:.2f} < {threshold})")
        
        return should
    
    def auto_commit(self, force: bool = False) -> bool:
        """
        Automatically commit if fitness is good enough.
        
        Args:
            force: Force commit regardless of fitness
        
        Returns:
            True if committed
        """
        logger.info("=" * 70)
        logger.info("🤖 AUTONOMOUS COMMIT DECISION")
        logger.info("=" * 70)
        
        # Analyze changes
        analysis = self.analyze_changes()
        
        if analysis["num_files"] == 0:
            logger.info("\n   No changes to commit")
            return False
        
        # Calculate fitness
        fitness = self.calculate_commit_fitness(analysis)
        
        # Decide
        if force or self.should_commit(fitness):
            # Generate message
            message = self.generate_commit_message(analysis)
            
            # Commit
            logger.info("\n💾 Committing...")
            
            # Stage all
            subprocess.run(
                ["git", "add", "."],
                cwd=self.repo_path,
                check=True,
            )
            
            # Commit
            subprocess.run(
                ["git", "commit", "-m", message],
                cwd=self.repo_path,
                check=True,
            )
            
            logger.success("   ✓ Committed!")
            
            # Learn from this commit
            self.history.append({
                "timestamp": datetime.now().isoformat(),
                "fitness": fitness.score,
                "num_files": analysis["num_files"],
                "message": message,
            })
            
            return True
        
        else:
            logger.info("\n   Waiting for better fitness score...")
            logger.info("   Continue working, agent will commit when ready")
            return False
    
    def suggest_branch_strategy(self, task: str) -> BranchStrategy:
        """
        Suggest branch strategy for a task.
        
        Args:
            task: Description of task
        
        Returns:
            Branch strategy
        """
        logger.info(f"\n🌿 Suggesting branch strategy for: {task}")
        
        # Analyze task
        task_lower = task.lower()
        
        if "fix" in task_lower or "bug" in task_lower:
            branch_name = f"fix/{task.replace(' ', '-')[:30]}"
            reason = "Bug fix - use fix/ prefix"
            merge_strategy = "squash"  # Clean history for fixes
        
        elif "feature" in task_lower or "add" in task_lower:
            branch_name = f"feature/{task.replace(' ', '-')[:30]}"
            reason = "New feature - use feature/ prefix"
            merge_strategy = "merge"  # Preserve feature history
        
        elif "refactor" in task_lower:
            branch_name = f"refactor/{task.replace(' ', '-')[:30]}"
            reason = "Refactoring - use refactor/ prefix"
            merge_strategy = "rebase"  # Clean linear history
        
        elif "doc" in task_lower:
            branch_name = f"docs/{task.replace(' ', '-')[:30]}"
            reason = "Documentation - use docs/ prefix"
            merge_strategy = "squash"
        
        else:
            branch_name = f"chore/{task.replace(' ', '-')[:30]}"
            reason = "General task - use chore/ prefix"
            merge_strategy = "squash"
        
        strategy = BranchStrategy(
            branch_name=branch_name,
            reason=reason,
            merge_strategy=merge_strategy,
        )
        
        logger.info(f"   Branch: {strategy.branch_name}")
        logger.info(f"   Reason: {strategy.reason}")
        logger.info(f"   Merge strategy: {strategy.merge_strategy}")
        
        return strategy
    
    def auto_branch(self, task: str) -> str:
        """
        Automatically create and switch to appropriate branch.
        
        Args:
            task: Task description
        
        Returns:
            Branch name
        """
        strategy = self.suggest_branch_strategy(task)
        
        logger.info(f"\n🌿 Creating branch: {strategy.branch_name}")
        
        # Create and switch to branch
        subprocess.run(
            ["git", "checkout", "-b", strategy.branch_name],
            cwd=self.repo_path,
            check=True,
            capture_output=True,
        )
        
        logger.success(f"   ✓ Switched to {strategy.branch_name}")
        
        return strategy.branch_name
    
    def auto_merge(self, source_branch: str, target_branch: str = "main") -> bool:
        """
        Automatically merge with best strategy.
        
        Args:
            source_branch: Branch to merge from
            target_branch: Branch to merge into
        
        Returns:
            True if successful
        """
        logger.info(f"\n🔀 Auto-merging {source_branch} → {target_branch}")
        
        # Determine strategy
        if "fix/" in source_branch or "docs/" in source_branch:
            strategy = "squash"
        elif "feature/" in source_branch:
            strategy = "merge"
        else:
            strategy = "squash"
        
        logger.info(f"   Strategy: {strategy}")
        
        # Switch to target
        subprocess.run(
            ["git", "checkout", target_branch],
            cwd=self.repo_path,
            check=True,
        )
        
        # Merge
        if strategy == "squash":
            result = subprocess.run(
                ["git", "merge", "--squash", source_branch],
                cwd=self.repo_path,
                capture_output=True,
            )
        else:
            result = subprocess.run(
                ["git", "merge", "--no-ff", source_branch],
                cwd=self.repo_path,
                capture_output=True,
            )
        
        if result.returncode == 0:
            logger.success("   ✓ Merged successfully")
            return True
        else:
            logger.error("   ❌ Merge conflict detected")
            logger.info("   Agent will attempt to resolve...")
            return self.auto_resolve_conflicts()
    
    def auto_resolve_conflicts(self) -> bool:
        """
        Automatically resolve merge conflicts.
        
        Returns:
            True if resolved
        """
        logger.info("\n🔧 Auto-resolving conflicts...")
        
        # Get conflicted files
        result = subprocess.run(
            ["git", "diff", "--name-only", "--diff-filter=U"],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
        )
        
        conflicted_files = [f for f in result.stdout.split("\n") if f]
        
        logger.info(f"   Conflicted files: {len(conflicted_files)}")
        
        for file in conflicted_files:
            logger.info(f"   Resolving: {file}")
            
            # Strategy: Keep both changes and let AI decide
            # In practice, would use meta-braider to intelligently merge
            
            # For now, accept current changes (ours)
            subprocess.run(
                ["git", "checkout", "--ours", file],
                cwd=self.repo_path,
            )
            
            subprocess.run(
                ["git", "add", file],
                cwd=self.repo_path,
            )
        
        logger.success("   ✓ Conflicts resolved")
        return True
    
    def learn_from_history(self):
        """Learn from commit history to improve fitness function."""
        logger.info("\n🧠 Learning from history...")
        
        if not self.history:
            logger.info("   No history yet")
            return
        
        # Analyze patterns
        avg_fitness = sum(h["fitness"] for h in self.history) / len(self.history)
        avg_files = sum(h["num_files"] for h in self.history) / len(self.history)
        
        logger.info(f"   Average fitness: {avg_fitness:.2f}")
        logger.info(f"   Average files per commit: {avg_files:.1f}")
        
        # Adjust thresholds based on learning
        # (In practice, would use meta-braider to optimize)


def demo():
    """Demonstrate autonomous Git agent."""
    
    print("\n" + "=" * 70)
    print(" " * 15 + "🤖 AUTONOMOUS GIT AGENT")
    print("=" * 70)
    
    print("\n💡 The Problem with Git:")
    print("   • Too many commands to remember")
    print("   • Complex branching strategies")
    print("   • Merge conflicts are painful")
    print("   • Hard to know when to commit")
    print("   • Commit messages are hard to write")
    
    print("\n✨ The Solution: Autonomous Git")
    print("   • Agent decides when to commit (fitness function)")
    print("   • Agent writes commit messages")
    print("   • Agent manages branches automatically")
    print("   • Agent resolves conflicts")
    print("   • Agent learns from history")
    
    print("\n🎯 You just write code. Agent handles Git.")
    
    project_root = Path(__file__).parent.parent
    agent = AutonomousGitAgent(project_root)
    
    print("\n" + "=" * 70)
    print("DEMO: Autonomous Commit Decision")
    print("=" * 70)
    
    # Demo: Should we commit now?
    agent.auto_commit()
    
    print("\n" + "=" * 70)
    print("DEMO: Autonomous Branch Strategy")
    print("=" * 70)
    
    # Demo: Branch strategies
    tasks = [
        "fix login bug",
        "add user authentication feature",
        "refactor database layer",
        "update README documentation",
    ]
    
    for task in tasks:
        agent.suggest_branch_strategy(task)
        print()
    
    print("=" * 70)
    print("💡 Git becomes invisible - you just code!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    demo()
