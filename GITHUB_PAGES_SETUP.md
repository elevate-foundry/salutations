# GitHub Pages Setup Guide

This guide will help you deploy the Autonomous Git website to GitHub Pages.

## 🎯 Quick Setup (5 minutes)

### Step 1: Enable GitHub Pages

1. Go to your repository on GitHub: `https://github.com/ryanbarrett/salutations`
2. Click **Settings** (top menu)
3. Scroll down and click **Pages** (left sidebar)
4. Under **Source**:
   - Branch: Select `main`
   - Folder: Select `/docs`
5. Click **Save**

That's it! GitHub will automatically deploy your site.

### Step 2: Wait for Deployment

- GitHub Pages will build and deploy your site (takes 1-2 minutes)
- You'll see a green checkmark when it's ready
- Your site will be live at: `https://ryanbarrett.github.io/salutations/`

### Step 3: Verify

Visit your site: `https://ryanbarrett.github.io/salutations/`

You should see the Autonomous Git landing page! 🎉

## 🔧 Advanced Configuration

### Custom Domain (Optional)

If you want to use a custom domain like `autonomousgit.dev`:

1. In GitHub Pages settings, enter your custom domain
2. Add DNS records at your domain provider:
   ```
   Type: CNAME
   Name: www
   Value: ryanbarrett.github.io
   ```
3. Wait for DNS propagation (up to 24 hours)

### HTTPS

GitHub Pages automatically provides HTTPS. Just check the "Enforce HTTPS" box in settings.

## 📝 Making Updates

Every time you push changes to the `docs/` directory, GitHub Pages will automatically redeploy:

```bash
# Edit files in docs/
vim docs/index.html

# Commit and push
git add docs/
git commit -m "Update website"
git push origin main

# GitHub Pages will auto-deploy in 1-2 minutes
```

## 🚀 GitHub Actions Workflow

The repository includes a GitHub Actions workflow (`.github/workflows/pages.yml`) that:

- Triggers on pushes to `main` branch
- Only runs when `docs/` files change
- Automatically deploys to GitHub Pages
- Can be manually triggered from Actions tab

### View Deployment Status

1. Go to **Actions** tab in your repository
2. Click on the latest workflow run
3. See deployment status and logs

## 📁 Site Structure

```
docs/
├── index.html              # Landing page
├── getting-started.html    # Documentation
├── styles.css             # Shared styles
├── _config.yml            # GitHub Pages config
├── .nojekyll              # Disable Jekyll processing
└── README.md              # Documentation
```

## 🎨 Customization

### Update Content

Edit the HTML files:
- `docs/index.html` - Landing page
- `docs/getting-started.html` - Documentation

### Update Styles

Edit `docs/styles.css` to change colors, fonts, layout, etc.

### Add New Pages

1. Create new HTML file in `docs/`
2. Link to it from existing pages
3. Add navigation in navbar

## 🐛 Troubleshooting

### Site Not Deploying

1. Check GitHub Actions tab for errors
2. Verify `docs/` folder exists in main branch
3. Ensure GitHub Pages is enabled in settings
4. Check that `.nojekyll` file exists

### 404 Errors

1. Verify file paths are correct
2. Check that files are in `docs/` directory
3. Ensure files are committed and pushed

### Styling Issues

1. Clear browser cache
2. Check browser console for errors
3. Verify CSS file is loading

### Custom Domain Not Working

1. Verify DNS records are correct
2. Wait for DNS propagation (up to 24 hours)
3. Check CNAME file in docs/ directory
4. Ensure "Enforce HTTPS" is enabled

## 📊 Analytics (Optional)

To add Google Analytics:

1. Get your GA tracking ID
2. Add to `docs/index.html` before `</head>`:

```html
<!-- Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id=GA_MEASUREMENT_ID"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'GA_MEASUREMENT_ID');
</script>
```

## 🔗 Useful Links

- **Your Site**: https://ryanbarrett.github.io/salutations/
- **GitHub Pages Docs**: https://docs.github.com/en/pages
- **Custom Domains**: https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site
- **GitHub Actions**: https://docs.github.com/en/actions

## ✅ Checklist

- [ ] Enable GitHub Pages in repository settings
- [ ] Verify site is live at GitHub Pages URL
- [ ] Test all pages and links
- [ ] Check mobile responsiveness
- [ ] (Optional) Set up custom domain
- [ ] (Optional) Add analytics
- [ ] Share your site! 🎉

## 🎉 Success!

Your Autonomous Git website is now live! Share it with the world:

- Tweet about it
- Post on LinkedIn
- Share in developer communities
- Add to your portfolio

---

**Questions?** Open an issue on GitHub or check the [GitHub Pages documentation](https://docs.github.com/en/pages).
