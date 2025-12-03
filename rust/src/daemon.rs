use anyhow::{Context, Result};
use colored::*;
use std::fs;
use std::path::PathBuf;

pub fn run_daemon(repo_path: &PathBuf, interval: u64, threshold: f32) -> Result<()> {
    println!("{}", "🔧 Daemon mode not yet implemented".yellow());
    println!("   Use: agit run --repo {} --interval {} --threshold {}", 
        repo_path.display(), interval, threshold);
    println!("   This will run in foreground for now.");
    Ok(())
}

pub fn install_service(repo_path: &PathBuf, interval: u64, threshold: f32) -> Result<()> {
    println!("{}", "═══════════════════════════════════════".green());
    println!("{}", "   Installing Autonomous Git Service".green().bold());
    println!("{}", "═══════════════════════════════════════".green());
    println!();

    #[cfg(target_os = "macos")]
    {
        install_launchd_service(repo_path, interval, threshold)?;
    }

    #[cfg(target_os = "linux")]
    {
        install_systemd_service(repo_path, interval, threshold)?;
    }

    #[cfg(not(any(target_os = "macos", target_os = "linux")))]
    {
        println!("{}", "❌ Service installation not supported on this platform".red());
        println!("   Run manually with: agit run");
    }

    Ok(())
}

#[cfg(target_os = "macos")]
fn install_launchd_service(repo_path: &PathBuf, interval: u64, threshold: f32) -> Result<()> {
    use std::env;

    let home = env::var("HOME").context("HOME not set")?;
    let launch_agents = PathBuf::from(home).join("Library/LaunchAgents");
    fs::create_dir_all(&launch_agents)?;

    let plist_path = launch_agents.join("com.autonomousgit.agent.plist");
    let agit_path = env::current_exe()?;

    let plist_content = format!(
        r#"<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.autonomousgit.agent</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>{}</string>
        <string>run</string>
        <string>--repo</string>
        <string>{}</string>
        <string>--interval</string>
        <string>{}</string>
        <string>--threshold</string>
        <string>{}</string>
    </array>
    
    <key>RunAtLoad</key>
    <true/>
    
    <key>KeepAlive</key>
    <dict>
        <key>SuccessfulExit</key>
        <false/>
    </dict>
    
    <key>StandardOutPath</key>
    <string>{}/.git/agit.log</string>
    
    <key>StandardErrorPath</key>
    <string>{}/.git/agit.error.log</string>
    
    <key>WorkingDirectory</key>
    <string>{}</string>
</dict>
</plist>
"#,
        agit_path.display(),
        repo_path.display(),
        interval,
        threshold,
        repo_path.display(),
        repo_path.display(),
        repo_path.display()
    );

    fs::write(&plist_path, plist_content)?;

    println!("{} Created plist: {}", "✓".green(), plist_path.display());
    println!();
    println!("{}", "To start the service:".cyan());
    println!("  launchctl load {}", plist_path.display());
    println!();
    println!("{}", "To stop the service:".cyan());
    println!("  launchctl unload {}", plist_path.display());
    println!();
    println!("{}", "To view logs:".cyan());
    println!("  tail -f {}/.git/agit.log", repo_path.display());

    Ok(())
}

#[cfg(target_os = "linux")]
fn install_systemd_service(repo_path: &PathBuf, interval: u64, threshold: f32) -> Result<()> {
    use std::env;

    let home = env::var("HOME").context("HOME not set")?;
    let systemd_user = PathBuf::from(home).join(".config/systemd/user");
    fs::create_dir_all(&systemd_user)?;

    let service_path = systemd_user.join("autonomous-git.service");
    let agit_path = env::current_exe()?;

    let service_content = format!(
        r#"[Unit]
Description=Autonomous Git Agent
After=network.target

[Service]
Type=simple
ExecStart={} run --repo {} --interval {} --threshold {}
Restart=always
RestartSec=10
WorkingDirectory={}
StandardOutput=append:{}/.git/agit.log
StandardError=append:{}/.git/agit.error.log

[Install]
WantedBy=default.target
"#,
        agit_path.display(),
        repo_path.display(),
        interval,
        threshold,
        repo_path.display(),
        repo_path.display(),
        repo_path.display()
    );

    fs::write(&service_path, service_content)?;

    println!("{} Created service: {}", "✓".green(), service_path.display());
    println!();
    println!("{}", "To start the service:".cyan());
    println!("  systemctl --user start autonomous-git");
    println!("  systemctl --user enable autonomous-git");
    println!();
    println!("{}", "To stop the service:".cyan());
    println!("  systemctl --user stop autonomous-git");
    println!();
    println!("{}", "To view logs:".cyan());
    println!("  journalctl --user -u autonomous-git -f");

    Ok(())
}

pub fn uninstall_service() -> Result<()> {
    println!("{}", "═══════════════════════════════════════".yellow());
    println!("{}", "   Uninstalling Autonomous Git Service".yellow().bold());
    println!("{}", "═══════════════════════════════════════".yellow());
    println!();

    #[cfg(target_os = "macos")]
    {
        use std::env;
        let home = env::var("HOME").context("HOME not set")?;
        let plist_path = PathBuf::from(home)
            .join("Library/LaunchAgents/com.autonomousgit.agent.plist");

        if plist_path.exists() {
            fs::remove_file(&plist_path)?;
            println!("{} Removed: {}", "✓".green(), plist_path.display());
        } else {
            println!("{} Service not found", "ℹ".blue());
        }
    }

    #[cfg(target_os = "linux")]
    {
        use std::env;
        let home = env::var("HOME").context("HOME not set")?;
        let service_path = PathBuf::from(home)
            .join(".config/systemd/user/autonomous-git.service");

        if service_path.exists() {
            fs::remove_file(&service_path)?;
            println!("{} Removed: {}", "✓".green(), service_path.display());
        } else {
            println!("{} Service not found", "ℹ".blue());
        }
    }

    Ok(())
}

pub fn show_status(repo_path: &PathBuf) -> Result<()> {
    println!("{}", "═══════════════════════════════════════".cyan());
    println!("{}", "   Autonomous Git Status".cyan().bold());
    println!("{}", "═══════════════════════════════════════".cyan());
    println!();

    println!("{} Repository: {}", "📁".cyan(), repo_path.display());

    // Check if logs exist
    let log_path = repo_path.join(".git/agit.log");
    if log_path.exists() {
        println!("{} Log file: {}", "📝".cyan(), log_path.display());
        
        // Show last 10 lines
        if let Ok(content) = fs::read_to_string(&log_path) {
            let lines: Vec<&str> = content.lines().rev().take(10).collect();
            println!("\n{}", "Recent activity:".yellow());
            for line in lines.iter().rev() {
                println!("  {}", line);
            }
        }
    } else {
        println!("{} No activity logs found", "ℹ".blue());
    }

    Ok(())
}
