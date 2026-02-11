# HACS Version Detection Fix

## Issue
HACS (Home Assistant Community Store) wasn't picking up versions despite git tags being created in the repository.

## Root Cause
HACS requires **GitHub Releases** to detect and display available versions. While our automated version bump workflow was creating git tags (e.g., `v1.1.3`), it was not creating corresponding GitHub Releases.

**Key difference:**
- **Git tags**: Lightweight references in the git repository
- **GitHub Releases**: GitHub's release feature that packages code, creates downloadable archives, and provides release notes

HACS specifically queries the GitHub Releases API to determine available versions. Git tags alone are not sufficient.

## Solution
The `.github/workflows/version-bump.yml` workflow has been updated to automatically create a GitHub Release whenever a version is bumped. The workflow now:

1. Bumps the version in `manifest.json` and `pyproject.toml`
2. Updates the `CHANGELOG.md`
3. Commits the changes
4. Creates a git tag (e.g., `v1.1.3`)
5. Pushes the commit and tag
6. **NEW:** Extracts the changelog section for the version
7. **NEW:** Creates a GitHub Release with the extracted changelog

## Verifying the Fix

### Check if GitHub Releases exist
Visit: https://github.com/Aaroneisele55/homeassistant-ads/releases

You should see releases for each version (v1.1.3, v1.1.2, etc.).

### Check what HACS sees
The GitHub Releases API endpoint that HACS uses:
```bash
curl -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/Aaroneisele55/homeassistant-ads/releases
```

This should return a JSON array with release information.

## Creating Releases for Existing Tags

If you have existing git tags without corresponding GitHub Releases (like v1.1.3), you can create releases manually:

### Option 1: Using the helper script
```bash
./create_release_for_tag.sh v1.1.3
```

This script:
- Extracts the relevant section from CHANGELOG.md
- Creates a GitHub Release for the tag
- Uses the GitHub CLI (`gh`)

### Option 2: Using GitHub CLI directly
```bash
gh release create v1.1.3 \
  --title "v1.1.3" \
  --notes "See [CHANGELOG.md](CHANGELOG.md) for details." \
  --verify-tag
```

### Option 3: Using the GitHub Web UI
1. Go to https://github.com/Aaroneisele55/homeassistant-ads/releases
2. Click "Draft a new release"
3. Select the existing tag (e.g., `v1.1.3`)
4. Add a title and description
5. Click "Publish release"

## Testing

After creating releases:
1. Wait a few minutes for HACS to refresh its cache
2. Check HACS in Home Assistant
3. The version should now be visible in HACS
4. HACS should show update notifications when new versions are available

## Future Versions

All future versions will automatically get GitHub Releases created by the workflow, so this issue should not recur.

## References

- [HACS Documentation](https://hacs.xyz/docs/publish/integration)
- [GitHub Releases Documentation](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases)
- [GitHub REST API - Releases](https://docs.github.com/en/rest/releases/releases)
