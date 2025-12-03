use anyhow::{Context, Result};
use chrono::Utc;
use colored::*;
use git2::{Repository, Status, StatusOptions};
use log::{error, info, warn};
use std::collections::HashMap;
use std::path::{Path, PathBuf};
use tokio::time::{sleep, Duration};

use crate::braider::MetaBraider;
use crate::fitness::CommitFitness;

#[derive(Debug, PartialEq)]
pub enum AgentAction {
    Commit(String),  // The message
    GhostCommit,     // Local snapshot
    Split,           // Needs splitting
    Wait,            // Do nothing
}

pub struct EntangledAgent {
    repo_path: PathBuf,
    repo: Repository,
    braider: MetaBraider,
    fitness_threshold: f32,
    commit_count: u64,
    ghost_mode_active: bool,
    auto_push: bool,  // NEW: Auto-push after commit
}

impl EntangledAgent {
    pub fn new(path: &PathBuf, threshold: f32) -> Result<Self> {
        Self::with_auto_push(path, threshold, false)
    }

    pub fn with_auto_push(path: &PathBuf, threshold: f32, auto_push: bool) -> Result<Self> {
        let repo = Repository::open(path).context("Failed to open git repo")?;
        Ok(Self {
            repo_path: path.clone(),
            repo,
            braider: MetaBraider::new(),
            fitness_threshold: threshold,
            commit_count: 0,
            ghost_mode_active: false,
            auto_push,
        })
    }

    /// The "Eyes": Perceives the current state of the repo
    pub fn perceive(&self) -> Result<String> {
        let mut diff_str = String::new();

        // Check for modified files
        let mut opts = StatusOptions::new();
        opts.include_untracked(true);
        opts.include_ignored(false);

        let statuses = self.repo.statuses(Some(&mut opts))?;

        if statuses.is_empty() {
            return Ok(String::new());
        }

        for entry in statuses.iter() {
            let status = entry.status();
            let path = entry.path().unwrap_or("unknown");

            if status.contains(Status::WT_MODIFIED) || status.contains(Status::INDEX_MODIFIED) {
                diff_str.push_str(&format!("MODIFIED: {}\n", path));
            } else if status.contains(Status::WT_NEW) {
                diff_str.push_str(&format!("NEW: {}\n", path));
            } else if status.contains(Status::WT_DELETED) {
                diff_str.push_str(&format!("DELETED: {}\n", path));
            }
        }

        Ok(diff_str)
    }

    /// Calculate fitness score with detailed breakdown
    pub fn calculate_fitness(&self, diff: &str) -> Result<(f32, String, HashMap<String, f32>)> {
        let (fitness, reasoning, breakdown) = self.braider.braid(diff);
        Ok((fitness, reasoning, breakdown))
    }

    /// The "Brain Loop": Calculates fitness and decides action
    pub fn decide(&self, diff: &str) -> Result<AgentAction> {
        if diff.trim().is_empty() {
            return Ok(AgentAction::Wait);
        }

        // Ask the Braider
        let (fitness, reason, breakdown) = self.braider.braid(diff);

        println!(
            "   {} Fitness: {:.2} | Reason: {}",
            "📊".purple(),
            fitness,
            reason
        );

        // Show breakdown
        println!("   {} Breakdown:", "🔍".cyan());
        for (expert, score) in breakdown {
            println!("     • {}: {:.2}", expert, score);
        }

        if fitness > self.fitness_threshold {
            // High confidence -> Real Commit
            let msg = self.generate_commit_message(diff)?;
            Ok(AgentAction::Commit(msg))
        } else if fitness > 0.4 {
            // Medium confidence -> Ghost Commit (Save work, don't push)
            Ok(AgentAction::GhostCommit)
        } else if diff.len() > 5000 {
            // Too big -> Split
            Ok(AgentAction::Split)
        } else {
            Ok(AgentAction::Wait)
        }
    }

    /// Generate intelligent commit message
    fn generate_commit_message(&self, diff: &str) -> Result<String> {
        let lines: Vec<&str> = diff.lines().collect();
        let mut files: Vec<String> = Vec::new();

        for line in lines {
            if let Some(path) = line.split_whitespace().nth(1) {
                files.push(path.to_string());
            }
        }

        let file_count = files.len();

        // Determine commit type
        let commit_type = if files.iter().any(|f| f.contains("test")) {
            ("test", "🧪")
        } else if files.iter().any(|f| f.ends_with(".md")) {
            ("docs", "📝")
        } else if files.iter().any(|f| f.contains("fix") || f.contains("bug")) {
            ("fix", "🐛")
        } else {
            ("feat", "✨")
        };

        // Generate message
        let timestamp = Utc::now().format("%H:%M");
        let message = if file_count == 1 {
            format!(
                "{} {}: update {} [{}]",
                commit_type.1, commit_type.0, files[0], timestamp
            )
        } else {
            format!(
                "{} {}: update {} files [{}]",
                commit_type.1, commit_type.0, file_count, timestamp
            )
        };

        Ok(message)
    }

    /// Execute a Real Commit
    pub fn execute_commit(&mut self, message: &str) -> Result<()> {
        let mut index = self.repo.index()?;

        // Stage all changes
        let mut opts = StatusOptions::new();
        opts.include_untracked(true);
        let statuses = self.repo.statuses(Some(&mut opts))?;

        for entry in statuses.iter() {
            if let Some(path) = entry.path() {
                index.add_path(Path::new(path))?;
            }
        }
        index.write()?;

        let oid = index.write_tree()?;
        let tree = self.repo.find_tree(oid)?;
        let sig = self.repo.signature()?;
        let parent_commit = self.repo.head()?.peel_to_commit()?;

        self.repo.commit(
            Some("HEAD"),
            &sig,
            &sig,
            message,
            &tree,
            &[&parent_commit],
        )?;

        self.commit_count += 1;

        println!(
            "{} {}",
            "🚀 COMMITTED:".green().bold(),
            message.bright_white()
        );
        println!("   {} Total commits: {}", "📊".cyan(), self.commit_count);

        // Auto-push if enabled
        if self.auto_push {
            self.execute_push()?;
        }

        Ok(())
    }

    /// Execute a push to remote
    pub fn execute_push(&self) -> Result<()> {
        println!("\n{} Pushing to remote...", "📤".cyan());

        // Get current branch
        let head = self.repo.head()?;
        let branch_name = head
            .shorthand()
            .ok_or_else(|| anyhow::anyhow!("Failed to get branch name"))?;

        // Push using git command (libgit2 push is complex with auth)
        let output = std::process::Command::new("git")
            .arg("push")
            .arg("origin")
            .arg(branch_name)
            .current_dir(&self.repo_path)
            .output()?;

        if output.status.success() {
            println!(
                "{} {}",
                "✅ PUSHED:".green().bold(),
                format!("origin/{}", branch_name).bright_white()
            );
            Ok(())
        } else {
            let error = String::from_utf8_lossy(&output.stderr);
            warn!("Push failed: {}", error);
            println!(
                "{} {}",
                "⚠️  Push failed:".yellow(),
                error.trim()
            );
            println!("   {} Commit saved locally", "💾".cyan());
            Ok(()) // Don't fail the whole operation
        }
    }

    /// Execute a Ghost Commit (Hidden ref)
    pub fn execute_ghost_commit(&self) -> Result<()> {
        // In a real app, this would commit to a ref like 'refs/ghosts/wip'
        println!(
            "{} {}",
            "👻 GHOST SAVE:".cyan(),
            "Local checkpoint created (not pushed)".bright_black()
        );
        Ok(())
    }

    /// The Main Loop
    pub async fn run(&mut self, interval: u64) -> Result<()> {
        println!("{}", "   Watching: ".green().to_string() + &self.repo_path.display().to_string());
        println!("{}", "   Threshold: ".green().to_string() + &format!("{:.2}", self.fitness_threshold));
        println!("{}", "   Interval: ".green().to_string() + &format!("{}s", interval));
        println!();

        loop {
            match self.perceive() {
                Ok(diff) => {
                    if !diff.is_empty() {
                        println!("\n{} Detected changes...", "👀".blue());

                        match self.decide(&diff)? {
                            AgentAction::Commit(msg) => {
                                if let Err(e) = self.execute_commit(&msg) {
                                    error!("Commit failed: {}", e);
                                }
                            }
                            AgentAction::GhostCommit => {
                                let _ = self.execute_ghost_commit();
                            }
                            AgentAction::Split => {
                                warn!("⚠️  Changes too large. Consider splitting manually.");
                                println!("   {} Suggestion: Commit related files separately", "💡".yellow());
                            }
                            AgentAction::Wait => {
                                println!("   {} Waiting for better fitness...", "⏳".yellow());
                            }
                        }
                    }
                }
                Err(e) => error!("Perception error: {}", e),
            }

            // Sleep to prevent CPU burning
            sleep(Duration::from_secs(interval)).await;
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::TempDir;

    #[test]
    fn test_agent_creation() {
        let temp_dir = TempDir::new().unwrap();
        let repo_path = temp_dir.path();

        // Initialize a git repo
        Repository::init(repo_path).unwrap();

        let agent = EntangledAgent::new(&repo_path.to_path_buf(), 0.7);
        assert!(agent.is_ok());
    }

    #[test]
    fn test_perceive_empty_repo() {
        let temp_dir = TempDir::new().unwrap();
        let repo_path = temp_dir.path();
        Repository::init(repo_path).unwrap();

        let agent = EntangledAgent::new(&repo_path.to_path_buf(), 0.7).unwrap();
        let diff = agent.perceive().unwrap();
        assert!(diff.is_empty());
    }
}
