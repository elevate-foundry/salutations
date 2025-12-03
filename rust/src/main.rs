use anyhow::{Context, Result};
use clap::{Parser, Subcommand};
use colored::*;
use log::info;
use std::path::PathBuf;

mod agent;
mod braider;
mod fitness;
mod fitness_analyzer;
mod daemon;
mod scl;
mod bifm;
mod tests;

use agent::EntangledAgent;
use fitness_analyzer::FitnessReport;

/// Autonomous Git - Git that manages itself
#[derive(Parser)]
#[command(name = "agit")]
#[command(about = "Autonomous Git: Git that manages itself using AI", long_about = None)]
struct Cli {
    /// Path to git repository
    #[arg(short, long, default_value = ".")]
    repo: PathBuf,

    /// Check interval in seconds
    #[arg(short, long, default_value = "300")]
    interval: u64,

    /// Fitness threshold for auto-commit (0.0-1.0)
    #[arg(short, long, default_value = "0.7")]
    threshold: f32,

    /// Auto-push after commit
    #[arg(short, long)]
    push: bool,

    /// Use SCL (Semantic Compression Language) for commits
    #[arg(long)]
    scl: bool,

    /// Language for SCL rendering (en, es, zh, ja, fr, de, nl)
    #[arg(long, default_value = "en")]
    lang: String,

    #[command(subcommand)]
    command: Option<Commands>,
}

#[derive(Subcommand)]
enum Commands {
    /// Run the autonomous agent
    Run {
        /// Run in daemon mode
        #[arg(short, long)]
        daemon: bool,
    },
    /// Check current fitness score
    Check,
    /// Install as system service
    Install,
    /// Uninstall system service
    Uninstall,
    /// Show agent status
    Status,
}

#[tokio::main]
async fn main() -> Result<()> {
    env_logger::init();

    let cli = Cli::parse();

    print_banner();

    match cli.command {
        Some(Commands::Run { daemon }) => {
            if daemon {
                daemon::run_daemon(&cli.repo, cli.interval, cli.threshold)?;
            } else {
                run_agent(&cli.repo, cli.interval, cli.threshold, cli.push, cli.scl, &cli.lang).await?;
            }
        }
        Some(Commands::Check) => {
            check_fitness(&cli.repo).await?;
        }
        Some(Commands::Install) => {
            daemon::install_service(&cli.repo, cli.interval, cli.threshold)?;
        }
        Some(Commands::Uninstall) => {
            daemon::uninstall_service()?;
        }
        Some(Commands::Status) => {
            daemon::show_status(&cli.repo)?;
        }
        None => {
            // Default: run agent
            run_agent(&cli.repo, cli.interval, cli.threshold, cli.push, cli.scl, &cli.lang).await?;
        }
    }

    Ok(())
}

fn print_banner() {
    println!("{}", "═══════════════════════════════════════════════════════════".green());
    println!("{}", "   🤖 AUTONOMOUS GIT - Git That Manages Itself".green().bold());
    println!("{}", "═══════════════════════════════════════════════════════════".green());
    println!();
}

async fn run_agent(
    repo_path: &PathBuf,
    interval: u64,
    threshold: f32,
    auto_push: bool,
    scl_enabled: bool,
    language: &str,
) -> Result<()> {
    use crate::scl::Language;
    
    let lang = match language {
        "es" => Language::Spanish,
        "zh" => Language::Chinese,
        "ja" => Language::Japanese,
        "fr" => Language::French,
        "de" => Language::German,
        "nl" => Language::Dutch,
        _ => Language::English,
    };
    
    let mut agent = EntangledAgent::with_scl(repo_path, threshold, auto_push, scl_enabled, lang)
        .context("Failed to initialize agent")?;

    info!("Agent initialized");
    info!("Repository: {}", repo_path.display());
    info!("Check interval: {}s", interval);
    info!("Fitness threshold: {:.2}", threshold);
    info!("Auto-push: {}", if auto_push { "enabled" } else { "disabled" });
    info!("SCL: {}", if scl_enabled { "enabled" } else { "disabled" });
    if scl_enabled {
        info!("Language: {:?}", lang);
    }

    agent.run(interval).await
}

async fn check_fitness(repo_path: &PathBuf) -> Result<()> {
    let agent = EntangledAgent::new(repo_path, 0.7)?;
    
    println!("{}", "🔍 Analyzing current changes...".cyan());
    
    let analysis = agent.perceive()?;
    
    if analysis.is_empty() {
        println!("{}", "   No changes detected".yellow());
        return Ok(());
    }

    let report = agent.calculate_fitness(&analysis)?;

    println!("\n{}", "📊 FITNESS REPORT".purple().bold());
    println!("   Score: {:.2} / 1.00", report.final_score);
    println!("   Threshold: {:.2}", 0.70);
    
    // Visual progress bar
    let bar_length = 20;
    let filled = (report.final_score * bar_length as f32) as usize;
    let bar = "█".repeat(filled) + &"░".repeat(bar_length - filled);
    println!("   [{}] {:.0}%", bar, report.final_score * 100.0);

    println!("\n{}", "   Component Breakdown:".cyan());
    println!("     • File metrics: {:.2}", report.components.get("file_metrics").unwrap_or(&0.0));
    println!("     • Code complexity: {:.2}", report.components.get("complexity").unwrap_or(&0.0));
    println!("     • Coherence: {:.2}", report.components.get("coherence").unwrap_or(&0.0));
    println!("     • Tests: {:.2}", report.components.get("tests").unwrap_or(&0.0));
    println!("     • Risk: {:.2}", report.components.get("risk").unwrap_or(&0.0));
    println!("     • Documentation: {:.2}", report.components.get("documentation").unwrap_or(&0.0));

    if !report.reasons.is_empty() {
        println!("\n{}", "   Analysis:".cyan());
        for reason in &report.reasons {
            println!("   • {}", reason);
        }
    }
    
    if !report.suggestions.is_empty() {
        println!("\n{}", "   Suggestions:".yellow());
        for suggestion in &report.suggestions {
            println!("   💡 {}", suggestion);
        }
    }

    if report.final_score >= 0.7 {
        println!("\n{}", "✅ Ready to commit!".green().bold());
    } else {
        println!("\n{}", "⏳ Waiting for better fitness...".yellow());
    }

    Ok(())
}
