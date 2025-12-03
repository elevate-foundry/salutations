#!/usr/bin/env python3
"""Calculate current project fitness score (0-10)."""

import sys
import os
from pathlib import Path
import subprocess

sys.path.insert(0, str(Path(__file__).parent))

from examples.autonomous_git_agent import AutonomousGitAgent


def check_component_status():
    """Check status of each major component."""
    scores = {}
    
    # 1. Documentation (2 points max)
    doc_files = [
        "README.md", "ARCHITECTURE.md", "QUICKSTART.md",
        "PROJECT_SUMMARY.md", "AUTONOMOUS_GIT.md", "SCL_SPECIFICATION.md"
    ]
    doc_count = sum(1 for f in doc_files if Path(f).exists())
    scores["documentation"] = min(2.0, (doc_count / len(doc_files)) * 2.5)
    
    # 2. Core Braiding Implementation (2.5 points max)
    braiding_files = [
        "models/braided_model.py",
        "models/fusion_layers.py", 
        "examples/minimal_braiding_example.py",
        "tests/test_braiding.py"
    ]
    braiding_count = sum(1 for f in braiding_files if Path(f).exists())
    scores["braiding"] = (braiding_count / len(braiding_files)) * 2.5
    
    # 3. Tests (1.5 points max)
    test_dir = Path("tests")
    test_count = len(list(test_dir.glob("test_*.py"))) if test_dir.exists() else 0
    scores["tests"] = min(1.5, test_count * 0.5)
    
    # 4. Examples (1.5 points max)
    example_dir = Path("examples")
    example_count = len(list(example_dir.glob("*.py"))) if example_dir.exists() else 0
    scores["examples"] = min(1.5, (example_count / 10) * 1.5)
    
    # 5. MCP Server (1 point max)
    mcp_exists = Path("mcp/src/index.ts").exists()
    scores["mcp_server"] = 0.7 if mcp_exists else 0  # Incomplete
    
    # 6. CI/CD (0.5 points max)
    ci_exists = Path(".github/workflows/test.yml").exists()
    scores["ci_cd"] = 0.5 if ci_exists else 0
    
    # 7. SCL/Rust Implementation (0.5 points max)
    rust_exists = Path("rust/src/scl.rs").exists()
    scores["rust_scl"] = 0.5 if rust_exists else 0
    
    # 8. Memory/Neo4j (0.5 points max) 
    memory_exists = Path("memory/memory_manager.py").exists()
    scores["memory"] = 0.3 if memory_exists else 0  # Not integrated
    
    return scores


def calculate_total_fitness(scores):
    """Calculate total fitness from component scores."""
    total = sum(scores.values())
    return min(10.0, total)


def print_fitness_report(scores):
    """Print detailed fitness report."""
    print("\n" + "=" * 70)
    print(" " * 20 + "🏋️ PROJECT FITNESS REPORT")
    print("=" * 70)
    
    total = calculate_total_fitness(scores)
    
    # Overall score with visual bar
    print(f"\n📊 OVERALL FITNESS: {total:.1f}/10")
    bar_length = 50
    filled = int((total/10) * bar_length)
    bar = "█" * filled + "░" * (bar_length - filled)
    print(f"[{bar}]")
    
    # Status
    if total >= 9:
        status = "🌟 EXCELLENT - Production Ready"
        color = ""
    elif total >= 7:
        status = "✅ GOOD - Functional with gaps"
        color = ""
    elif total >= 5:
        status = "⚠️  FAIR - Needs work"
        color = ""
    else:
        status = "❌ POOR - Major work needed"
        color = ""
    
    print(f"\nStatus: {status}")
    
    # Component breakdown
    print("\n📋 COMPONENT BREAKDOWN:")
    print("-" * 40)
    
    components = [
        ("Documentation", "documentation", 2.0),
        ("Core Braiding", "braiding", 2.5),
        ("Tests", "tests", 1.5),
        ("Examples", "examples", 1.5),
        ("MCP Server", "mcp_server", 1.0),
        ("CI/CD", "ci_cd", 0.5),
        ("SCL/Rust", "rust_scl", 0.5),
        ("Memory/Neo4j", "memory", 0.5),
    ]
    
    for name, key, max_score in components:
        score = scores.get(key, 0)
        percentage = (score / max_score) * 100 if max_score > 0 else 0
        
        # Status icon
        if percentage >= 90:
            icon = "✅"
        elif percentage >= 60:
            icon = "🟡"
        else:
            icon = "❌"
        
        print(f"{icon} {name:15} {score:.1f}/{max_score:.1f} ({percentage:.0f}%)")
    
    # Git changes fitness
    print("\n📝 GIT CHANGES FITNESS:")
    print("-" * 40)
    
    try:
        agent = AutonomousGitAgent(Path.cwd())
        analysis = agent.analyze_changes()
        
        if analysis["num_files"] > 0:
            fitness = agent.calculate_commit_fitness(analysis)
            print(f"Current changes: {fitness.score:.2f}/1.00")
            print(f"Files changed: {analysis['num_files']}")
            
            if fitness.score >= 0.7:
                print("✅ Ready to auto-commit!")
            else:
                print(f"⏳ Need +{0.7 - fitness.score:.2f} to auto-commit")
        else:
            print("No uncommitted changes")
    except Exception as e:
        print(f"Could not analyze: {e}")
    
    # Improvements needed
    print("\n🎯 TO REACH 10/10:")
    print("-" * 40)
    
    improvements = []
    
    if scores.get("braiding", 0) < 2.5:
        improvements.append("• Test core braiding with real models")
    if scores.get("tests", 0) < 1.5:
        improvements.append("• Add more unit tests")
    if scores.get("mcp_server", 0) < 1.0:
        improvements.append("• Complete MCP TypeScript server")
    if scores.get("memory", 0) < 0.5:
        improvements.append("• Integrate Neo4j memory system")
    if scores.get("examples", 0) < 1.5:
        improvements.append("• Add more working examples")
    
    if improvements:
        for improvement in improvements[:5]:  # Top 5
            print(improvement)
    else:
        print("🌟 All components at maximum fitness!")
    
    # Time estimate
    remaining = 10.0 - total
    if remaining > 0:
        hours_needed = int(remaining * 2)  # Rough estimate
        print(f"\n⏱️  Estimated time to 10/10: {hours_needed} hours")
    
    print("\n" + "=" * 70)
    print()


def main():
    """Run fitness check."""
    scores = check_component_status()
    print_fitness_report(scores)
    
    # Return exit code based on fitness
    total = calculate_total_fitness(scores)
    if total >= 7:
        return 0  # Good enough
    else:
        return 1  # Needs work


if __name__ == "__main__":
    sys.exit(main())
