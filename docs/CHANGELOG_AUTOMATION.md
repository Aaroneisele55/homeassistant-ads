# Changelog Automation

This document explains how the automated changelog generation works in this project.

## Overview

The project uses an automated system to maintain the `CHANGELOG.md` file. The system ensures that all changes are documented, whether they come from pull requests or direct commits to main.

## How It Works

### Automated Workflow

When code is pushed to main or a PR is merged, the GitHub Actions workflow automatically:

1. **Checks the [Unreleased] section**
   - If it contains changes, those changes are moved to a new version section
   - If it's empty, the workflow extracts the commit message and adds it

2. **Categorizes changes** based on commit message prefixes:
   - `fix:`, `bugfix:`, `hotfix:` → **Fixed**
   - `feat:`, `feature:` → **Added**
   - `remove:`, `delete:` → **Removed**
   - `security:`, `sec:` → **Security**
   - Everything else → **Changed**

3. **Creates a version section** with:
   - Version number (e.g., `[1.2.3]`)
   - Release date
   - Categorized changes

4. **Commits and pushes** the updated CHANGELOG.md along with version bumps

### Manual Updates (Recommended)

For better changelog quality, we recommend manually updating the `[Unreleased]` section:

```markdown
## [Unreleased]

### Added
- New feature X that does Y
- Support for Z protocol

### Fixed
- Bug where connection would timeout
- Memory leak in hub component
```

The workflow will move these entries to the appropriate version section when triggered.

### Automatic Extraction (Fallback)

If you forget to update `[Unreleased]`, the workflow will automatically:

1. Extract your commit message
2. Clean up conventional commit prefixes (e.g., `feat:`, `fix:`)
3. Categorize the change appropriately
4. Add it to the changelog

**Example:**
- Commit message: `fix: resolve connection timeout issue`
- Becomes: `- resolve connection timeout issue` under `### Fixed`

## Commit Message Best Practices

To get the best automatic changelog entries, use clear commit messages:

### Good Examples

```bash
# Feature addition
feat: add support for REAL data type
feature: implement automatic reconnection

# Bug fixes
fix: resolve connection timeout after 60 seconds
bugfix: handle null pointer in hub initialization
hotfix: patch critical security vulnerability

# Removals
remove: deprecated YAML configuration option
delete: unused helper functions

# Security
security: patch SQL injection vulnerability
sec: update pyads to fix CVE-2024-1234
```

### Avoid

```bash
# Too vague
chore: updates
fix: bug

# No prefix (will be categorized as "Changed")
Updated some files
Fixed stuff
```

## Workflow Details

### Trigger Conditions

The workflow runs when:
- Code is pushed directly to the `main` branch
- A pull request is merged to `main`
- Changes are made to Python files, tests, or custom components

### Version Bump Detection

The workflow automatically determines the version bump type:

1. **From PR labels** (highest priority):
   - `major` → Major version bump
   - `minor` → Minor version bump
   - `patch` → Patch version bump

2. **From commit messages**:
   - `BREAKING CHANGE` or `[major]` → Major
   - `feat:` or `[minor]` → Minor
   - `fix:` or `[patch]` → Patch

3. **Default**: Patch bump if no indicator is found

### Files Updated

The workflow automatically updates:
- `custom_components/ads_custom/manifest.json` (version)
- `pyproject.toml` (version)
- `CHANGELOG.md` (changelog entries)
- Creates git tag (e.g., `v1.2.3`)
- Creates GitHub Release with release notes

## Troubleshooting

### Empty Version Sections

If you see empty version sections in the changelog:
- This should no longer happen with the updated workflow
- The workflow now always populates changelog entries

**Note for manual use**: If you run `bump_version.py` manually without first populating the `[Unreleased]` section, it will create an empty version section. The script will print "Created empty version section" as a warning. To avoid this, either:
1. Manually add entries to `[Unreleased]` before running the script
2. Use the GitHub Actions workflow which automatically populates the section

### Missing Changes

If a change isn't in the changelog:
- Check if the commit had `[skip ci]` in the message
- Verify the workflow ran successfully in GitHub Actions
- The change might be in the next version section

### Wrong Category

If a change is in the wrong category:
- Update the commit message prefix to match the desired category
- Or manually update the `[Unreleased]` section before committing

### Existing Content Not Updated

**Important limitation**: If the `[Unreleased]` section already contains manually-added content, the automatic extraction step is skipped entirely. This means:

- The commit message is not added to the changelog (the existing content is preserved)
- The category is not automatically determined from the commit prefix
- This is by design to avoid overwriting or conflicting with manual entries

**Example scenario**: You manually add a "Fixed" entry to `[Unreleased]`, then commit with `feat: new feature`. The workflow will:
1. See that `[Unreleased]` has content
2. Skip the automatic extraction
3. Move the existing "Fixed" entry to the version section
4. The "feat: new feature" commit will NOT be in the changelog

**Recommendation**: When manually updating `[Unreleased]`, include all changes (both manual and from commits) to ensure completeness.

## Related Documentation

- [VERSION_MANAGEMENT.md](../VERSION_MANAGEMENT.md) - Complete version management guide
- [Keep a Changelog](https://keepachangelog.com/) - Changelog format standard
- [Conventional Commits](https://www.conventionalcommits.org/) - Commit message standard
