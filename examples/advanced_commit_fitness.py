"""
Advanced CommitFitness: The Conscience with Learning

This module implements an advanced fitness function that:
1. Learns from commit history
2. Adapts to team patterns
3. Improves over time
4. Provides detailed reasoning
"""

import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import json
from datetime import datetime
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger


@dataclass
class FitnessWeights:
    """Learnable weights for fitness calculation."""
    file_count: float = 0.30
    cohesion: float = 0.20
    tests: float = 0.20
    documentation: float = 0.15
    localization: float = 0.15
    
    def to_dict(self) -> Dict[str, float]:
        return {
            "file_count": self.file_count,
            "cohesion": self.cohesion,
            "tests": self.tests,
            "documentation": self.documentation,
            "localization": self.localization,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> 'FitnessWeights':
        return cls(**data)


@dataclass
class CommitFitness:
    """Enhanced commit fitness with learning."""
    score: float
    reasons: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    breakdown: Dict[str, float] = field(default_factory=dict)
    confidence: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "score": self.score,
            "reasons": self.reasons,
            "suggestions": self.suggestions,
            "breakdown": self.breakdown,
            "confidence": self.confidence,
        }


class AdvancedCommitFitness:
    """
    Advanced fitness calculator with learning capabilities.
    
    The Conscience of the Entangled Git system.
    """
    
    def __init__(self, repo_path: Path):
        """
        Initialize advanced fitness calculator.
        
        Args:
            repo_path: Path to repository
        """
        self.repo_path = repo_path
        self.weights = FitnessWeights()
        self.history: List[Dict[str, Any]] = []
        self.team_patterns: Dict[str, Any] = {}
        
        # Load saved state
        self._load_state()
        
        logger.info("🧠 Advanced CommitFitness initialized")
        logger.info(f"   Weights: {self.weights.to_dict()}")
    
    def calculate(self, analysis: Dict[str, Any]) -> CommitFitness:
        """
        Calculate fitness score with detailed breakdown.
        
        Args:
            analysis: Analysis of changes
        
        Returns:
            Fitness score with reasoning
        """
        logger.info("\n🧠 Calculating advanced fitness...")
        
        score = 0.0
        reasons = []
        suggestions = []
        breakdown = {}
        
        # Factor 1: File Count (sweet spot: 3-7 files)
        num_files = analysis["num_files"]
        file_score = self._score_file_count(num_files)
        score += file_score * self.weights.file_count
        breakdown["file_count"] = file_score
        
        if file_score > 0.8:
            reasons.append(f"Optimal file count ({num_files} files)")
        elif file_score < 0.5:
            if num_files < 3:
                suggestions.append("Consider grouping with related changes")
            else:
                suggestions.append("Consider splitting into multiple commits")
        
        # Factor 2: Cohesion (related files)
        cohesion_score = self._score_cohesion(analysis)
        score += cohesion_score * self.weights.cohesion
        breakdown["cohesion"] = cohesion_score
        
        if cohesion_score > 0.8:
            reasons.append("Changes are highly cohesive")
        elif cohesion_score < 0.5:
            suggestions.append("Group files by feature or module")
        
        # Factor 3: Tests
        test_score = self._score_tests(analysis)
        score += test_score * self.weights.tests
        breakdown["tests"] = test_score
        
        if test_score > 0.8:
            reasons.append("Includes comprehensive tests")
        elif test_score < 0.3:
            suggestions.append("Add test coverage")
        
        # Factor 4: Documentation
        doc_score = self._score_documentation(analysis)
        score += doc_score * self.weights.documentation
        breakdown["documentation"] = doc_score
        
        if doc_score > 0.8:
            reasons.append("Documentation updated")
        elif doc_score < 0.3:
            suggestions.append("Update relevant documentation")
        
        # Factor 5: Localization (focused changes)
        local_score = self._score_localization(analysis)
        score += local_score * self.weights.localization
        breakdown["localization"] = local_score
        
        if local_score > 0.8:
            reasons.append("Changes are well-localized")
        
        # Calculate confidence based on history
        confidence = self._calculate_confidence(score, analysis)
        
        fitness = CommitFitness(
            score=min(score, 1.0),
            reasons=reasons,
            suggestions=suggestions,
            breakdown=breakdown,
            confidence=confidence,
        )
        
        logger.info(f"   Score: {fitness.score:.2f}")
        logger.info(f"   Confidence: {fitness.confidence:.0%}")
        logger.info("   Breakdown:")
        for factor, value in breakdown.items():
            logger.info(f"     • {factor}: {value:.2f}")
        
        return fitness
    
    def _score_file_count(self, num_files: int) -> float:
        """Score based on file count (sweet spot: 3-7)."""
        if num_files == 0:
            return 0.0
        elif 3 <= num_files <= 7:
            return 1.0
        elif num_files < 3:
            return 0.3 + (num_files / 3) * 0.4
        else:
            # Penalty for too many files
            return max(0.5 - (num_files - 7) * 0.05, 0.2)
    
    def _score_cohesion(self, analysis: Dict[str, Any]) -> float:
        """Score based on file cohesion."""
        files = analysis["files"]
        if not files:
            return 0.0
        
        # Check file types
        file_types = analysis["file_types"]
        type_diversity = len(file_types)
        
        # Check directories
        dirs = set(str(Path(f).parent) for f in files)
        dir_diversity = len(dirs)
        
        # Check name similarity
        names = [Path(f).stem for f in files]
        name_similarity = self._calculate_name_similarity(names)
        
        # Combine scores
        type_score = 1.0 if type_diversity == 1 else max(0.5 - (type_diversity - 1) * 0.1, 0.2)
        dir_score = 1.0 if dir_diversity <= 2 else max(0.7 - (dir_diversity - 2) * 0.1, 0.3)
        
        return (type_score * 0.4 + dir_score * 0.4 + name_similarity * 0.2)
    
    def _calculate_name_similarity(self, names: List[str]) -> float:
        """Calculate similarity between file names."""
        if len(names) <= 1:
            return 1.0
        
        # Check if names share common prefixes/suffixes
        similarities = []
        for i, name1 in enumerate(names):
            for name2 in names[i+1:]:
                # Simple similarity: shared substring length
                common = self._longest_common_substring(name1, name2)
                similarity = len(common) / max(len(name1), len(name2))
                similarities.append(similarity)
        
        return np.mean(similarities) if similarities else 0.0
    
    def _longest_common_substring(self, s1: str, s2: str) -> str:
        """Find longest common substring."""
        m = [[0] * (1 + len(s2)) for _ in range(1 + len(s1))]
        longest, x_longest = 0, 0
        
        for x in range(1, 1 + len(s1)):
            for y in range(1, 1 + len(s2)):
                if s1[x - 1] == s2[y - 1]:
                    m[x][y] = m[x - 1][y - 1] + 1
                    if m[x][y] > longest:
                        longest = m[x][y]
                        x_longest = x
        
        return s1[x_longest - longest: x_longest]
    
    def _score_tests(self, analysis: Dict[str, Any]) -> float:
        """Score based on test coverage."""
        files = analysis["files"]
        
        # Count test files
        test_files = [f for f in files if "test" in f.lower()]
        
        if not test_files:
            return 0.0
        
        # Ratio of test files to total files
        test_ratio = len(test_files) / len(files)
        
        # Ideal: 20-40% test files
        if 0.2 <= test_ratio <= 0.4:
            return 1.0
        elif test_ratio < 0.2:
            return test_ratio / 0.2
        else:
            return 0.8  # Still good if more tests
    
    def _score_documentation(self, analysis: Dict[str, Any]) -> float:
        """Score based on documentation."""
        files = analysis["files"]
        
        # Check for doc files
        doc_files = [
            f for f in files
            if f.endswith((".md", ".rst", ".txt")) or "doc" in f.lower()
        ]
        
        if not doc_files:
            return 0.0
        
        # Bonus if README is updated
        has_readme = any("readme" in f.lower() for f in doc_files)
        
        return 1.0 if has_readme else 0.7
    
    def _score_localization(self, analysis: Dict[str, Any]) -> float:
        """Score based on how localized changes are."""
        files = analysis["files"]
        if not files:
            return 0.0
        
        # Check directory spread
        dirs = set(str(Path(f).parent) for f in files)
        
        if len(dirs) == 1:
            return 1.0
        elif len(dirs) == 2:
            return 0.8
        elif len(dirs) <= 4:
            return 0.6
        else:
            return max(0.4 - (len(dirs) - 4) * 0.05, 0.2)
    
    def _calculate_confidence(self, score: float, analysis: Dict[str, Any]) -> float:
        """Calculate confidence in the fitness score."""
        if not self.history:
            return 0.7  # Lower confidence with no history
        
        # Compare to historical patterns
        similar_commits = [
            h for h in self.history
            if abs(h["num_files"] - analysis["num_files"]) <= 2
        ]
        
        if not similar_commits:
            return 0.8
        
        # High confidence if score matches historical patterns
        avg_historical_score = np.mean([h["fitness"] for h in similar_commits])
        score_diff = abs(score - avg_historical_score)
        
        confidence = 1.0 - (score_diff * 0.5)
        return max(min(confidence, 1.0), 0.5)
    
    def learn_from_commit(self, analysis: Dict[str, Any], fitness: CommitFitness):
        """
        Learn from a commit to improve future predictions.
        
        Args:
            analysis: Analysis of the commit
            fitness: Fitness score that was calculated
        """
        logger.info("\n🧠 Learning from commit...")
        
        # Add to history
        self.history.append({
            "timestamp": datetime.now().isoformat(),
            "num_files": analysis["num_files"],
            "file_types": analysis["file_types"],
            "fitness": fitness.score,
            "breakdown": fitness.breakdown,
        })
        
        # Update weights based on patterns
        if len(self.history) >= 10:
            self._update_weights()
        
        # Save state
        self._save_state()
        
        logger.info(f"   History size: {len(self.history)}")
    
    def _update_weights(self):
        """Update weights based on learning."""
        logger.info("   Updating weights from patterns...")
        
        # Analyze recent commits
        recent = self.history[-20:]
        
        # Find what factors correlate with good commits
        good_commits = [h for h in recent if h["fitness"] >= 0.7]
        
        if not good_commits:
            return
        
        # Calculate average breakdown for good commits
        avg_breakdown = {}
        for factor in ["file_count", "cohesion", "tests", "documentation", "localization"]:
            values = [h["breakdown"].get(factor, 0) for h in good_commits]
            avg_breakdown[factor] = np.mean(values) if values else 0
        
        # Adjust weights toward factors that matter
        total = sum(avg_breakdown.values())
        if total > 0:
            # Smooth adjustment (don't change too drastically)
            alpha = 0.1  # Learning rate
            
            for factor, value in avg_breakdown.items():
                new_weight = value / total
                old_weight = getattr(self.weights, factor)
                setattr(self.weights, factor, old_weight * (1 - alpha) + new_weight * alpha)
        
        logger.info(f"   Updated weights: {self.weights.to_dict()}")
    
    def learn_from_team(self, team_history: List[Dict[str, Any]]):
        """
        Learn from team commit patterns.
        
        Args:
            team_history: History of team commits
        """
        logger.info("\n🧠 Learning from team patterns...")
        
        # Analyze team patterns
        self.team_patterns = {
            "avg_files_per_commit": np.mean([h["num_files"] for h in team_history]),
            "test_ratio": np.mean([
                len([f for f in h.get("files", []) if "test" in f.lower()]) / max(h["num_files"], 1)
                for h in team_history
            ]),
            "doc_ratio": np.mean([
                len([f for f in h.get("files", []) if f.endswith(".md")]) / max(h["num_files"], 1)
                for h in team_history
            ]),
        }
        
        logger.info(f"   Team patterns: {self.team_patterns}")
        
        # Adjust weights to match team
        if self.team_patterns["test_ratio"] > 0.3:
            self.weights.tests = min(self.weights.tests + 0.05, 0.3)
        
        if self.team_patterns["doc_ratio"] > 0.2:
            self.weights.documentation = min(self.weights.documentation + 0.05, 0.25)
    
    def _save_state(self):
        """Save learning state to disk."""
        state_file = self.repo_path / ".git" / "fitness_state.json"
        
        try:
            state = {
                "weights": self.weights.to_dict(),
                "history": self.history[-100:],  # Keep last 100
                "team_patterns": self.team_patterns,
            }
            
            state_file.parent.mkdir(parents=True, exist_ok=True)
            with open(state_file, "w") as f:
                json.dump(state, f, indent=2)
        
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
    
    def _load_state(self):
        """Load learning state from disk."""
        state_file = self.repo_path / ".git" / "fitness_state.json"
        
        if not state_file.exists():
            return
        
        try:
            with open(state_file) as f:
                state = json.load(f)
            
            self.weights = FitnessWeights.from_dict(state.get("weights", {}))
            self.history = state.get("history", [])
            self.team_patterns = state.get("team_patterns", {})
            
            logger.info(f"   Loaded state: {len(self.history)} commits in history")
        
        except Exception as e:
            logger.error(f"Failed to load state: {e}")


def demo():
    """Demonstrate advanced commit fitness."""
    
    print("\n" + "=" * 70)
    print(" " * 15 + "🧠 ADVANCED COMMIT FITNESS")
    print(" " * 20 + "The Conscience")
    print("=" * 70)
    
    print("\n💡 What is CommitFitness?")
    print("   The conscience that decides when and how to commit.")
    print("   Uses mathematical scoring + machine learning.")
    
    print("\n📊 Fitness Function:")
    print("   Score = f(file_count, cohesion, tests, docs, localization)")
    print("   Range: 0.0 - 1.0 (higher is better)")
    print("   Threshold: 0.7 for auto-commit")
    
    print("\n🧠 Learning Capabilities:")
    print("   • Learns from commit history")
    print("   • Adapts weights based on patterns")
    print("   • Learns from team conventions")
    print("   • Improves confidence over time")
    
    # Create fitness calculator
    repo_path = Path(__file__).parent.parent
    fitness_calc = AdvancedCommitFitness(repo_path)
    
    # Example 1: Good commit
    print("\n" + "=" * 70)
    print("Example 1: Good Commit")
    print("=" * 70)
    
    analysis1 = {
        "num_files": 5,
        "files": ["auth.py", "auth_test.py", "middleware.py", "README.md", "docs/auth.md"],
        "file_types": {".py": 3, ".md": 2},
    }
    
    fitness1 = fitness_calc.calculate(analysis1)
    print(f"\n✅ Fitness: {fitness1.score:.2f}")
    print(f"   Confidence: {fitness1.confidence:.0%}")
    print("   Reasons:")
    for reason in fitness1.reasons:
        print(f"     • {reason}")
    
    # Example 2: Needs improvement
    print("\n" + "=" * 70)
    print("Example 2: Needs Improvement")
    print("=" * 70)
    
    analysis2 = {
        "num_files": 2,
        "files": ["utils.py", "config.py"],
        "file_types": {".py": 2},
    }
    
    fitness2 = fitness_calc.calculate(analysis2)
    print(f"\n⚠️  Fitness: {fitness2.score:.2f}")
    print(f"   Confidence: {fitness2.confidence:.0%}")
    print("   Suggestions:")
    for suggestion in fitness2.suggestions:
        print(f"     • {suggestion}")
    
    # Learn from commits
    print("\n" + "=" * 70)
    print("Learning from Commits")
    print("=" * 70)
    
    fitness_calc.learn_from_commit(analysis1, fitness1)
    print("   ✓ Learned from good commit")
    print("   ✓ Updated patterns")
    print("   ✓ Saved state")
    
    print("\n" + "=" * 70)
    print("🧠 CommitFitness: The Conscience That Learns")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    demo()
