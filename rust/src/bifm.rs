/// Braille Infinity Fitness Map (BIFM-64)
/// 
/// Encodes 3D fitness topology in a single 8-dot Braille character:
/// - κ (Curvature): Semantic deformation (0-7) - left column (dots 1-2-3)
/// - σ (Stability): Volatility/risk (0-7) - right column (dots 4-5-6)
/// - δ (Direction): Evolution direction (0-3) - bottom pair (dots 7-8)

/// Fitness topology encoded in 3D space
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct FitnessTopology {
    /// Curvature: How much semantic deformation (0-7)
    pub kappa: u8,
    
    /// Stability: How volatile/risky (0-7)
    pub sigma: u8,
    
    /// Direction: Evolution trajectory (0-3)
    /// 0 = neutral/stable
    /// 1 = positive drift
    /// 2 = negative drift
    /// 3 = divergent/critical
    pub delta: u8,
}

impl FitnessTopology {
    pub fn new(kappa: u8, sigma: u8, delta: u8) -> Self {
        assert!(kappa <= 7, "κ must be 0-7");
        assert!(sigma <= 7, "σ must be 0-7");
        assert!(delta <= 3, "δ must be 0-3");
        
        Self { kappa, sigma, delta }
    }
    
    /// Encode to BIFM-64 Braille character
    pub fn to_braille(&self) -> char {
        // Base Unicode: U+2800
        let base = 0x2800u32;
        
        // Left column (κ): dots 1-2-3
        let left = self.kappa as u32;
        
        // Right column (σ): dots 4-5-6 (shift by 3)
        let right = (self.sigma as u32) << 3;
        
        // Bottom pair (δ): dots 7-8 (shift by 6)
        let bottom = (self.delta as u32) << 6;
        
        // Combine
        let codepoint = base + left + right + bottom;
        
        char::from_u32(codepoint).unwrap()
    }
    
    /// Decode from BIFM-64 Braille character
    pub fn from_braille(c: char) -> Option<Self> {
        let codepoint = c as u32;
        let base = 0x2800u32;
        
        if codepoint < base || codepoint > base + 255 {
            return None;
        }
        
        let offset = codepoint - base;
        
        // Extract components
        let kappa = (offset & 0b00000111) as u8;
        let sigma = ((offset >> 3) & 0b00000111) as u8;
        let delta = ((offset >> 6) & 0b00000011) as u8;
        
        Some(Self { kappa, sigma, delta })
    }
    
    /// Human-readable interpretation
    pub fn interpret(&self) -> String {
        let curvature = match self.kappa {
            0 => "minimal deformation",
            1..=2 => "slight change",
            3..=4 => "moderate change",
            5..=6 => "significant change",
            7 => "maximum deformation",
            _ => unreachable!(),
        };
        
        let stability = match self.sigma {
            0 => "rock solid",
            1..=2 => "stable",
            3..=4 => "moderate volatility",
            5..=6 => "high volatility",
            7 => "extremely volatile",
            _ => unreachable!(),
        };
        
        let direction = match self.delta {
            0 => "neutral/stable",
            1 => "positive drift",
            2 => "negative drift",
            3 => "divergent/critical",
            _ => unreachable!(),
        };
        
        format!("{}, {}, {}", curvature, stability, direction)
    }
    
    /// Calculate from commit analysis
    pub fn from_analysis(
        file_count: usize,
        line_changes: usize,
        has_tests: bool,
        has_breaking: bool,
        fitness_score: f32,
    ) -> Self {
        // κ (Curvature): Based on scope of change
        let kappa = if file_count > 20 {
            7
        } else if file_count > 10 {
            6
        } else if file_count > 5 {
            4
        } else if file_count > 2 {
            2
        } else {
            1
        };
        
        // σ (Stability): Based on risk factors
        let mut sigma = 0u8;
        
        if !has_tests {
            sigma += 2;
        }
        if has_breaking {
            sigma += 3;
        }
        if line_changes > 500 {
            sigma += 2;
        }
        
        sigma = sigma.min(7);
        
        // δ (Direction): Based on fitness trajectory
        let delta = if fitness_score >= 0.9 {
            0 // Stable
        } else if fitness_score >= 0.7 {
            1 // Positive
        } else if fitness_score >= 0.5 {
            2 // Negative
        } else {
            3 // Critical
        };
        
        Self { kappa, sigma, delta }
    }
}

/// BIFM-64 complete table for reference
pub const BIFM_TABLE: &str = r#"
BIFM-64 — Complete 8×8 Table (δ=0–3)

δ = 0 (neutral/stable)
κ↓ σ→ | 0  1  2  3  4  5  6  7
--------------------------------
0      ⠀  ⠈  ⠐  ⠘  ⠠  ⠨  ⠰  ⠸
1      ⠁  ⠉  ⠑  ⠙  ⠡  ⠩  ⠱  ⠹
2      ⠂  ⠊  ⠒  ⠚  ⠢  ⠪  ⠲  ⠺
3      ⠃  ⠋  ⠓  ⠛  ⠣  ⠫  ⠳  ⠻
4      ⠄  ⠌  ⠔  ⠜  ⠤  ⠬  ⠴  ⠼
5      ⠅  ⠍  ⠕  ⠝  ⠥  ⠭  ⠵  ⠽
6      ⠆  ⠎  ⠖  ⠞  ⠦  ⠮  ⠶  ⠾
7      ⠇  ⠏  ⠗  ⠟  ⠧  ⠯  ⠷  ⠿

δ = 1 (positive drift)
κ↓ σ→ | 0  1  2  3  4  5  6  7
--------------------------------
0      ⡀  ⡈  ⡐  ⡘  ⡠  ⡨  ⡰  ⡸
1      ⡁  ⡉  ⡑  ⡙  ⡡  ⡩  ⡱  ⡹
2      ⡂  ⡊  ⡒  ⡚  ⡢  ⡪  ⡲  ⡺
3      ⡃  ⡋  ⡓  ⡛  ⡣  ⡫  ⡳  ⡻
4      ⡄  ⡌  ⡔  ⡜  ⡤  ⡬  ⡴  ⡼
5      ⡅  ⡍  ⡕  ⡝  ⡥  ⡭  ⡵  ⡽
6      ⡆  ⡎  ⡖  ⡞  ⡦  ⡮  ⡶  ⡾
7      ⡇  ⡏  ⡗  ⡟  ⡧  ⡯  ⡷  ⡿

δ = 2 (negative drift)
κ↓ σ→ | 0  1  2  3  4  5  6  7
--------------------------------
0      ⢀  ⢈  ⢐  ⢘  ⢠  ⢨  ⢰  ⢸
1      ⢁  ⢉  ⢑  ⢙  ⢡  ⢩  ⢱  ⢹
2      ⢂  ⢊  ⢒  ⢚  ⢢  ⢪  ⢲  ⢺
3      ⢃  ⢋  ⢓  ⢛  ⢣  ⢫  ⢳  ⢻
4      ⢄  ⢌  ⢔  ⢜  ⢤  ⢬  ⢴  ⢼
5      ⢅  ⢍  ⢕  ⢝  ⢥  ⢭  ⢵  ⢽
6      ⢆  ⢎  ⢖  ⢞  ⢦  ⢮  ⢶  ⢾
7      ⢇  ⢏  ⢗  ⢟  ⢧  ⢯  ⢷  ⢿

δ = 3 (divergent/critical)
κ↓ σ→ | 0  1  2  3  4  5  6  7
--------------------------------
0      ⣀  ⣈  ⣐  ⣘  ⣠  ⣨  ⣰  ⣸
1      ⣁  ⣉  ⣑  ⣙  ⣡  ⣩  ⣱  ⣹
2      ⣂  ⣊  ⣒  ⣚  ⣢  ⣪  ⣲  ⣺
3      ⣃  ⣋  ⣓  ⣛  ⣣  ⣫  ⣳  ⣻
4      ⣄  ⣌  ⣔  ⣜  ⣤  ⣬  ⣴  ⣼
5      ⣅  ⣍  ⣕  ⣝  ⣥  ⣭  ⣵  ⣽
6      ⣆  ⣎  ⣖  ⣞  ⣦  ⣮  ⣶  ⣾
7      ⣇  ⣏  ⣗  ⣟  ⣧  ⣯  ⣷  ⣿
"#;

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_encode_decode() {
        let topo = FitnessTopology::new(7, 5, 3);
        let braille = topo.to_braille();
        assert_eq!(braille, '⣯');
        
        let decoded = FitnessTopology::from_braille(braille).unwrap();
        assert_eq!(decoded, topo);
    }
    
    #[test]
    fn test_all_64_tokens() {
        for delta in 0..=3 {
            for kappa in 0..=7 {
                for sigma in 0..=7 {
                    let topo = FitnessTopology::new(kappa, sigma, delta);
                    let braille = topo.to_braille();
                    let decoded = FitnessTopology::from_braille(braille).unwrap();
                    
                    assert_eq!(decoded.kappa, kappa);
                    assert_eq!(decoded.sigma, sigma);
                    assert_eq!(decoded.delta, delta);
                }
            }
        }
    }
    
    #[test]
    fn test_interpretation() {
        let topo = FitnessTopology::new(7, 5, 3);
        let interp = topo.interpret();
        assert!(interp.contains("maximum deformation"));
        assert!(interp.contains("high volatility"));
        assert!(interp.contains("divergent"));
    }
}
