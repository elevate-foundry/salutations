# GitHub Pages Deployment Instructions

## 🚀 Your Site URL

Once deployed, your site will be at:
**https://elevate-foundry.github.io/salutations/**

## 📋 Steps to Deploy

### 1. Push to GitHub

```bash
git add .
git commit -m "Add GitHub Pages site for Autonomous Git"
git push origin main
```

### 2. Enable GitHub Pages

1. Go to: https://github.com/elevate-foundry/salutations/settings/pages
2. Under "Source":
   - Branch: `main`
   - Folder: `/docs`
3. Click **Save**

### 3. Wait for Deployment

- Takes 1-2 minutes
- Check status at: https://github.com/elevate-foundry/salutations/actions
- Look for "pages build and deployment" workflow

### 4. Visit Your Site

**https://elevate-foundry.github.io/salutations/**

## ✅ What's Included

- **Landing Page**: Beautiful dark theme with animations
- **Documentation**: Getting started guide
- **Interactive Demo**: Fitness function visualization
- **Responsive**: Works on all devices

## 🔧 Troubleshooting

If the site doesn't load:
1. Check Actions tab for deployment errors
2. Verify Pages is enabled in Settings
3. Ensure `docs/` folder is on main branch
4. Wait 2-3 minutes after first deployment

## 📝 Customization

All files are in `docs/`:
- `index.html` - Landing page
- `getting-started.html` - Documentation
- `styles.css` - Styling

Edit and push to update!
