use anyhow::{Context, Result};
use clap::{Parser, Subcommand};
use colored::*;
use log::info;
use std::path::PathBuf;

mod agent;
mod braider;
mod fitness;
mod daemon;
mod scl;
mod bifm;

use agent::EntangledAgent;

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

    /// Language for SCL rendering (en, es, zh, ja, fr, de)
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

    let (fitness, reasoning, breakdown) = agent.calculate_fitness(&analysis)?;

    println!("\n{}", "📊 FITNESS REPORT".purple().bold());
    println!("   Score: {:.2} / 1.00", fitness);
    println!("   Threshold: 0.70");
    
    // Visual progress bar
    let bar_length = 20;
    let filled = (fitness * bar_length as f32) as usize;
    let bar = "█".repeat(filled) + &"░".repeat(bar_length - filled);
    println!("   [{}] {:.0}%", bar, fitness * 100.0);

    println!("\n{}", "   Breakdown:".cyan());
    for (factor, score) in breakdown {
        println!("     • {}: {:.2}", factor, score);
    }

    println!("\n{}", "   Reasoning:".cyan());
    println!("     {}", reasoning);

    if fitness >= 0.7 {
        println!("\n{}", "✅ Ready to commit!".green().bold());
    } else {
        println!("\n{}", "⏳ Waiting for better fitness...".yellow());
    }

    Ok(())
}
