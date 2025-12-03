#!/bin/bash
# Quick fitness check - see if your changes are improving the codebase

cd "$(dirname "$0")"

python3 << 'EOF'
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from examples.autonomous_git_agent import AutonomousGitAgent

# Create agent
agent = AutonomousGitAgent(Path.cwd())

# Analyze changes
analysis = agent.analyze_changes()

if analysis["num_files"] == 0:
    print("\n📊 No changes detected")
    print("   Make some changes and run again!")
    sys.exit(0)

# Calculate fitness
fitness = agent.calculate_commit_fitness(analysis)

# Display fitness report
print("\n" + "=" * 70)
print("📊 CONTINUOUS FITNESS MONITOR")
print("=" * 70)

print(f"\n🎯 Current Score: {fitness.score:.2f} / 1.00")

# Visual progress bar
bar_length = 40
filled = int(fitness.score * bar_length)
bar = "█" * filled + "░" * (bar_length - filled)
print(f"\n   [{bar}] {fitness.score*100:.0f}%")

# Show threshold
threshold = 0.7
if fitness.score >= threshold:
    print(f"\n   ✅ READY TO COMMIT (threshold: {threshold})")
else:
    gap = threshold - fitness.score
    print(f"\n   ⏳ Need +{gap:.2f} to auto-commit (threshold: {threshold})")

# Show strengths
if fitness.reasons:
    print(f"\n✅ Strengths:")
    for reason in fitness.reasons:
        print(f"   • {reason}")

# Show improvements needed
if fitness.suggestions:
    print(f"\n💡 To improve fitness:")
    for suggestion in fitness.suggestions:
        print(f"   • {suggestion}")

# Show file breakdown
print(f"\n📁 Files ({analysis['num_files']} total):")
if analysis.get('staged_files'):
    print(f"   • Staged: {len(analysis['staged_files'])}")
if analysis.get('unstaged_files'):
    print(f"   • Unstaged: {len(analysis['unstaged_files'])}")
if analysis.get('untracked_files'):
    print(f"   • Untracked: {len(analysis['untracked_files'])}")

print(f"\n📝 File types: {', '.join(analysis['file_types'].keys())}")

print("\n" + "=" * 70)
print("💡 TIP: Run this script as you work to see fitness in real-time!")
print("=" * 70 + "\n")

EOF
