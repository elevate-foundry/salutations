"""
Git Daemon: Always-running autonomous Git agent.

Runs as a background service that:
1. Watches for file changes
2. Automatically commits when fitness is high
3. Restarts on machine reboot
4. Logs all decisions
5. Learns continuously
"""

import sys
import time
import signal
from pathlib import Path
from datetime import datetime
from typing import Optional
import json

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

from autonomous_git_agent import AutonomousGitAgent
from loguru import logger


class GitDaemon:
    """
    Always-running Git daemon that watches your repo and commits intelligently.
    """
    
    def __init__(
        self,
        repo_path: Path,
        check_interval: int = 300,  # 5 minutes (or 1 second for real-time!)
        auto_commit_threshold: float = 0.7,
        log_file: Optional[Path] = None,
        quiet_mode: bool = False,  # Reduce logging for high-frequency checks
    ):
        """
        Initialize Git daemon.
        
        Args:
            repo_path: Path to git repository
            check_interval: Seconds between checks (default: 5 minutes)
            auto_commit_threshold: Fitness threshold for auto-commit
            log_file: Path to log file
        """
        self.repo_path = repo_path
        self.check_interval = check_interval
        self.auto_commit_threshold = auto_commit_threshold
        self.running = False
        self.quiet_mode = quiet_mode
        
        # Setup logging
        if log_file:
            # For high-frequency checks, only log important events
            log_level = "WARNING" if check_interval <= 5 else "INFO"
            logger.add(
                log_file,
                rotation="1 day",
                retention="30 days",
                level=log_level,
            )
        
        # Create agent
        self.agent = AutonomousGitAgent(repo_path)
        
        # Stats
        self.stats = {
            "started_at": datetime.now().isoformat(),
            "checks_performed": 0,
            "commits_made": 0,
            "last_check": None,
            "last_commit": None,
        }
        
        logger.info("🤖 Git Daemon initialized")
        logger.info(f"   Repository: {repo_path}")
        logger.info(f"   Check interval: {check_interval}s")
        logger.info(f"   Auto-commit threshold: {auto_commit_threshold}")
    
    def start(self):
        """Start the daemon."""
        logger.info("\n🚀 Starting Git Daemon...")
        logger.info("   Daemon will run continuously")
        logger.info("   Press Ctrl+C to stop")
        
        self.running = True
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        
        # Main loop
        try:
            while self.running:
                self._check_and_commit()
                
                if self.running:  # Check again in case we're shutting down
                    logger.info(f"\n💤 Sleeping for {self.check_interval}s...")
                    time.sleep(self.check_interval)
        
        except Exception as e:
            logger.error(f"❌ Daemon error: {e}")
            raise
        
        finally:
            self._shutdown()
    
    def _check_and_commit(self):
        """Check repository and commit if fitness is high enough."""
        # Only log verbose info for slow intervals
        if not self.quiet_mode and self.check_interval > 5:
            logger.info("\n" + "=" * 70)
            logger.info(f"🔍 CHECK #{self.stats['checks_performed'] + 1}")
            logger.info(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info("=" * 70)
        
        self.stats["checks_performed"] += 1
        self.stats["last_check"] = datetime.now().isoformat()
        
        try:
            # Analyze changes
            analysis = self.agent.analyze_changes()
            
            if analysis["num_files"] == 0:
                # Don't log "no changes" for high-frequency checks
                if not self.quiet_mode and self.check_interval > 5:
                    logger.info("   No changes detected")
                return
            
            # Calculate fitness
            fitness = self.agent.calculate_commit_fitness(analysis)
            
            # ALWAYS show fitness when there are changes (continuous feedback!)
            logger.info(f"\n📊 FITNESS REPORT")
            logger.info(f"   Score: {fitness.score:.2f} / 1.00")
            logger.info(f"   Threshold: {self.auto_commit_threshold}")
            
            # Visual progress bar
            bar_length = 20
            filled = int(fitness.score * bar_length)
            bar = "█" * filled + "░" * (bar_length - filled)
            logger.info(f"   [{bar}] {fitness.score*100:.0f}%")
            
            # Show reasons
            if fitness.reasons:
                logger.info(f"\n   ✅ Strengths:")
                for reason in fitness.reasons:
                    logger.info(f"      • {reason}")
            
            # Show what's needed to improve
            if fitness.suggestions:
                logger.info(f"\n   💡 To improve fitness:")
                for suggestion in fitness.suggestions:
                    logger.info(f"      • {suggestion}")
            
            # Show distance to threshold
            if fitness.score < self.auto_commit_threshold:
                gap = self.auto_commit_threshold - fitness.score
                logger.info(f"\n   📈 Need +{gap:.2f} to auto-commit")
            
            # Should we commit?
            if fitness.score >= self.auto_commit_threshold:
                logger.success(f"\n✅ Fitness above threshold! Auto-committing...")
                
                # Commit
                success = self.agent.auto_commit(force=True)
                
                if success:
                    self.stats["commits_made"] += 1
                    self.stats["last_commit"] = datetime.now().isoformat()
                    
                    logger.success(f"\n🎉 Auto-commit #{self.stats['commits_made']} successful!")
                    
                    # Save stats
                    self._save_stats()
            
            else:
                logger.info(f"\n⏳ Fitness below threshold ({fitness.score:.2f} < {self.auto_commit_threshold})")
                logger.info("   Waiting for more changes...")
                
                # Show suggestions
                if fitness.suggestions:
                    logger.info("\n💡 Suggestions:")
                    for suggestion in fitness.suggestions:
                        logger.info(f"   • {suggestion}")
        
        except Exception as e:
            logger.error(f"❌ Check failed: {e}")
    
    def _save_stats(self):
        """Save daemon statistics."""
        stats_file = self.repo_path / ".git" / "daemon_stats.json"
        
        try:
            with open(stats_file, "w") as f:
                json.dump(self.stats, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save stats: {e}")
    
    def _handle_shutdown(self, signum, frame):
        """Handle shutdown signals."""
        logger.info("\n\n🛑 Shutdown signal received")
        self.running = False
    
    def _shutdown(self):
        """Clean shutdown."""
        logger.info("\n" + "=" * 70)
        logger.info("📊 DAEMON STATISTICS")
        logger.info("=" * 70)
        logger.info(f"   Started: {self.stats['started_at']}")
        logger.info(f"   Checks performed: {self.stats['checks_performed']}")
        logger.info(f"   Commits made: {self.stats['commits_made']}")
        
        if self.stats["last_commit"]:
            logger.info(f"   Last commit: {self.stats['last_commit']}")
        
        self._save_stats()
        
        logger.info("\n👋 Git Daemon stopped")


def create_launchd_plist(
    repo_path: Path,
    python_path: str,
    script_path: Path,
) -> str:
    """
    Create macOS LaunchAgent plist for auto-start on boot.
    
    Args:
        repo_path: Path to git repository
        python_path: Path to Python interpreter
        script_path: Path to this script
    
    Returns:
        Plist content
    """
    plist = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.salutations.git-daemon</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>{python_path}</string>
        <string>{script_path}</string>
        <string>--repo</string>
        <string>{repo_path}</string>
        <string>--daemon</string>
    </array>
    
    <key>RunAtLoad</key>
    <true/>
    
    <key>KeepAlive</key>
    <dict>
        <key>SuccessfulExit</key>
        <false/>
    </dict>
    
    <key>StandardOutPath</key>
    <string>{repo_path}/.git/daemon.log</string>
    
    <key>StandardErrorPath</key>
    <string>{repo_path}/.git/daemon.error.log</string>
    
    <key>WorkingDirectory</key>
    <string>{repo_path}</string>
    
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    </dict>
</dict>
</plist>
"""
    return plist


def install_service(repo_path: Path):
    """
    Install Git daemon as a system service (macOS LaunchAgent).
    
    Args:
        repo_path: Path to git repository
    """
    logger.info("\n🔧 Installing Git Daemon as system service...")
    
    # Get paths
    python_path = sys.executable
    script_path = Path(__file__).absolute()
    
    # Create plist
    plist_content = create_launchd_plist(repo_path, python_path, script_path)
    
    # Save plist
    launch_agents_dir = Path.home() / "Library" / "LaunchAgents"
    launch_agents_dir.mkdir(parents=True, exist_ok=True)
    
    plist_path = launch_agents_dir / "com.salutations.git-daemon.plist"
    plist_path.write_text(plist_content)
    
    logger.success(f"   ✓ Created plist: {plist_path}")
    
    # Load service
    import subprocess
    
    try:
        subprocess.run(
            ["launchctl", "load", str(plist_path)],
            check=True,
            capture_output=True,
        )
        logger.success("   ✓ Service loaded")
    except subprocess.CalledProcessError as e:
        logger.error(f"   ❌ Failed to load service: {e.stderr.decode()}")
        return
    
    logger.success("\n✅ Git Daemon installed!")
    logger.info("\n📋 Service details:")
    logger.info(f"   Name: com.salutations.git-daemon")
    logger.info(f"   Plist: {plist_path}")
    logger.info(f"   Logs: {repo_path}/.git/daemon.log")
    
    logger.info("\n🎮 Control commands:")
    logger.info("   Start:   launchctl start com.salutations.git-daemon")
    logger.info("   Stop:    launchctl stop com.salutations.git-daemon")
    logger.info("   Restart: launchctl restart com.salutations.git-daemon")
    logger.info("   Status:  launchctl list | grep git-daemon")
    logger.info("   Logs:    tail -f ~/.git/daemon.log")
    
    logger.info("\n🔄 The daemon will:")
    logger.info("   • Start automatically on boot")
    logger.info("   • Restart if it crashes")
    logger.info("   • Run in the background")
    logger.info("   • Commit when fitness is high")


def uninstall_service():
    """Uninstall Git daemon service."""
    logger.info("\n🗑️  Uninstalling Git Daemon service...")
    
    plist_path = Path.home() / "Library" / "LaunchAgents" / "com.salutations.git-daemon.plist"
    
    if not plist_path.exists():
        logger.warning("   Service not installed")
        return
    
    # Unload service
    import subprocess
    
    try:
        subprocess.run(
            ["launchctl", "unload", str(plist_path)],
            check=True,
            capture_output=True,
        )
        logger.success("   ✓ Service unloaded")
    except subprocess.CalledProcessError:
        pass  # May not be loaded
    
    # Remove plist
    plist_path.unlink()
    logger.success("   ✓ Plist removed")
    
    logger.success("\n✅ Git Daemon uninstalled!")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Git Daemon - Always-running autonomous Git")
    parser.add_argument("--repo", type=Path, default=Path.cwd(), help="Repository path")
    parser.add_argument("--interval", type=int, default=300, help="Check interval (seconds)")
    parser.add_argument("--threshold", type=float, default=0.7, help="Auto-commit threshold")
    parser.add_argument("--daemon", action="store_true", help="Run as daemon")
    parser.add_argument("--install", action="store_true", help="Install as system service")
    parser.add_argument("--uninstall", action="store_true", help="Uninstall system service")
    parser.add_argument("--realtime", action="store_true", help="Real-time mode (1s interval, optimized for AI agents)")
    parser.add_argument("--quiet", action="store_true", help="Quiet mode (minimal logging)")
    
    args = parser.parse_args()
    
    # Real-time mode overrides
    if args.realtime:
        args.interval = 1
        args.threshold = 0.6  # Lower threshold for AI agents
        args.quiet = True
        logger.info("⚡ Real-time mode enabled!")
        logger.info("   Interval: 1 second")
        logger.info("   Threshold: 0.6")
    
    if args.install:
        install_service(args.repo)
        return
    
    if args.uninstall:
        uninstall_service()
        return
    
    # Run daemon
    log_file = args.repo / ".git" / "daemon.log"
    
    daemon = GitDaemon(
        repo_path=args.repo,
        check_interval=args.interval,
        auto_commit_threshold=args.threshold,
        log_file=log_file,
        quiet_mode=args.quiet,
    )
    
    daemon.start()


if __name__ == "__main__":
    main()
