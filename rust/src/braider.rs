use ndarray::{Array1, Array2};
use std::collections::HashMap;

/// Represents the "Hidden State" of an LLM (a vector of floating point numbers).
pub type HiddenState = Array1<f32>;

/// A trait for our Expert Models (CodeLlama, Mistral, etc.)
pub trait ExpertModel: Send + Sync {
    fn name(&self) -> &str;
    /// Simulates a forward pass, returning a "Thought Vector" (Hidden State)
    fn forward(&self, input: &str) -> HiddenState;
}

/// Syntax Expert: Analyzes code structure and quality
pub struct SyntaxExpert;

impl ExpertModel for SyntaxExpert {
    fn name(&self) -> &str {
        "CodeLlama-7B-Syntax"
    }

    fn forward(&self, input: &str) -> HiddenState {
        let mut state = Array1::zeros(128);

        // Analyze syntax quality
        let has_todos = input.contains("TODO") || input.contains("FIXME");
        let has_warnings = input.contains("HACK") || input.contains("XXX");
        let has_tests = input.contains("test_") || input.contains("Test");
        let has_docs = input.contains("///") || input.contains("/**");

        if has_todos || has_warnings {
            state.fill(-0.8); // Distress signal
        } else if has_tests && has_docs {
            state.fill(0.9); // High quality
        } else if has_tests || has_docs {
            state.fill(0.6); // Good
        } else {
            state.fill(0.3); // Neutral
        }

        state
    }
}

/// Logic Expert: Analyzes change complexity and coherence
pub struct LogicExpert;

impl ExpertModel for LogicExpert {
    fn name(&self) -> &str {
        "Mistral-7B-Logic"
    }

    fn forward(&self, input: &str) -> HiddenState {
        let mut state = Array1::zeros(128);

        // Analyze complexity
        let line_count = input.lines().count();
        let file_count = input.matches("MODIFIED:").count() + input.matches("NEW:").count();

        // Sweet spot: 3-7 files, moderate changes
        let complexity = if (3..=7).contains(&file_count) {
            0.8 // Optimal
        } else if file_count < 3 {
            0.4 // Too small
        } else {
            0.3 // Too large
        };

        state.fill(complexity);
        state
    }
}

/// Semantic Expert: Analyzes semantic coherence
pub struct SemanticExpert;

impl ExpertModel for SemanticExpert {
    fn name(&self) -> &str {
        "Llama-3.1-Semantic"
    }

    fn forward(&self, input: &str) -> HiddenState {
        let mut state = Array1::zeros(128);

        // Analyze semantic patterns
        let lines: Vec<&str> = input.lines().collect();
        let mut paths: Vec<&str> = Vec::new();

        for line in lines {
            if line.starts_with("MODIFIED:") || line.starts_with("NEW:") {
                if let Some(path) = line.split_whitespace().nth(1) {
                    paths.push(path);
                }
            }
        }

        // Check coherence: are files related?
        let coherence = if paths.is_empty() {
            0.0
        } else {
            // Simple heuristic: files in same directory = coherent
            let dirs: Vec<_> = paths
                .iter()
                .filter_map(|p| p.rsplit_once('/').map(|(d, _)| d))
                .collect();

            let unique_dirs = dirs.iter().collect::<std::collections::HashSet<_>>().len();

            if unique_dirs <= 2 {
                0.9 // Highly coherent
            } else if unique_dirs <= 4 {
                0.6 // Moderately coherent
            } else {
                0.3 // Scattered
            }
        };

        state.fill(coherence);
        state
    }
}

/// The Fusion Layer: Entangles the states of multiple experts.
pub struct MetaBraider {
    experts: Vec<Box<dyn ExpertModel>>,
    attention_weights: Array1<f32>,
}

impl MetaBraider {
    pub fn new() -> Self {
        Self {
            experts: vec![
                Box::new(SyntaxExpert),
                Box::new(LogicExpert),
                Box::new(SemanticExpert),
            ],
            // Initialize with equal trust
            attention_weights: Array1::from_vec(vec![0.33, 0.33, 0.34]),
        }
    }

    /// The Core "Entanglement" Function
    /// Fuses the hidden states of experts into a single decision vector.
    pub fn braid(&self, diff: &str) -> (f32, String, HashMap<String, f32>) {
        let mut states = Vec::new();
        let mut breakdown = HashMap::new();

        // 1. Parallel Forward Pass (Collect Thoughts)
        for expert in &self.experts {
            let state = expert.forward(diff);
            let energy = state.mean().unwrap_or(0.0);
            breakdown.insert(expert.name().to_string(), energy);
            states.push(state);
        }

        // 2. Fusion (Weighted Attention)
        // Output = (StateA * WeightA) + (StateB * WeightB) + (StateC * WeightC)
        let mut fused_state = Array1::zeros(128);

        for (i, state) in states.iter().enumerate() {
            let weight = self.attention_weights[i];
            fused_state = fused_state + (state * weight);
        }

        // 3. Decode Decision (Simple Classification Head)
        let energy = fused_state.mean().unwrap_or(0.0);

        // Sigmoid activation to get 0.0 - 1.0
        let fitness_score = 1.0 / (1.0 + (-energy).exp());

        let reasoning = if fitness_score > 0.8 {
            "High semantic cohesion, valid syntax, and optimal complexity.".to_string()
        } else if fitness_score > 0.6 {
            "Good changes, but could be improved with tests or docs.".to_string()
        } else if fitness_score > 0.4 {
            "Changes are ambiguous; waiting for more context.".to_string()
        } else {
            "Detected syntax issues, incomplete logic, or poor coherence.".to_string()
        };

        (fitness_score, reasoning, breakdown)
    }

    /// Update attention weights based on learning
    pub fn update_weights(&mut self, feedback: &[f32]) {
        if feedback.len() == self.attention_weights.len() {
            // Simple gradient descent
            let learning_rate = 0.1;
            for (i, &fb) in feedback.iter().enumerate() {
                self.attention_weights[i] += learning_rate * fb;
            }

            // Normalize to sum to 1.0
            let sum: f32 = self.attention_weights.sum();
            self.attention_weights /= sum;
        }
    }
}

impl Default for MetaBraider {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_syntax_expert() {
        let expert = SyntaxExpert;
        let state = expert.forward("TODO: fix this");
        assert!(state.mean().unwrap() < 0.0);

        let state = expert.forward("fn test_feature() { }");
        assert!(state.mean().unwrap() > 0.0);
    }

    #[test]
    fn test_logic_expert() {
        let expert = LogicExpert;
        let input = "MODIFIED: file1.rs\nMODIFIED: file2.rs\nMODIFIED: file3.rs";
        let state = expert.forward(input);
        assert!(state.mean().unwrap() > 0.5);
    }

    #[test]
    fn test_meta_braider() {
        let braider = MetaBraider::new();
        let diff = "MODIFIED: src/main.rs\nMODIFIED: src/lib.rs";
        let (fitness, _, _) = braider.braid(diff);
        assert!(fitness >= 0.0 && fitness <= 1.0);
    }
}
