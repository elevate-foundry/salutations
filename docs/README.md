# Autonomous Git - GitHub Pages

This directory contains the GitHub Pages site for the Autonomous Git project.

## 🌐 Live Site

Visit: https://ryanbarrett.github.io/salutations/

## 📁 Structure

```
docs/
├── index.html           # Landing page
├── getting-started.html # Documentation
├── styles.css          # Shared styles
└── README.md           # This file
```

## 🚀 Deployment

GitHub Pages automatically deploys from the `docs/` directory when you push to the main branch.

### Enable GitHub Pages

1. Go to repository Settings
2. Navigate to Pages section
3. Under "Source", select:
   - Branch: `main`
   - Folder: `/docs`
4. Click Save

GitHub will automatically build and deploy your site!

## 🎨 Features

- **Modern Design**: Dark theme with gradient accents
- **Responsive**: Works on all devices
- **Interactive**: Smooth animations and hover effects
- **Fast**: Pure HTML/CSS/JS, no build step needed
- **Accessible**: Semantic HTML and proper contrast ratios

## 🛠️ Local Development

Simply open the HTML files in your browser:

```bash
# macOS
open docs/index.html

# Linux
xdg-open docs/index.html

# Or use a local server
python -m http.server 8000 --directory docs
# Then visit http://localhost:8000
```

## 📝 Content

The site showcases:

- **Problem Statement**: Why Git is hard
- **Solution**: How Autonomous Git solves it
- **Features**: Fitness functions, AI commit messages, smart branching
- **Demo**: Code comparisons and live examples
- **Getting Started**: Installation and usage guide

## 🤝 Contributing

To update the site:

1. Edit HTML/CSS files in `docs/`
2. Test locally
3. Commit and push to main branch
4. GitHub Pages will auto-deploy

## 📄 License

Part of the Salutations project. See main repository for license details.
