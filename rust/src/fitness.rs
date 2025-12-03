use serde::{Deserialize, Serialize};
use std::collections::HashMap;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CommitFitness {
    pub score: f32,
    pub reasons: Vec<String>,
    pub suggestions: Vec<String>,
    pub breakdown: HashMap<String, f32>,
    pub confidence: f32,
}

impl CommitFitness {
    pub fn new(score: f32) -> Self {
        Self {
            score,
            reasons: Vec::new(),
            suggestions: Vec::new(),
            breakdown: HashMap::new(),
            confidence: 1.0,
        }
    }

    pub fn add_reason(&mut self, reason: String) {
        self.reasons.push(reason);
    }

    pub fn add_suggestion(&mut self, suggestion: String) {
        self.suggestions.push(suggestion);
    }

    pub fn set_breakdown(&mut self, breakdown: HashMap<String, f32>) {
        self.breakdown = breakdown;
    }

    pub fn should_commit(&self, threshold: f32) -> bool {
        self.score >= threshold
    }
}

#[derive(Debug, Serialize, Deserialize)]
pub struct FitnessHistory {
    pub commits: Vec<HistoricalCommit>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct HistoricalCommit {
    pub timestamp: String,
    pub fitness: f32,
    pub file_count: usize,
    pub message: String,
}

impl FitnessHistory {
    pub fn new() -> Self {
        Self {
            commits: Vec::new(),
        }
    }

    pub fn add_commit(&mut self, commit: HistoricalCommit) {
        self.commits.push(commit);
        
        // Keep only last 100 commits
        if self.commits.len() > 100 {
            self.commits.remove(0);
        }
    }

    pub fn average_fitness(&self) -> f32 {
        if self.commits.is_empty() {
            return 0.0;
        }

        let sum: f32 = self.commits.iter().map(|c| c.fitness).sum();
        sum / self.commits.len() as f32
    }

    pub fn average_file_count(&self) -> f32 {
        if self.commits.is_empty() {
            return 0.0;
        }

        let sum: usize = self.commits.iter().map(|c| c.file_count).sum();
        sum as f32 / self.commits.len() as f32
    }
}

impl Default for FitnessHistory {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_commit_fitness() {
        let mut fitness = CommitFitness::new(0.85);
        fitness.add_reason("Good file count".to_string());
        fitness.add_suggestion("Add tests".to_string());

        assert_eq!(fitness.score, 0.85);
        assert_eq!(fitness.reasons.len(), 1);
        assert_eq!(fitness.suggestions.len(), 1);
    }

    #[test]
    fn test_should_commit() {
        let fitness = CommitFitness::new(0.75);
        assert!(fitness.should_commit(0.7));
        assert!(!fitness.should_commit(0.8));
    }

    #[test]
    fn test_fitness_history() {
        let mut history = FitnessHistory::new();
        
        history.add_commit(HistoricalCommit {
            timestamp: "2025-12-02T21:00:00".to_string(),
            fitness: 0.8,
            file_count: 5,
            message: "test commit".to_string(),
        });

        assert_eq!(history.commits.len(), 1);
        assert_eq!(history.average_fitness(), 0.8);
        assert_eq!(history.average_file_count(), 5.0);
    }
}
