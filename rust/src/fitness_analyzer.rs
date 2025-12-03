use std::collections::{HashMap, HashSet};
use regex::Regex;

/// Advanced fitness analyzer that deeply understands code changes
pub struct FitnessAnalyzer {
    // Cached patterns for performance
    import_pattern: Regex,
    function_pattern: Regex,
    class_pattern: Regex,
    test_pattern: Regex,
    todo_pattern: Regex,
    breaking_pattern: Regex,
    security_pattern: Regex,
}

impl FitnessAnalyzer {
    pub fn new() -> Self {
        Self {
            import_pattern: Regex::new(r"(?m)^(?:import|use|require|include|from .* import)").unwrap(),
            function_pattern: Regex::new(r"(?m)^(?:fn |def |function |const \w+ = |let \w+ = function)").unwrap(),
            class_pattern: Regex::new(r"(?m)^(?:class |struct |enum |trait |interface |type )").unwrap(),
            test_pattern: Regex::new(r"(?i)(?:#\[test\]|@test|describe\(|it\(|test\(|assert|expect)").unwrap(),
            todo_pattern: Regex::new(r"(?i)(?:TODO|FIXME|HACK|XXX|BUG|REFACTOR)").unwrap(),
            breaking_pattern: Regex::new(r"(?i)(?:BREAKING|deprecated|removed|deleted)").unwrap(),
            security_pattern: Regex::new(r"(?i)(?:password|secret|token|api[_-]?key|private[_-]?key|auth|credential)").unwrap(),
        }
    }

    /// Calculate comprehensive fitness score
    pub fn calculate_fitness(&self, diff: &str) -> FitnessReport {
        let mut report = FitnessReport::new();
        
        // Parse the diff into structured changes
        let changes = self.parse_diff(diff);
        
        // 1. File Metrics (15% weight)
        let file_score = self.analyze_file_metrics(&changes);
        report.add_component("file_metrics", file_score * 0.15);
        
        // 2. Code Complexity (20% weight)
        let complexity_score = self.analyze_complexity(&changes);
        report.add_component("complexity", complexity_score * 0.20);
        
        // 3. Semantic Coherence (25% weight)
        let coherence_score = self.analyze_coherence(&changes);
        report.add_component("coherence", coherence_score * 0.25);
        
        // 4. Test Coverage (15% weight)
        let test_score = self.analyze_test_impact(&changes);
        report.add_component("tests", test_score * 0.15);
        
        // 5. Risk Assessment (15% weight)
        let risk_score = self.analyze_risk(&changes);
        report.add_component("risk", risk_score * 0.15);
        
        // 6. Documentation (10% weight)
        let doc_score = self.analyze_documentation(&changes);
        report.add_component("documentation", doc_score * 0.10);
        
        // Calculate final score
        report.calculate_final_score();
        
        // Generate recommendations
        self.generate_recommendations(&mut report);
        
        report
    }
    
    fn parse_diff(&self, diff: &str) -> Vec<FileChange> {
        let mut changes = Vec::new();
        let mut current_file = None;
        let mut added_lines = Vec::new();
        let mut removed_lines = Vec::new();
        
        for line in diff.lines() {
            if line.starts_with("MODIFIED:") || line.starts_with("NEW:") || line.starts_with("DELETED:") {
                // Save previous file if exists
                if let Some(file) = current_file.take() {
                    changes.push(FileChange {
                        path: file,
                        added: added_lines.clone(),
                        removed: removed_lines.clone(),
                    });
                    added_lines.clear();
                    removed_lines.clear();
                }
                
                current_file = Some(line.split_whitespace().nth(1).unwrap_or("").to_string());
            } else if line.starts_with('+') && !line.starts_with("+++") {
                added_lines.push(line[1..].to_string());
            } else if line.starts_with('-') && !line.starts_with("---") {
                removed_lines.push(line[1..].to_string());
            }
        }
        
        // Save last file
        if let Some(file) = current_file {
            changes.push(FileChange {
                path: file,
                added: added_lines,
                removed: removed_lines,
            });
        }
        
        changes
    }
    
    fn analyze_file_metrics(&self, changes: &[FileChange]) -> f32 {
        let file_count = changes.len();
        
        // Optimal range is 2-5 files
        if file_count == 0 {
            return 0.0;
        } else if file_count >= 2 && file_count <= 5 {
            return 1.0;
        } else if file_count == 1 {
            return 0.7; // Single file is okay
        } else if file_count <= 10 {
            return 0.8 - (file_count as f32 - 5.0) * 0.1; // Gradually decrease
        } else {
            return 0.3; // Too many files
        }
    }
    
    fn analyze_complexity(&self, changes: &[FileChange]) -> f32 {
        let mut total_complexity = 0;
        let mut max_complexity = 0;
        
        for change in changes {
            let complexity = self.calculate_cyclomatic_complexity(change);
            total_complexity += complexity;
            max_complexity = max_complexity.max(complexity);
        }
        
        // Penalize high complexity
        if max_complexity > 10 {
            return 0.3;
        } else if max_complexity > 7 {
            return 0.6;
        } else if max_complexity > 4 {
            return 0.8;
        } else {
            return 1.0;
        }
    }
    
    fn calculate_cyclomatic_complexity(&self, change: &FileChange) -> usize {
        let mut complexity = 1; // Base complexity
        
        for line in &change.added {
            // Count decision points
            if line.contains("if ") || line.contains("if(") {
                complexity += 1;
            }
            if line.contains("else if") || line.contains("elif") {
                complexity += 1;
            }
            if line.contains("for ") || line.contains("for(") {
                complexity += 1;
            }
            if line.contains("while ") || line.contains("while(") {
                complexity += 1;
            }
            if line.contains("match ") || line.contains("switch") {
                complexity += 1;
            }
            if line.contains(" && ") || line.contains(" || ") {
                complexity += 1;
            }
            if line.contains(".unwrap()") || line.contains("?") {
                complexity += 1; // Error handling paths
            }
        }
        
        complexity
    }
    
    fn analyze_coherence(&self, changes: &[FileChange]) -> f32 {
        if changes.is_empty() {
            return 0.0;
        }
        
        let mut score = 1.0;
        
        // Check directory coherence
        let directories: HashSet<_> = changes.iter()
            .filter_map(|c| c.path.rsplit_once('/').map(|(d, _)| d))
            .collect();
        
        if directories.len() > 3 {
            score *= 0.7; // Too scattered
        } else if directories.len() == 1 {
            score *= 1.2; // Excellent focus
        }
        
        // Check for mixed concerns
        let has_tests = changes.iter().any(|c| c.path.contains("test"));
        let has_src = changes.iter().any(|c| !c.path.contains("test"));
        let has_docs = changes.iter().any(|c| c.path.ends_with(".md"));
        let has_config = changes.iter().any(|c| 
            c.path.ends_with(".toml") || 
            c.path.ends_with(".json") || 
            c.path.ends_with(".yml")
        );
        
        // Mixed concerns reduce coherence
        let concern_count = [has_tests, has_src, has_docs, has_config]
            .iter()
            .filter(|&&x| x)
            .count();
        
        if concern_count > 2 {
            score *= 0.8; // Too many different concerns
        }
        
        // Check for related functionality
        let functions_added = self.extract_function_names(changes);
        let semantic_similarity = self.calculate_semantic_similarity(&functions_added);
        score *= semantic_similarity;
        
        score.min(1.0)
    }
    
    fn extract_function_names(&self, changes: &[FileChange]) -> Vec<String> {
        let mut names = Vec::new();
        
        for change in changes {
            for line in &change.added {
                if let Some(caps) = self.function_pattern.captures(line) {
                    if let Some(name) = line.split_whitespace().nth(1) {
                        names.push(name.trim_matches(&['{', '(', ':', '='][..]).to_string());
                    }
                }
            }
        }
        
        names
    }
    
    fn calculate_semantic_similarity(&self, names: &[String]) -> f32 {
        if names.len() < 2 {
            return 1.0; // Can't compare
        }
        
        // Check for common prefixes/patterns
        let mut similarity_score = 0.0;
        let mut comparisons = 0;
        
        for i in 0..names.len() {
            for j in (i + 1)..names.len() {
                let common_prefix_len = names[i]
                    .chars()
                    .zip(names[j].chars())
                    .take_while(|(a, b)| a == b)
                    .count();
                
                let max_len = names[i].len().max(names[j].len());
                if max_len > 0 {
                    similarity_score += common_prefix_len as f32 / max_len as f32;
                    comparisons += 1;
                }
            }
        }
        
        if comparisons > 0 {
            0.5 + (similarity_score / comparisons as f32) * 0.5
        } else {
            1.0
        }
    }
    
    fn analyze_test_impact(&self, changes: &[FileChange]) -> f32 {
        let mut has_tests = false;
        let mut has_source = false;
        let mut test_count = 0;
        let mut source_count = 0;
        
        for change in changes {
            if change.path.contains("test") || change.path.contains("spec") {
                has_tests = true;
                test_count += 1;
            } else if change.path.ends_with(".rs") || 
                      change.path.ends_with(".py") || 
                      change.path.ends_with(".js") ||
                      change.path.ends_with(".ts") {
                has_source = true;
                source_count += 1;
            }
            
            // Count test assertions in content
            for line in &change.added {
                if self.test_pattern.is_match(line) {
                    test_count += 1;
                }
            }
        }
        
        if has_source && has_tests {
            // Excellent: changes include tests
            return 1.0;
        } else if has_tests && !has_source {
            // Good: only test changes
            return 0.9;
        } else if has_source && source_count <= 3 {
            // Okay: small change without tests
            return 0.6;
        } else {
            // Poor: large change without tests
            return 0.3;
        }
    }
    
    fn analyze_risk(&self, changes: &[FileChange]) -> f32 {
        let mut risk_factors = 0;
        let mut critical_changes = 0;
        
        for change in changes {
            // Check for risky patterns
            for line in &change.added {
                if self.breaking_pattern.is_match(line) {
                    risk_factors += 3; // Breaking changes are high risk
                }
                if self.security_pattern.is_match(line) {
                    risk_factors += 2; // Security-related changes need care
                }
                if self.todo_pattern.is_match(line) {
                    risk_factors += 1; // Incomplete work
                }
                if line.contains(".unwrap()") || line.contains("unsafe") {
                    risk_factors += 2; // Potentially dangerous code
                }
            }
            
            // Check file criticality
            if change.path.contains("auth") || 
               change.path.contains("security") ||
               change.path.contains("payment") ||
               change.path.contains("database") {
                critical_changes += 1;
            }
            
            // Removed more than added (potential deletion)
            if change.removed.len() > change.added.len() * 2 {
                risk_factors += 1;
            }
        }
        
        // Convert risk to inverse score (low risk = high score)
        if risk_factors == 0 && critical_changes == 0 {
            1.0
        } else if risk_factors <= 2 && critical_changes == 0 {
            0.8
        } else if risk_factors <= 5 && critical_changes <= 1 {
            0.6
        } else if risk_factors <= 10 {
            0.4
        } else {
            0.2 // Very risky
        }
    }
    
    fn analyze_documentation(&self, changes: &[FileChange]) -> f32 {
        let mut doc_lines = 0;
        let mut code_lines = 0;
        let mut has_readme_change = false;
        
        for change in changes {
            if change.path.ends_with("README.md") || change.path.contains("doc") {
                has_readme_change = true;
            }
            
            for line in &change.added {
                if line.trim().starts_with("//") || 
                   line.trim().starts_with("#") ||
                   line.trim().starts_with("/**") ||
                   line.trim().starts_with("///") ||
                   line.contains("TODO") ||
                   line.contains("NOTE") {
                    doc_lines += 1;
                } else if !line.trim().is_empty() {
                    code_lines += 1;
                }
            }
        }
        
        let doc_ratio = if code_lines > 0 {
            doc_lines as f32 / code_lines as f32
        } else {
            0.0
        };
        
        if has_readme_change {
            return 1.0; // Documentation updates are excellent
        } else if doc_ratio > 0.2 {
            return 0.9; // Good documentation ratio
        } else if doc_ratio > 0.1 {
            return 0.7; // Adequate documentation
        } else if doc_ratio > 0.05 {
            return 0.5; // Some documentation
        } else {
            return 0.3; // Poor documentation
        }
    }
    
    fn generate_recommendations(&self, report: &mut FitnessReport) {
        let score = report.final_score;
        
        if score > 0.8 {
            report.add_reason("Excellent commit candidate: well-structured, tested, and documented");
            report.set_decision(CommitDecision::Commit);
        } else if score > 0.6 {
            report.add_reason("Good changes, ready to commit");
            
            // Add specific suggestions based on weak areas
            if report.components.get("tests").unwrap_or(&0.0) < &0.5 {
                report.add_suggestion("Consider adding tests for these changes");
            }
            if report.components.get("documentation").unwrap_or(&0.0) < &0.5 {
                report.add_suggestion("Add documentation or comments");
            }
            
            report.set_decision(CommitDecision::Commit);
        } else if score > 0.4 {
            report.add_reason("Changes need refinement before committing");
            
            if report.components.get("coherence").unwrap_or(&0.0) < &0.5 {
                report.add_suggestion("Split into smaller, more focused commits");
            }
            if report.components.get("risk").unwrap_or(&0.0) < &0.5 {
                report.add_suggestion("Review risky changes carefully");
            }
            
            report.set_decision(CommitDecision::Wait);
        } else {
            report.add_reason("Changes are not ready for commit");
            report.add_suggestion("Break down changes into smaller, coherent pieces");
            report.add_suggestion("Ensure all changes are complete and tested");
            
            report.set_decision(CommitDecision::Split);
        }
    }
}

#[derive(Debug, Clone)]
pub struct FileChange {
    pub path: String,
    pub added: Vec<String>,
    pub removed: Vec<String>,
}

#[derive(Debug, Clone)]
pub struct FitnessReport {
    pub final_score: f32,
    pub components: HashMap<String, f32>,
    pub reasons: Vec<String>,
    pub suggestions: Vec<String>,
    pub decision: CommitDecision,
}

impl FitnessReport {
    pub fn new() -> Self {
        Self {
            final_score: 0.0,
            components: HashMap::new(),
            reasons: Vec::new(),
            suggestions: Vec::new(),
            decision: CommitDecision::Wait,
        }
    }
    
    pub fn add_component(&mut self, name: &str, score: f32) {
        self.components.insert(name.to_string(), score);
    }
    
    pub fn calculate_final_score(&mut self) {
        self.final_score = self.components.values().sum();
    }
    
    pub fn add_reason(&mut self, reason: &str) {
        self.reasons.push(reason.to_string());
    }
    
    pub fn add_suggestion(&mut self, suggestion: &str) {
        self.suggestions.push(suggestion.to_string());
    }
    
    pub fn set_decision(&mut self, decision: CommitDecision) {
        self.decision = decision;
    }
}

#[derive(Debug, Clone, PartialEq)]
pub enum CommitDecision {
    Commit,    // Ready to commit
    Wait,      // Need more changes
    Split,     // Too large, needs splitting
    Ghost,     // Save locally but don't push
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_fitness_analyzer() {
        let analyzer = FitnessAnalyzer::new();
        
        let diff = r#"
MODIFIED: src/main.rs
+fn calculate_total(items: Vec<i32>) -> i32 {
+    items.iter().sum()
+}
+
+#[test]
+fn test_calculate_total() {
+    assert_eq!(calculate_total(vec![1, 2, 3]), 6);
+}
MODIFIED: src/lib.rs
+/// Calculate average of numbers
+fn calculate_average(items: Vec<i32>) -> f32 {
+    if items.is_empty() {
+        return 0.0;
+    }
+    items.iter().sum::<i32>() as f32 / items.len() as f32
+}
"#;
        
        let report = analyzer.calculate_fitness(diff);
        
        // Should have good score for coherent changes with tests
        assert!(report.final_score > 0.6);
        assert!(report.components.contains_key("tests"));
        assert!(report.components["tests"] > 0.8); // Has tests
        assert_eq!(report.decision, CommitDecision::Commit);
    }
}
