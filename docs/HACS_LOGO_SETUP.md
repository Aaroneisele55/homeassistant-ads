# Quick Setup: Display Icons in HACS

**Problem**: The integration logo doesn't appear in HACS even though the files are in the repository.

**Solution**: HACS uses GitHub's social preview image, not files in your repo. Follow these steps:

## Step-by-Step Instructions

### 1. Go to Repository Settings

Visit your repository settings:
```
https://github.com/Aaroneisele55/homeassistant-ads/settings
```

Or:
1. Open your repository on GitHub
2. Click the **Settings** tab (requires admin access)

### 2. Find Social Preview Section

1. Scroll down to the **Social preview** section (near the top of settings)
2. Look for the "Image" area

### 3. Upload the Logo

1. Click **Upload an image** or **Edit**
2. Select the logo file from `custom_components/ads_custom/logo.png`
   - Or download it from: `https://raw.githubusercontent.com/Aaroneisele55/homeassistant-ads/main/custom_components/ads_custom/logo.png`
3. Crop if needed (GitHub recommends 1200×630, but smaller images work)
4. Click **Save**

### 4. Wait for Cache Refresh

- HACS caches repository data
- The logo may take **5-15 minutes** to appear
- You can speed this up by:
  - Removing and re-adding the repository in HACS
  - Clearing HACS cache (if your HACS version supports it)

## Visual Confirmation

Once set up correctly, you'll see the logo in:

- ✅ HACS integration listing
- ✅ Repository page in HACS
- ✅ GitHub repository main page header
- ✅ GitHub social media shares

## Troubleshooting

**Q: I set the social preview but it's not showing in HACS**

- Wait 15-30 minutes for GitHub's CDN to update
- Remove and re-add the custom repository in HACS
- Check that you uploaded to the correct repository

**Q: The image looks stretched or blurry**

- Use an image with 1200×630 pixels for best results
- The current logo.png (447×256) will be scaled by GitHub

**Q: Can I use a different image than the one in the repo?**

- Yes! The GitHub social preview is independent of repo files
- You can create a custom 1200×630 image for better presentation
- The Beckhoff/TwinCAT branding from `logo.png` is recommended for consistency

## Important Note

⚠️ **The `logo.png` file in the repository does NOT automatically appear in HACS.** You **must** set it as the GitHub social preview image manually. This is a GitHub/HACS limitation, not a bug in this integration.

---

Need help? See the full [Icon Setup Guide](ICON_SETUP.md) for detailed information.
