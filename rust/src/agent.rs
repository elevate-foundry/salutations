use anyhow::{Context, Result};
use chrono::Utc;
use colored::*;
use git2::{Repository, StatusOptions};
use log::info;
use std::collections::HashMap;
use std::path::{Path, PathBuf};
use tokio::time::{sleep, Duration};

use crate::braider::MetaBraider;
use crate::fitness::{FitnessHistory, HistoricalCommit};
use crate::scl::{SCLCommit, SemanticToken, LanguageRenderer, Language};
use crate::bifm::FitnessTopology;

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
    auto_push: bool,
    history: FitnessHistory,
    scl_enabled: bool,  // Use SCL for commits
    language: Language, // Preferred language for rendering
}

impl EntangledAgent {
    pub fn new(path: &PathBuf, threshold: f32) -> Result<Self> {
        Self::with_auto_push(path, threshold, false)
    }

    pub fn with_auto_push(path: &PathBuf, threshold: f32, auto_push: bool) -> Result<Self> {
        Self::with_scl(path, threshold, auto_push, false, Language::English)
    }

    pub fn with_scl(
        path: &PathBuf,
        threshold: f32,
        auto_push: bool,
        scl_enabled: bool,
        language: Language,
    ) -> Result<Self> {
        let repo = Repository::open(path).context("Failed to open git repo")?;
        let history = Self::load_history(path)?;
        
        Ok(Self {
            repo_path: path.clone(),
            repo,
            braider: MetaBraider::new(),
            fitness_threshold: threshold,
            commit_count: 0,
            ghost_mode_active: false,
            auto_push,
            history,
            scl_enabled,
            language,
        })
    }

    /// Load commit history from disk
    fn load_history(path: &PathBuf) -> Result<FitnessHistory> {
        let history_file = path.join(".git").join("agit_history.json");
        
        if history_file.exists() {
            let content = std::fs::read_to_string(&history_file)?;
            let history: FitnessHistory = serde_json::from_str(&content)?;
            info!("Loaded {} commits from history", history.commits.len());
            Ok(history)
        } else {
            Ok(FitnessHistory::new())
        }
    }

    /// Save commit history to disk
    fn save_history(&self) -> Result<()> {
        let history_file = self.repo_path.join(".git").join("agit_history.json");
        let content = serde_json::to_string_pretty(&self.history)?;
        std::fs::write(&history_file, content)?;
        Ok(())
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
        
        // Adjust based on historical learning
        let adjusted_fitness = if self.history.commits.len() > 5 {
            let avg_files = self.history.average_file_count();
            let current_files = diff.lines().count();
            
            // Bonus if similar to historical patterns
            let file_similarity = 1.0 - ((current_files as f32 - avg_files).abs() / avg_files.max(1.0));
            let learning_bonus = file_similarity * 0.05;
            
            (fitness + learning_bonus).min(1.0)
        } else {
            fitness
        };
        
        Ok((adjusted_fitness, reasoning, breakdown))
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
        if self.scl_enabled {
            self.generate_scl_message(diff)
        } else {
            self.generate_traditional_message(diff)
        }
    }

    /// Generate SCL commit message
    fn generate_scl_message(&self, diff: &str) -> Result<String> {
        // Extract semantic tokens from changes
        let tokens = self.extract_semantic_tokens(diff);
        
        // Calculate fitness topology
        let fitness = self.calculate_fitness_topology(diff)?;
        
        // Create SCL commit with fitness
        let scl_commit = SCLCommit::with_fitness(
            tokens,
            "autonomous-agent".to_string(),
            Some(fitness),
        );
        
        // Render in preferred language
        let renderer = LanguageRenderer::new();
        let message = renderer.render(&scl_commit, self.language);
        
        // Show Braille FIRST (native format)
        println!("\n{} {}", "🔤".cyan(), scl_commit.braille);
        println!("{} {} translation: {}", "🌍".cyan(), format!("{:?}", self.language), message);
        
        // Show fitness topology
        println!("{} κ={} σ={} δ={} ({})", 
            "📊".purple(),
            fitness.kappa, fitness.sigma, fitness.delta,
            fitness.interpret());
        
        Ok(format!("{}\n\nSCL: {}", scl_commit.braille, message))
    }
    
    /// Calculate fitness topology from diff
    fn calculate_fitness_topology(&self, diff: &str) -> Result<FitnessTopology> {
        let lines: Vec<&str> = diff.lines().collect();
        let file_count = lines.len();
        
        // Estimate line changes (rough heuristic)
        let line_changes = file_count * 50; // Assume ~50 lines per file
        
        // Check for tests
        let has_tests = diff.contains("test");
        
        // Check for breaking changes
        let has_breaking = diff.contains("BREAKING") 
            || diff.contains("breaking")
            || diff.contains("!:");
        
        // Get current fitness score
        let (fitness_score, _, _) = self.braider.braid(diff);
        
        Ok(FitnessTopology::from_analysis(
            file_count,
            line_changes,
            has_tests,
            has_breaking,
            fitness_score,
        ))
    }

    /// Extract semantic tokens from diff
    fn extract_semantic_tokens(&self, diff: &str) -> Vec<SemanticToken> {
        let mut tokens = Vec::new();
        
        // Analyze what changed
        let has_test = diff.contains("test");
        let has_doc = diff.contains(".md");
        let has_auth = diff.contains("auth");
        let has_security = diff.contains("security") || diff.contains("sec");
        let has_perf = diff.contains("perf") || diff.contains("performance");
        let has_fix = diff.contains("fix") || diff.contains("bug");
        let has_new = diff.contains("NEW:");
        let has_refactor = diff.contains("refactor");
        
        // Determine action
        if has_fix {
            tokens.push(SemanticToken::Fix);
        } else if has_new {
            tokens.push(SemanticToken::Add);
        } else if has_refactor {
            tokens.push(SemanticToken::Refactor);
        } else {
            tokens.push(SemanticToken::Update);
        }
        
        // Determine domain
        if has_auth {
            tokens.push(SemanticToken::Authentication);
        } else if has_security {
            tokens.push(SemanticToken::Security);
        } else if has_perf {
            tokens.push(SemanticToken::Performance);
        } else if has_test {
            tokens.push(SemanticToken::Testing);
        } else if has_doc {
            tokens.push(SemanticToken::Documentation);
        } else {
            tokens.push(SemanticToken::Feature);
        }
        
        // Add modifiers
        if diff.contains("edge") || diff.contains("corner") {
            tokens.push(SemanticToken::EdgeCase);
        }
        
        if diff.contains("enhance") || diff.contains("improve") {
            tokens.push(SemanticToken::Enhancement);
        }
        
        tokens
    }

    /// Generate traditional commit message
    fn generate_traditional_message(&self, diff: &str) -> Result<String> {
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
    pub fn execute_commit(&mut self, message: &str, analysis: &str) -> Result<()> {
        // Clone what we need for learning
        let message_clone = message.to_string();
        let analysis_clone = analysis.to_string();
        
        // Do all git operations in a scope to release borrows
        {
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
        } // All repo borrows released here

        self.commit_count += 1;

        println!(
            "{} {}",
            "🚀 COMMITTED:".green().bold(),
            message.bright_white()
        );
        println!("   {} Total commits: {}", "📊".cyan(), self.commit_count);

        // Learn from this commit (now safe to borrow mutably)
        self.learn_from_commit(&message_clone, &analysis_clone)?;

        // Auto-push if enabled
        if self.auto_push {
            self.execute_push()?;
        }

        Ok(())
    }

    /// Learn from a commit to improve future decisions
    fn learn_from_commit(&mut self, message: &str, analysis: &str) -> Result<()> {
        use chrono::Utc;

        // Calculate fitness for this commit
        let (fitness, _, _) = self.braider.braid(analysis);
        
        // Count files
        let file_count = analysis.lines().count();

        // Add to history
        let commit = HistoricalCommit {
            timestamp: Utc::now().to_rfc3339(),
            fitness,
            file_count,
            message: message.to_string(),
        };

        self.history.add_commit(commit);

        // Save history
        self.save_history()?;

        // Show learning stats every 10 commits
        if self.history.commits.len() % 10 == 0 {
            self.show_learning_stats();
        }

        Ok(())
    }

    /// Show what the agent has learned
    fn show_learning_stats(&self) {
        println!("\n{}", "📚 LEARNING STATS".purple().bold());
        println!("   Total commits: {}", self.history.commits.len());
        println!("   Average fitness: {:.2}", self.history.average_fitness());
        println!("   Average files/commit: {:.1}", self.history.average_file_count());
        
        // Suggest threshold adjustment
        let avg_fitness = self.history.average_fitness();
        if avg_fitness > self.fitness_threshold + 0.1 {
            println!("   {} Consider raising threshold to {:.2}", 
                "💡".yellow(), avg_fitness - 0.05);
        } else if avg_fitness < self.fitness_threshold - 0.1 {
            println!("   {} Consider lowering threshold to {:.2}", 
                "💡".yellow(), avg_fitness + 0.05);
        }
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

                        let diff_clone = diff.clone();
                        match self.decide(&diff)? {
                            AgentAction::Commit(msg) => {
                                if let Err(e) = self.execute_commit(&msg, &diff_clone) {
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
