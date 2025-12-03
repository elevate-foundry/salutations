# SCL Git Demo

## 🌟 Semantic Commits in Action

The autonomous Git agent now speaks **Semantic Compression Language**!

## 🚀 Usage

### Basic SCL Commit (English)
```bash
./rust/target/release/agit --scl run
```

Output:
```
👀 Detected changes...
   📊 Fitness: 0.85

🔤 ⠥⠏⠙.⠙⠕⠉
🌍 English translation: update: documentation

🚀 COMMITTED: ⠥⠏⠙.⠙⠕⠉

SCL: ⠥⠏⠙.⠙⠕⠉
```

### Spanish
```bash
./rust/target/release/agit --scl --lang es run
```

Output:
```
🔤 ⠥⠏⠙.⠙⠕⠉
🌍 Spanish translation: actualizar: documentación

🚀 COMMITTED: ⠥⠏⠙.⠙⠕⠉

SCL: ⠥⠏⠙.⠙⠕⠉
```

### Chinese
```bash
./rust/target/release/agit --scl --lang zh run
```

Output:
```
🔤 SCL (Braille): ⠥⠏⠙.⠙⠕⠉
🌍 Chinese Translation: 更新: 文档

🚀 COMMITTED: 更新: 文档

SCL: ⠥⠏⠙.⠙⠕⠉
```

## 🎯 The Magic

**Same semantic meaning, different languages, universal Braille!**

### Example: Authentication Fix

```bash
# Make auth changes
echo "fix auth edge case" > auth.rs

# Commit in Spanish
./rust/target/release/agit --scl --lang es --threshold 0.5 run
```

Output:
```
🔤 SCL (Braille): ⠋⠊⠭.⠁⠥⠞⠓.⠑⠙⠛⠑
🌍 Spanish Translation: corregir: autenticación caso límite

🚀 COMMITTED: corregir: autenticación caso límite

SCL: ⠋⠊⠭.⠁⠥⠞⠓.⠑⠙⠛⠑
```

### Read in Different Language

```bash
# Spanish developer committed
# Chinese developer reads
git log --format="%B" -1
```

Shows:
```
corregir: autenticación caso límite

SCL: ⠋⠊⠭.⠁⠥⠞⠓.⠑⠙⠛⠑
```

The SCL is preserved! Any tool can parse it and render in any language.

## 🌍 Supported Languages

- `--lang en` - English (default)
- `--lang es` - Spanish
- `--lang zh` - Chinese
- `--lang ja` - Japanese
- `--lang fr` - French
- `--lang de` - German

## 🔤 Semantic Tokens

The agent automatically extracts semantics:

| Change Type | SCL Token | Braille |
|-------------|-----------|---------|
| Fix bug | Fix | ⠋⠊⠭ |
| Add feature | Add | ⠁⠙⠙ |
| Update code | Update | ⠥⠏⠙ |
| Refactor | Refactor | ⠗⠑⠋ |
| Remove code | Remove | ⠗⠑⠍ |

| Domain | SCL Token | Braille |
|--------|-----------|---------|
| Authentication | Authentication | ⠁⠥⠞⠓ |
| Security | Security | ⠎⠑⠉ |
| Performance | Performance | ⠏⠑⠗⠋ |
| Testing | Testing | ⠞⠑⠎⠞ |
| Documentation | Documentation | ⠙⠕⠉ |

| Modifier | SCL Token | Braille |
|----------|-----------|---------|
| Edge case | EdgeCase | ⠑⠙⠛⠑ |
| Enhancement | Enhancement | ⠑⠝⠓ |
| Bug | Bug | ⠃⠥⠛ |
| Feature | Feature | ⠋⠑⠁⠞ |

## 🎨 Examples

### Security Fix
```
Changes: security.rs
SCL: ⠋⠊⠭.⠎⠑⠉
English: fix: security
Spanish: corregir: seguridad
Chinese: 修复: 安全
```

### Add Tests
```
Changes: test_auth.rs
SCL: ⠁⠙⠙.⠞⠑⠎⠞
English: add: testing
Spanish: añadir: pruebas
Chinese: 添加: 测试
```

### Performance Enhancement
```
Changes: optimize.rs
SCL: ⠥⠏⠙.⠏⠑⠗⠋.⠑⠝⠓
English: update: performance enhancement
Spanish: actualizar: rendimiento mejora
Chinese: 更新: 性能 增强
```

## 🚀 With Auto-Push

```bash
# Commit AND push in Spanish
./rust/target/release/agit --scl --lang es --push --threshold 0.6 run
```

Output:
```
👀 Detected changes...
   📊 Fitness: 0.87

🔤 SCL (Braille): ⠥⠏⠙.⠙⠕⠉.⠑⠝⠓
🌍 Spanish Translation: actualizar: documentación mejora

🚀 COMMITTED: actualizar: documentación mejora

SCL: ⠥⠏⠙.⠙⠕⠉.⠑⠝⠓

📤 Pushing to remote...
✅ PUSHED: origin/main
```

## 🌟 The Vision

**Every developer, regardless of language or ability, can understand every commit.**

- Blind developers read in Braille (native format)
- International teams read in their language
- Semantics preserved across all translations
- AI can reason about changes semantically

## 🔮 Future

- Parse existing commits to SCL
- Semantic diff: `git diff --semantic`
- Semantic search: `git log --semantic ⠎⠑⠉`
- Cross-repo semantic analysis
- Braille display integration

---

**This is the future of version control.** 🚀
