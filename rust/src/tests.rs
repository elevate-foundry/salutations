#[cfg(test)]
mod tests {
    use crate::bifm::FitnessTopology;
    use crate::scl::{BrailleToken, SCLCommit, SemanticToken};

    #[test]
    fn test_bifm_creation() {
        // Test BIFM topology creation
        let topology = FitnessTopology::new(5, 3, 1);
        assert_eq!(topology.kappa, 5);
        assert_eq!(topology.sigma, 3);
        assert_eq!(topology.delta, 1);
        
        // Test from_braille parsing
        let from_braille = FitnessTopology::from_braille('⣯');
        assert!(from_braille.is_some());
        
        // Test interpretation contains expected drift
        assert!(topology.interpret().contains("positive"));
    }

    #[test]
    fn test_scl_commit() {
        // Test SCL commit creation
        let tokens = vec![SemanticToken::Fix, SemanticToken::Authentication];
        let commit = SCLCommit::new(tokens.clone(), "test-agent".to_string());
        
        assert!(!commit.braille.is_empty());
        assert_eq!(commit.author, "test-agent");
        assert!(!commit.timestamp.is_empty());
        
        // Test from_braille parsing
        let braille_str = "⠋⠊⠭.⠁⠥⠞⠓";
        let parsed = SCLCommit::from_braille(braille_str, "agent".to_string());
        assert!(parsed.is_some());
    }
    
    #[test]
    fn test_semantic_token_conversion() {
        // Test token to/from braille conversion
        let token = SemanticToken::Fix;
        let braille = token.to_braille();
        assert_eq!(braille.0, "⠋⠊⠭");
        
        // Test from_braille
        let parsed = SemanticToken::from_braille(&BrailleToken("⠋⠊⠭".to_string()));
        assert_eq!(parsed, Some(SemanticToken::Fix));
    }
    
    #[test]
    fn test_fitness_topology_analysis() {
        // Test fitness analysis
        let topology = FitnessTopology::from_analysis(
            5,      // file_count
            200,    // line_changes  
            true,   // has_tests
            false,  // has_breaking
            0.85,   // fitness_score
        );
        
        assert!(topology.kappa > 0);
        assert!(topology.sigma >= 0);  // sigma can be 0 for very stable changes
        assert!(topology.interpret().contains("drift"));
    }
}
