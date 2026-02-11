# HACS Version Detection Fix - Summary

## Issue
HACS (Home Assistant Community Store) was not detecting versions despite git tags being created in the repository.

## Root Cause
**HACS requires GitHub Releases, not just git tags.**

While the repository had a git tag `v1.1.3`, there were no corresponding GitHub Releases. HACS specifically queries the GitHub Releases API to determine available versions, so git tags alone are insufficient.

## Solution Implemented

### 1. Updated GitHub Actions Workflow
Modified `.github/workflows/version-bump.yml` to automatically create GitHub Releases:
- Extracts the relevant changelog section for each new version
- Creates a GitHub Release with the extracted changelog as release notes
- Uses GitHub CLI (`gh`) to create the release
- Uses secure temporary file storage (`${{ runner.temp }}`)

### 2. Created Helper Script
Added `create_release_for_tag.sh` for manually creating releases for existing tags:
```bash
./create_release_for_tag.sh v1.1.3
```

### 3. Added Documentation
Created `docs/HACS_VERSION_FIX.md` with:
- Detailed explanation of the issue
- Solution overview
- Instructions for verifying the fix
- Multiple options for creating releases manually

### 4. Updated Project Documentation
- Updated `CHANGELOG.md` to document this fix
- Updated `README.md` to mention GitHub Releases in version management

## What Happens Now

### Automatic (Future Versions)
All future version bumps will automatically get GitHub Releases created by the updated workflow. No manual intervention needed.

### Manual (Existing Tag v1.1.3)
The existing `v1.1.3` tag needs a GitHub Release created manually. Three options:

**Option 1: Use the helper script** (requires gh CLI authentication)
```bash
./create_release_for_tag.sh v1.1.3
```

**Option 2: Use GitHub CLI directly**
```bash
gh release create v1.1.3 \
  --title "v1.1.3" \
  --notes "See [CHANGELOG.md](CHANGELOG.md) for details." \
  --verify-tag
```

**Option 3: Use GitHub Web UI**
1. Go to https://github.com/Aaroneisele55/homeassistant-ads/releases
2. Click "Draft a new release"
3. Select the existing tag `v1.1.3`
4. Add title and description
5. Click "Publish release"

## Verification

After merging and creating the release for v1.1.3:

1. **Check GitHub Releases page:**
   https://github.com/Aaroneisele55/homeassistant-ads/releases
   
2. **Query the GitHub API (what HACS uses):**
   ```bash
   curl -H "Accept: application/vnd.github.v3+json" \
     https://api.github.com/repos/Aaroneisele55/homeassistant-ads/releases
   ```

3. **Check in HACS:**
   - Wait a few minutes for HACS cache to refresh
   - The version should now be visible
   - Update notifications should appear for new versions

## Files Changed

- `.github/workflows/version-bump.yml` - Added GitHub Release creation
- `create_release_for_tag.sh` - Helper script for manual release creation
- `docs/HACS_VERSION_FIX.md` - Comprehensive documentation
- `CHANGELOG.md` - Documented the fix
- `README.md` - Updated version management section

## Testing Performed

- ✅ Validated workflow YAML syntax
- ✅ Tested changelog extraction for populated sections (v1.1.2)
- ✅ Tested changelog extraction for empty sections (v1.1.3)
- ✅ Verified fallback behavior when no changelog exists
- ✅ Code review completed and feedback addressed
- ✅ CodeQL security scan passed with no issues

## Security Improvements

- Uses `${{ runner.temp }}` instead of `/tmp` for secure temporary file storage in GitHub Actions
- Uses portable shebang (`#!/usr/bin/env bash`) in helper script

## Next Steps

1. **Merge this PR** to enable automatic GitHub Release creation for future versions
2. **Create a release for v1.1.3** using one of the three manual options above
3. **Wait for HACS to refresh** (5-15 minutes) and verify the version appears
4. **Celebrate!** 🎉 All future versions will automatically work with HACS

## References

- [HACS Documentation](https://hacs.xyz/docs/publish/integration)
- [GitHub Releases Documentation](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases)
- [GitHub REST API - Releases](https://docs.github.com/en/rest/releases/releases)
- [Keep a Changelog](https://keepachangelog.com/)
