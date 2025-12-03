#!/usr/bin/env python3
"""Quick fitness check - see your code quality in real-time."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from examples.autonomous_git_agent import AutonomousGitAgent

def main():
    agent = AutonomousGitAgent(Path.cwd())
    analysis = agent.analyze_changes()
    
    if analysis["num_files"] == 0:
        print("\n📊 No changes detected - make some changes and run again!\n")
        return
    
    fitness = agent.calculate_commit_fitness(analysis)
    
    # Display
    print("\n" + "=" * 70)
    print("📊 CONTINUOUS FITNESS MONITOR")
    print("=" * 70)
    
    print(f"\n🎯 Score: {fitness.score:.2f} / 1.00")
    
    # Progress bar
    bar_length = 40
    filled = int(fitness.score * bar_length)
    bar = "█" * filled + "░" * (bar_length - filled)
    print(f"\n   [{bar}] {fitness.score*100:.0f}%")
    
    # Threshold
    threshold = 0.7
    if fitness.score >= threshold:
        print(f"\n   ✅ READY TO AUTO-COMMIT!")
    else:
        gap = threshold - fitness.score
        print(f"\n   ⏳ Need +{gap:.2f} to reach threshold ({threshold})")
    
    # Details
    print(f"\n📁 Changes: {analysis['num_files']} files")
    if analysis.get('staged_files'):
        print(f"   • {len(analysis['staged_files'])} staged")
    if analysis.get('unstaged_files'):
        print(f"   • {len(analysis['unstaged_files'])} unstaged")
    if analysis.get('untracked_files'):
        print(f"   • {len(analysis['untracked_files'])} untracked")
    
    print("\n" + "=" * 70 + "\n")

if __name__ == "__main__":
    main()
