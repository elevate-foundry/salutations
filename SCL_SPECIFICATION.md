# SCL Specification v0.1

## 🎯 Full Semantic Compression Language Specification

### What is SCL?

**SCL (Semantic Compression Language)** is a formal language for encoding version control semantics in a language-agnostic, accessible format using 8-dot Braille as the native representation.

## 📐 Core Principles

1. **Braille-Native**: Not a translation, but the primary format
2. **Semantic-First**: Captures meaning, not syntax
3. **Lossless**: Can reconstruct intent from compressed form
4. **Universal**: One representation → infinite translations
5. **Machine-Readable**: Structured for AI/automation

## 🔤 Token Vocabulary

### Actions (What Changed)
```
⠋⠊⠭ (fix)      - Bug fix, correction
⠁⠙⠙ (add)      - New feature, addition
⠗⠑⠍ (remove)   - Deletion, removal
⠥⠏⠙ (update)   - Modification, change
⠗⠑⠋ (refactor) - Code restructuring
```

### Domains (Where Changed)
```
⠁⠥⠞⠓ (auth)   - Authentication
⠎⠑⠉ (sec)     - Security
⠏⠑⠗⠋ (perf)   - Performance
⠞⠑⠎⠞ (test)   - Testing
⠙⠕⠉ (doc)     - Documentation
⠋⠑⠁⠞ (feat)   - Feature
```

### Modifiers (How/Why)
```
⠑⠙⠛⠑ (edge)   - Edge case
⠑⠝⠓ (enh)     - Enhancement
⠃⠥⠛ (bug)     - Bug-related
⠉⠗⠊⠞ (crit)   - Critical
```

### Composition Rules

**Format**: `ACTION.DOMAIN.MODIFIER.FITNESS`

**Example**:
```
⠋⠊⠭.⠁⠥⠞⠓.⠑⠙⠛⠑.⣯
│   │   │   └─ Fitness: ⣯ (κ=7, σ=5, δ=3)
│   │   └───── Modifier: edge case
│   └───────── Domain: authentication
└───────────── Action: fix
```

## 📊 BIFM-64 Fitness Topology

### What is "Fitness"?

**Fitness** measures code change quality across three dimensions:

#### κ (Kappa) - Curvature (0-7)
**Semantic deformation**: How much meaning changed

```
0-1: Minimal (typo, formatting)
2-3: Slight (small refactor)
4-5: Moderate (feature addition)
6-7: Maximum (architecture change)
```

**Computed from**:
- File count changed
- Lines added/removed
- Dependency changes
- API surface changes

#### σ (Sigma) - Stability (0-7)
**Risk/volatility**: How risky the change is

```
0-1: Rock solid (tests pass, no breaking)
2-3: Stable (minor risk)
4-5: Moderate volatility (some risk)
6-7: High volatility (breaking changes)
```

**Computed from**:
- Test coverage
- Breaking changes
- Dependency updates
- Error-prone patterns

#### δ (Delta) - Direction (0-3)
**Trajectory**: Where the code is heading

```
0: Neutral/stable (maintenance)
1: Positive drift (improvement)
2: Negative drift (degradation)
3: Divergent/critical (needs review)
```

**Computed from**:
- Code quality metrics
- Complexity trends
- Technical debt
- Historical patterns

### Encoding Algorithm

```rust
// Left column (dots 1-2-3): κ
let kappa_bits = kappa as u32;

// Right column (dots 4-5-6): σ
let sigma_bits = (sigma as u32) << 3;

// Bottom pair (dots 7-8): δ
let delta_bits = (delta as u32) << 6;

// Combine into Unicode codepoint
let codepoint = 0x2800 + kappa_bits + sigma_bits + delta_bits;
let braille_char = char::from_u32(codepoint);
```

### Example Calculations

**Safe Documentation Update**:
```
Files: 1 (README.md)
Lines: +50
Tests: N/A (docs)
Breaking: No

κ = 1 (slight change)
σ = 0 (rock solid)
δ = 1 (positive)

Result: ⡁
```

**Risky Auth Refactor**:
```
Files: 15
Lines: +500/-300
Tests: 80% coverage
Breaking: Yes

κ = 7 (maximum deformation)
σ = 5 (high volatility)
δ = 3 (critical)

Result: ⣯
```

## 🔧 Toolchain Integration

### Git Integration

**Storage Format**:
```
commit a1b2c3d4
Author: developer@example.com
Date: 2025-12-03

⠋⠊⠭.⠁⠥⠞⠓.⠑⠙⠛⠑.⣯

SCL: ⠋⠊⠭.⠁⠥⠞⠓.⠑⠙⠛⠑.⣯
EN: fix: authentication edge case
ES: corregir: autenticación caso límite
```

**Git Hooks**:
```bash
# .git/hooks/commit-msg
#!/bin/bash
# Parse SCL and validate
scl-validate "$1"
```

### Diff/Merge Support

**Semantic Diff**:
```bash
$ git diff --scl
- ⠥⠏⠙.⠙⠕⠉.⡁  (update: documentation, stable)
+ ⠋⠊⠭.⠁⠥⠞⠓.⣯  (fix: auth, critical)

Fitness change: ⡁ → ⣯
Risk increased: σ 0→5, δ 1→3
```

**Semantic Merge**:
```bash
$ git merge --scl feature-branch
Analyzing semantic conflicts...
  ⠋⠊⠭.⠁⠥⠞⠓ (yours) vs ⠥⠏⠙.⠁⠥⠞⠓ (theirs)
  Both touch auth, but different intents
  Recommend: manual review
```

### Code Review Integration

**GitHub/GitLab**:
```markdown
## Commit Analysis

**SCL**: ⠋⠊⠭.⠁⠥⠞⠓.⠑⠙⠛⠑.⣯

**Fitness**: κ=7 σ=5 δ=3
⚠️ **Critical Review Required**
- Maximum semantic deformation
- High volatility
- Divergent trajectory

**Translations**:
- 🇺🇸 fix: authentication edge case
- 🇪🇸 corregir: autenticación caso límite
- 🇨🇳 修复: 身份验证 边缘情况
```

## 🌍 Translation System

### How Translations Work

**Not simple string mapping** - uses semantic understanding:

```python
class SCLTranslator:
    def translate(self, scl: str, target_lang: str) -> str:
        # Parse tokens
        tokens = scl.split('.')
        action, domain, *modifiers = tokens
        
        # Get semantic meaning
        action_sem = self.semantic_db[action]
        domain_sem = self.semantic_db[domain]
        
        # Compose in target language
        template = self.templates[target_lang]
        return template.render(
            action=action_sem,
            domain=domain_sem,
            modifiers=modifiers
        )
```

### Handling Ambiguity

**Problem**: "fix" could mean "repair" or "correct" or "patch"

**Solution**: Context from domain + modifiers

```
⠋⠊⠭.⠁⠥⠞⠓.⠑⠙⠛⠑
→ "fix authentication edge case" (repair specific bug)

⠋⠊⠭.⠙⠕⠉
→ "fix documentation" (correct typo)

⠋⠊⠭.⠎⠑⠉.⠉⠗⠊⠞
→ "fix critical security issue" (patch vulnerability)
```

### Limitations

**What SCL Cannot Express**:
- Detailed implementation notes
- Multi-paragraph explanations
- Issue tracker references
- Code review comments

**Solution**: Extended metadata

```
SCL: ⠋⠊⠭.⠁⠥⠞⠓.⠑⠙⠛⠑.⣯
Extended:
  Issue: #1234
  Reviewer: @alice
  Notes: "Handles OAuth token expiry during request processing"
```

## 🔐 Security & Auditability

### Signing SCL Commits

```bash
$ git commit --scl --gpg-sign
SCL: ⠋⠊⠭.⠁⠥⠞⠓.⠑⠙⠛⠑.⣯
Signature: [GPG signature of SCL + fitness]
```

### Audit Trail

```cypher
// Neo4j query for audit
MATCH (c:Commit)-[:HAS_FITNESS]->(f:FitnessTopology)
WHERE f.delta = 3  // Critical commits
  AND c.timestamp > datetime('2025-01-01')
RETURN c.scl, c.author, c.timestamp, f.braille
ORDER BY c.timestamp DESC
```

### Verification

```bash
$ scl-verify commit-hash
✓ SCL format valid
✓ Fitness topology correct
✓ Translations consistent
✓ GPG signature valid
```

## 🤖 AI Integration

### LLM-Friendly Format

**Why AI loves SCL**:
1. **Structured**: Tokens have clear semantics
2. **Compressed**: Less context needed
3. **Typed**: Action/Domain/Modifier hierarchy
4. **Fitness-aware**: Quality signals built-in

### Example: Automated Code Review

```python
def ai_review(commit_scl: str) -> Review:
    # Parse SCL
    action, domain, modifier, fitness = parse_scl(commit_scl)
    
    # Extract fitness
    kappa, sigma, delta = decode_fitness(fitness)
    
    # AI analysis
    if delta == 3:  # Critical
        return Review(
            status="NEEDS_REVIEW",
            reason=f"High risk: κ={kappa}, σ={sigma}",
            suggestions=ai_suggest_improvements(commit_scl)
        )
```

## 📈 Maturity & Adoption

### Current Status (v0.1)

**✅ Working**:
- Core SCL tokenization
- BIFM-64 encoding/decoding
- Multi-language rendering (6 languages)
- Rust agent implementation
- Neo4j graph integration
- VS Code extension (alpha)

**🚧 In Progress**:
- Git hooks integration
- GitHub/GitLab plugins
- Semantic diff/merge
- Extended metadata format
- Community token vocabulary

**📋 Planned**:
- IDE integrations (JetBrains, Emacs, Vim)
- CI/CD pipeline integration
- Automated fitness calculation
- Machine learning for fitness prediction
- Braille display hardware support

### Known Limitations

1. **Token vocabulary is limited** - Currently ~20 tokens, need ~100+
2. **Fitness calculation is heuristic** - Not yet ML-based
3. **Translation quality varies** - Some languages better than others
4. **Tooling is early** - Not production-ready
5. **No conflict resolution** - Semantic merge is manual

## 🎯 Roadmap

### Phase 1: Foundation (Current)
- ✅ Core SCL spec
- ✅ BIFM-64 encoding
- ✅ Basic tooling
- ✅ Documentation

### Phase 2: Integration (Q1 2026)
- Git hooks
- GitHub/GitLab plugins
- IDE extensions
- CI/CD integration

### Phase 3: Intelligence (Q2 2026)
- ML-based fitness
- Semantic conflict resolution
- Automated translations
- Pattern recognition

### Phase 4: Ecosystem (Q3 2026)
- Community token registry
- Braille hardware support
- Multi-repo analytics
- Swarm learning

## 🤝 Contributing

### How to Extend SCL

**Adding New Tokens**:
```rust
// In scl.rs
pub enum SemanticToken {
    // ... existing tokens
    Deploy,  // New: deployment
}

impl SemanticToken {
    pub fn to_braille(&self) -> BrailleToken {
        match self {
            // ... existing mappings
            SemanticToken::Deploy => BrailleToken("⠙⠏⠇".to_string()),
        }
    }
}
```

**Adding New Languages**:
```rust
// In scl.rs
let mut portuguese = HashMap::new();
portuguese.insert("Fix".to_string(), "corrigir".to_string());
// ... more translations
templates.insert(Language::Portuguese, portuguese);
```

## 📚 References

- **8-Dot Braille**: [Why 8-Dot?](https://elevate-foundry.github.io/salutations/why-8-dot-braille.html)
- **BIFM-64**: [Fitness Topology](https://elevate-foundry.github.io/salutations/scl-bifm.html)
- **Source Code**: [GitHub](https://github.com/elevate-foundry/salutations)
- **Neo4j Integration**: [BIFM_NEO4J.md](./BIFM_NEO4J.md)

## ⚖️ License

MIT License - See [LICENSE](./LICENSE)

---

**Status**: Experimental / Research
**Version**: 0.1.0
**Last Updated**: 2025-12-03

This is a living specification. Feedback and contributions welcome!
