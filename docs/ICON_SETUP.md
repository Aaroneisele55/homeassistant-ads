# Icon and Logo Setup Guide

This guide explains how to properly display the ADS Custom integration icons in Home Assistant and HACS.

## Files Included

The integration includes two branding image files:

- **`icon.png`** (256×256 pixels) - Used by Home Assistant UI
- **`logo.png`** (447×256 pixels) - Used by HACS and documentation

Both files are located in: `custom_components/ads_custom/`

## Home Assistant UI Display

### How It Works

Home Assistant **automatically detects** the `icon.png` file if it's placed in the integration directory. No additional configuration in `manifest.json` is required for custom integrations.

### Requirements

✅ **File location**: `custom_components/ads_custom/icon.png`  
✅ **File format**: PNG  
✅ **Recommended size**: 256×256 pixels  
✅ **Color mode**: RGB or indexed color (8-bit)

### Where the Icon Appears

Once properly installed, the icon should appear in:

1. **Settings → Devices & Services** - Integration card
2. **Integration configuration pages** - Header area
3. **Device detail pages** - If devices are registered

### Troubleshooting

If the icon doesn't appear in Home Assistant:

1. **Verify file exists**: Check that `custom_components/ads_custom/icon.png` is present
2. **Check file permissions**: Ensure Home Assistant can read the file
3. **Clear browser cache**: Force-refresh your browser (Ctrl+F5 or Cmd+Shift+R)
4. **Restart Home Assistant**: Perform a full restart, not just a reload
5. **Check HA version**: Ensure you're running Home Assistant 2021.1 or later
6. **Verify installation**: Make sure the entire `ads_custom` folder was copied correctly

### Alternative: Using Material Design Icons

If you prefer not to use custom PNG files, you can use Material Design Icons by adding an `icon` field to `manifest.json`:

```json
{
  "domain": "ads_custom",
  "icon": "mdi:lightning-bolt"
}
```

However, this will **override** the custom `icon.png` file.

## HACS Display

### How It Works

**HACS does NOT use the `logo.png` file from your repository.** Instead, it uses the **GitHub repository's social preview image**.

### Setup Steps

To display the logo in HACS:

1. **Go to GitHub repository settings**:
   - Navigate to: `https://github.com/Aaroneisele55/homeassistant-ads/settings`
   - Or click: **Settings** (if you have admin access)

2. **Upload social preview image**:
   - Scroll to the **Social preview** section
   - Click **Upload an image**
   - Choose the `logo.png` file (or any 1200×630 px image)
   - Save the changes

3. **Wait for HACS to refresh**:
   - HACS caches repository information
   - The logo may take a few minutes to appear
   - You can force a refresh by re-adding the repository

### Image Requirements for HACS

- **Recommended size**: 1200×630 pixels (GitHub's social preview standard)
- **Alternative sizes**: 640×320 px minimum
- **Format**: PNG or JPG
- **File size**: Under 1 MB

### Where the Logo Appears in HACS

Once the GitHub social preview is set:

- HACS integration listing page
- Repository detail view in HACS
- GitHub repository page header

### Important Notes

⚠️ **The `logo.png` file in the repository is for documentation purposes only.** HACS will not automatically use it. You **must** set it as the GitHub social preview image.

## Summary

| Platform | File Used | Configuration Required |
|----------|-----------|------------------------|
| **Home Assistant UI** | `icon.png` in integration folder | ✅ Automatic detection (no manifest changes needed) |
| **HACS** | GitHub social preview image | ⚠️ Manual: Set in GitHub repository settings |
| **Documentation** | `logo.png` in repo | ✅ Already included |

## Verification Checklist

### Home Assistant
- [ ] File `custom_components/ads_custom/icon.png` exists
- [ ] File is 256×256 PNG format
- [ ] Home Assistant has been restarted
- [ ] Browser cache has been cleared
- [ ] Icon appears in Settings → Devices & Services

### HACS
- [ ] Repository social preview image set in GitHub settings
- [ ] Image is at least 640×320 pixels (recommended: 1200×630)
- [ ] HACS cache has refreshed (wait a few minutes or re-add repo)
- [ ] Logo appears in HACS integration list

## Additional Resources

- [Home Assistant Brands Repository](https://github.com/home-assistant/brands)
- [GitHub Social Preview Images Guide](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/customizing-your-repositorys-social-media-preview)
- [HACS Documentation](https://hacs.xyz/)

---

*For more information about the branding assets and their licensing, see [ATTRIBUTION.md](../ATTRIBUTION.md).*
