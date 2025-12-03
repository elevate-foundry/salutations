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

        // Count different quality indicators
        let lines: Vec<&str> = input.lines().collect();
        let total_lines = lines.len().max(1) as f32;
        
        // Negative indicators
        let todo_count = input.matches("TODO").count() + input.matches("FIXME").count();
        let warning_count = input.matches("HACK").count() + input.matches("XXX").count();
        
        // Positive indicators
        let test_count = input.matches("test").count() + input.matches("Test").count();
        let doc_count = input.matches(".md").count() + input.matches("///").count();
        let rust_count = input.matches(".rs").count();
        let py_count = input.matches(".py").count();
        
        // Calculate score based on actual content
        let mut score = 0.5; // Start neutral
        
        // Penalties
        score -= (todo_count as f32 / total_lines) * 2.0;
        score -= (warning_count as f32 / total_lines) * 1.5;
        
        // Bonuses
        score += (test_count as f32 / total_lines) * 0.8;
        score += (doc_count as f32 / total_lines) * 0.6;
        score += (rust_count as f32 / total_lines) * 0.3; // Rust is good!
        score += (py_count as f32 / total_lines) * 0.2;
        
        // Clamp to [-1, 1]
        score = score.max(-1.0).min(1.0);
        
        state.fill(score);
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

        // Analyze complexity dynamically
        let line_count = input.lines().count();
        let file_count = input.matches("MODIFIED:").count() 
            + input.matches("NEW:").count() 
            + input.matches("DELETED:").count();

        // Different file types have different complexity
        let rust_files = input.matches(".rs").count();
        let py_files = input.matches(".py").count();
        let md_files = input.matches(".md").count();
        let config_files = input.matches(".toml").count() 
            + input.matches(".json").count() 
            + input.matches(".yaml").count();
        
        // Calculate complexity score
        let mut score = 0.5;
        
        // File count scoring (sweet spot: 3-7)
        if (3..=7).contains(&file_count) {
            score += 0.3;
        } else if file_count < 3 {
            score -= 0.1;
        } else if file_count > 10 {
            score -= 0.3;
        }
        
        // Type diversity (mixed is good)
        let type_diversity = [rust_files > 0, py_files > 0, md_files > 0, config_files > 0]
            .iter()
            .filter(|&&x| x)
            .count();
        
        score += (type_diversity as f32) * 0.1;
        
        // Line count (not too big)
        if line_count > 50 {
            score -= 0.2;
        }
        
        score = score.max(0.0).min(1.0);
        state.fill(score);
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
            if line.starts_with("MODIFIED:") || line.starts_with("NEW:") || line.starts_with("DELETED:") {
                if let Some(path) = line.split_whitespace().nth(1) {
                    paths.push(path);
                }
            }
        }

        if paths.is_empty() {
            state.fill(0.0);
            return state;
        }

        // Extract directories and filenames
        let dirs: Vec<_> = paths
            .iter()
            .filter_map(|p| p.rsplit_once('/').map(|(d, _)| d))
            .collect();
        
        let filenames: Vec<_> = paths
            .iter()
            .filter_map(|p| p.rsplit_once('/').map(|(_, f)| f))
            .collect();

        let unique_dirs = dirs.iter().collect::<std::collections::HashSet<_>>().len();
        
        // Check for name similarity (related files)
        let mut name_similarity: f32 = 0.0;
        for i in 0..filenames.len() {
            for j in (i+1)..filenames.len() {
                let f1 = filenames[i];
                let f2 = filenames[j];
                
                // Check for common prefixes/suffixes
                let common_prefix = f1.chars()
                    .zip(f2.chars())
                    .take_while(|(a, b)| a == b)
                    .count();
                
                if common_prefix > 3 {
                    name_similarity += 0.2;
                }
            }
        }
        
        // Calculate coherence score
        let mut coherence: f32 = 0.5;
        
        // Directory coherence
        if unique_dirs <= 1 {
            coherence += 0.4; // All in same dir
        } else if unique_dirs <= 2 {
            coherence += 0.2; // Mostly related
        } else if unique_dirs > 4 {
            coherence -= 0.3; // Very scattered
        }
        
        // Name similarity bonus
        coherence += name_similarity.min(0.3_f32);
        
        // File type coherence
        let extensions: Vec<_> = paths
            .iter()
            .filter_map(|p| p.rsplit_once('.').map(|(_, e)| e))
            .collect();
        let unique_extensions = extensions.iter().collect::<std::collections::HashSet<_>>().len();
        
        if unique_extensions == 1 {
            coherence += 0.2; // All same type
        }
        
        coherence = coherence.max(0.0_f32).min(1.0_f32);
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
