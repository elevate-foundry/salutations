/// Semantic Compression Language (SCL) for Git
/// 
/// Compresses git commits to pure semantics, renders in Braille,
/// translates to any language.

use std::collections::HashMap;

/// Braille token representing a semantic concept
#[derive(Debug, Clone, PartialEq)]
pub struct BrailleToken(pub String);

/// Semantic token (language-agnostic)
#[derive(Debug, Clone, PartialEq)]
pub enum SemanticToken {
    // Actions
    Fix,
    Add,
    Remove,
    Update,
    Refactor,
    
    // Domains
    Authentication,
    Security,
    Performance,
    Testing,
    Documentation,
    
    // Modifiers
    EdgeCase,
    Feature,
    Bug,
    Enhancement,
}

impl SemanticToken {
    /// Convert to Braille representation
    pub fn to_braille(&self) -> BrailleToken {
        let braille = match self {
            // Actions
            SemanticToken::Fix => "⠋⠊⠭",
            SemanticToken::Add => "⠁⠙⠙",
            SemanticToken::Remove => "⠗⠑⠍",
            SemanticToken::Update => "⠥⠏⠙",
            SemanticToken::Refactor => "⠗⠑⠋",
            
            // Domains
            SemanticToken::Authentication => "⠁⠥⠞⠓",
            SemanticToken::Security => "⠎⠑⠉",
            SemanticToken::Performance => "⠏⠑⠗⠋",
            SemanticToken::Testing => "⠞⠑⠎⠞",
            SemanticToken::Documentation => "⠙⠕⠉",
            
            // Modifiers
            SemanticToken::EdgeCase => "⠑⠙⠛⠑",
            SemanticToken::Feature => "⠋⠑⠁⠞",
            SemanticToken::Bug => "⠃⠥⠛",
            SemanticToken::Enhancement => "⠑⠝⠓",
        };
        
        BrailleToken(braille.to_string())
    }
    
    /// Convert from Braille representation
    pub fn from_braille(braille: &BrailleToken) -> Option<Self> {
        match braille.0.as_str() {
            "⠋⠊⠭" => Some(SemanticToken::Fix),
            "⠁⠙⠙" => Some(SemanticToken::Add),
            "⠗⠑⠍" => Some(SemanticToken::Remove),
            "⠥⠏⠙" => Some(SemanticToken::Update),
            "⠗⠑⠋" => Some(SemanticToken::Refactor),
            "⠁⠥⠞⠓" => Some(SemanticToken::Authentication),
            "⠎⠑⠉" => Some(SemanticToken::Security),
            "⠏⠑⠗⠋" => Some(SemanticToken::Performance),
            "⠞⠑⠎⠞" => Some(SemanticToken::Testing),
            "⠙⠕⠉" => Some(SemanticToken::Documentation),
            "⠑⠙⠛⠑" => Some(SemanticToken::EdgeCase),
            "⠋⠑⠁⠞" => Some(SemanticToken::Feature),
            "⠃⠥⠛" => Some(SemanticToken::Bug),
            "⠑⠝⠓" => Some(SemanticToken::Enhancement),
            _ => None,
        }
    }
}

use crate::bifm::FitnessTopology;

/// SCL Commit - compressed semantic representation
#[derive(Debug, Clone)]
pub struct SCLCommit {
    /// Semantic tokens (language-agnostic)
    pub tokens: Vec<SemanticToken>,
    
    /// Braille representation (native format)
    pub braille: String,
    
    /// Fitness topology (BIFM-64)
    pub fitness: Option<FitnessTopology>,
    
    /// Metadata
    pub timestamp: String,
    pub author: String,
}

impl SCLCommit {
    /// Create from semantic tokens
    pub fn new(tokens: Vec<SemanticToken>, author: String) -> Self {
        Self::with_fitness(tokens, author, None)
    }
    
    /// Create with fitness topology
    pub fn with_fitness(
        tokens: Vec<SemanticToken>,
        author: String,
        fitness: Option<FitnessTopology>,
    ) -> Self {
        let mut braille = tokens
            .iter()
            .map(|t| t.to_braille().0)
            .collect::<Vec<_>>()
            .join(".");
        
        // Append fitness topology if present
        if let Some(ref f) = fitness {
            braille.push('.');
            braille.push(f.to_braille());
        }
        
        Self {
            tokens,
            braille,
            fitness,
            timestamp: chrono::Utc::now().to_rfc3339(),
            author,
        }
    }
    
    /// Parse from Braille string
    pub fn from_braille(braille: &str, author: String) -> Option<Self> {
        let parts: Vec<&str> = braille.split('.').collect();
        
        let mut tokens = Vec::new();
        let mut fitness = None;
        
        for part in parts {
            // Try to parse as semantic token first
            if let Some(token) = SemanticToken::from_braille(&BrailleToken(part.to_string())) {
                tokens.push(token);
            } else if part.len() == 1 {
                // Try to parse as fitness topology (single character)
                if let Some(c) = part.chars().next() {
                    fitness = FitnessTopology::from_braille(c);
                }
            }
        }
        
        if tokens.is_empty() {
            return None;
        }
        
        Some(Self {
            tokens: tokens.clone(),
            braille: braille.to_string(),
            fitness,
            timestamp: chrono::Utc::now().to_rfc3339(),
            author,
        })
    }
}

/// Language for rendering
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum Language {
    English,
    Spanish,
    Chinese,
    Japanese,
    French,
    German,
    Dutch,
}

/// Renders SCL commits in natural language
pub struct LanguageRenderer {
    templates: HashMap<Language, HashMap<String, String>>,
}

impl LanguageRenderer {
    pub fn new() -> Self {
        let mut templates = HashMap::new();
        
        // English templates
        let mut english = HashMap::new();
        english.insert("Fix".to_string(), "fix".to_string());
        english.insert("Add".to_string(), "add".to_string());
        english.insert("Remove".to_string(), "remove".to_string());
        english.insert("Update".to_string(), "update".to_string());
        english.insert("Refactor".to_string(), "refactor".to_string());
        english.insert("Authentication".to_string(), "authentication".to_string());
        english.insert("Security".to_string(), "security".to_string());
        english.insert("Performance".to_string(), "performance".to_string());
        english.insert("Testing".to_string(), "testing".to_string());
        english.insert("Documentation".to_string(), "documentation".to_string());
        english.insert("EdgeCase".to_string(), "edge case".to_string());
        english.insert("Feature".to_string(), "feature".to_string());
        english.insert("Bug".to_string(), "bug".to_string());
        english.insert("Enhancement".to_string(), "enhancement".to_string());
        templates.insert(Language::English, english);
        
        // Spanish templates
        let mut spanish = HashMap::new();
        spanish.insert("Fix".to_string(), "corregir".to_string());
        spanish.insert("Add".to_string(), "añadir".to_string());
        spanish.insert("Remove".to_string(), "eliminar".to_string());
        spanish.insert("Update".to_string(), "actualizar".to_string());
        spanish.insert("Refactor".to_string(), "refactorizar".to_string());
        spanish.insert("Authentication".to_string(), "autenticación".to_string());
        spanish.insert("Security".to_string(), "seguridad".to_string());
        spanish.insert("Performance".to_string(), "rendimiento".to_string());
        spanish.insert("Testing".to_string(), "pruebas".to_string());
        spanish.insert("Documentation".to_string(), "documentación".to_string());
        spanish.insert("EdgeCase".to_string(), "caso límite".to_string());
        spanish.insert("Feature".to_string(), "característica".to_string());
        spanish.insert("Bug".to_string(), "error".to_string());
        spanish.insert("Enhancement".to_string(), "mejora".to_string());
        templates.insert(Language::Spanish, spanish);
        
        // Chinese templates
        let mut chinese = HashMap::new();
        chinese.insert("Fix".to_string(), "修复".to_string());
        chinese.insert("Add".to_string(), "添加".to_string());
        chinese.insert("Remove".to_string(), "删除".to_string());
        chinese.insert("Update".to_string(), "更新".to_string());
        chinese.insert("Refactor".to_string(), "重构".to_string());
        chinese.insert("Authentication".to_string(), "身份验证".to_string());
        chinese.insert("Security".to_string(), "安全".to_string());
        chinese.insert("Performance".to_string(), "性能".to_string());
        chinese.insert("Testing".to_string(), "测试".to_string());
        chinese.insert("Documentation".to_string(), "文档".to_string());
        chinese.insert("EdgeCase".to_string(), "边缘情况".to_string());
        chinese.insert("Feature".to_string(), "功能".to_string());
        chinese.insert("Bug".to_string(), "错误".to_string());
        chinese.insert("Enhancement".to_string(), "增强".to_string());
        templates.insert(Language::Chinese, chinese);
        
        Self { templates }
    }
    
    /// Render SCL commit in specified language
    pub fn render(&self, commit: &SCLCommit, lang: Language) -> String {
        let template = self.templates.get(&lang).unwrap();
        
        let words: Vec<String> = commit.tokens
            .iter()
            .map(|token| {
                let key = format!("{:?}", token);
                template.get(&key).cloned().unwrap_or(key)
            })
            .collect();
        
        // Simple composition: action + domain + modifier
        if words.len() >= 2 {
            format!("{}: {}", words[0], words[1..].join(" "))
        } else {
            words.join(" ")
        }
    }
}

impl Default for LanguageRenderer {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_semantic_to_braille() {
        let token = SemanticToken::Fix;
        assert_eq!(token.to_braille().0, "⠋⠊⠭");
    }
    
    #[test]
    fn test_braille_to_semantic() {
        let braille = BrailleToken("⠋⠊⠭".to_string());
        assert_eq!(SemanticToken::from_braille(&braille), Some(SemanticToken::Fix));
    }
    
    #[test]
    fn test_scl_commit() {
        let tokens = vec![
            SemanticToken::Fix,
            SemanticToken::Authentication,
            SemanticToken::EdgeCase,
        ];
        
        let commit = SCLCommit::new(tokens, "test@example.com".to_string());
        assert_eq!(commit.braille, "⠋⠊⠭.⠁⠥⠞⠓.⠑⠙⠛⠑");
    }
    
    #[test]
    fn test_language_rendering() {
        let tokens = vec![
            SemanticToken::Fix,
            SemanticToken::Authentication,
            SemanticToken::EdgeCase,
        ];
        
        let commit = SCLCommit::new(tokens, "test@example.com".to_string());
        let renderer = LanguageRenderer::new();
        
        let english = renderer.render(&commit, Language::English);
        assert!(english.contains("fix"));
        assert!(english.contains("authentication"));
        
        let spanish = renderer.render(&commit, Language::Spanish);
        assert!(spanish.contains("corregir"));
        assert!(spanish.contains("autenticación"));
    }
}
