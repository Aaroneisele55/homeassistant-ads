# Version Management Guide

## Overview

This project uses **Semantic Versioning** (SemVer 2.0.0) with automated version bumping. The versioning system ensures consistency across all version identifiers and automatically creates git tags.

## Version Format

Versions follow the format: `MAJOR.MINOR.PATCH`

- **MAJOR**: Incompatible API changes, breaking changes
- **MINOR**: New features, backward-compatible functionality
- **PATCH**: Bug fixes, backward-compatible fixes

## Automated Version Bumping

### For AI Agents

When completing a task, AI agents should:

1. **Use appropriate commit message prefixes** or **PR labels** to trigger automatic version bumps
2. **Update the CHANGELOG.md** with changes under an `[Unreleased]` section
3. The GitHub Actions workflow will automatically:
   - Detect the version bump type
   - Update `manifest.json` and `pyproject.toml`
   - Move `[Unreleased]` changes to a versioned section in `CHANGELOG.md`
   - Create a git tag
   - Commit and push all changes

### Version Bump Detection

The system automatically detects the version bump type from:

#### 1. **PR Labels** (Highest Priority)
- `major` → Major version bump
- `minor` → Minor version bump  
- `patch` → Patch version bump

#### 2. **Commit Message Prefixes**
- `[major]` or `BREAKING CHANGE` or `breaking` → Major bump
- `[minor]` or `feat:` or `feature:` → Minor bump
- `[patch]` or `fix:` or `bugfix:` or `hotfix:` → Patch bump

#### 3. **Conventional Commits**
- `feat!:` → Major bump (breaking feature)
- `feat:` or `feat(scope):` → Minor bump
- `fix:` or `fix(scope):` → Patch bump
- `bugfix:` or `hotfix:` → Patch bump

#### 4. **Default Behavior**
- If no indicator is found, defaults to **patch** bump
- Commits with "Bump version to" in the message are skipped to prevent loops

### Examples

#### Example 1: Bug Fix (Patch Bump)
```bash
# Commit message
fix: resolve ADS connection timeout issue

# Or with conventional commit
fix(hub): handle connection timeout gracefully
```

#### Example 2: New Feature (Minor Bump)
```bash
# Commit message
feat: add support for new number entity type

# Or with prefix
[minor] Add number entity support
```

#### Example 3: Breaking Change (Major Bump)
```bash
# Commit message
BREAKING CHANGE: remove deprecated YAML configuration

# Or with conventional commit
feat!: redesign configuration flow with breaking changes

# Or with prefix
[major] Remove support for legacy configuration format
```

## Manual Version Bumping

### Using the bump_version.py Script

For manual version bumps or local testing:

```bash
# Dry run (see what would change)
python bump_version.py patch --dry-run

# Bump patch version (2.0.0 → 2.0.1)
python bump_version.py patch

# Bump minor version (2.0.1 → 2.1.0)
python bump_version.py minor

# Bump major version (2.1.0 → 3.0.0)
python bump_version.py major

# Bump without creating git tag
python bump_version.py patch --no-tag
```

The script will:
1. Update `custom_components/ads_custom/manifest.json`
2. Update `pyproject.toml`
3. Move `[Unreleased]` section to versioned section in `CHANGELOG.md` (if it exists)
4. Create a git tag (unless `--no-tag` is specified)
5. Print next steps for committing and pushing

### After Manual Bump

```bash
# Review changes
git diff

# Commit (include [skip ci] to prevent automatic bump)
git add -A
git commit -m "Bump version to X.Y.Z [skip ci]"

# Push with tags
git push && git push --tags
```

## CHANGELOG.md Management

### For AI Agents

When making changes, add entries to the `[Unreleased]` section at the top of `CHANGELOG.md`:

```markdown
## [Unreleased]

### Added
- New feature description

### Changed
- Changed functionality description

### Fixed
- Bug fix description

### Removed
- Removed functionality description
```

The automated workflow will convert this to a versioned section when bumping the version.

### Categories

Use these standard categories:
- **Added**: New features
- **Changed**: Changes to existing functionality
- **Deprecated**: Soon-to-be removed features
- **Removed**: Removed features
- **Fixed**: Bug fixes
- **Security**: Security fixes

## Version Files

The version is stored in **two locations** and must stay synchronized:

1. **`custom_components/ads_custom/manifest.json`**
   ```json
   {
     "version": "2.0.0"
   }
   ```

2. **`pyproject.toml`**
   ```toml
   [project]
   version = "2.0.0"
   ```

Both files are automatically updated by the versioning tools.

## Git Tags

Git tags follow the format `vX.Y.Z` (e.g., `v2.0.0`).

Tags are automatically created by:
- The GitHub Actions workflow when changes are pushed to main
- The `bump_version.py` script (unless `--no-tag` is used)

## Workflow Triggers

The auto-versioning workflow runs when:

1. **Direct push to main branch** with changes to:
   - `custom_components/**`
   - `tests/**`
   - Any `.py` files

2. **Pull request merged to main** with changes to the same paths

## Best Practices for AI Agents

1. ✅ **Always add changes to `[Unreleased]` section in CHANGELOG.md**
2. ✅ **Use clear, descriptive commit messages with appropriate prefixes**
3. ✅ **Apply PR labels when creating pull requests**
4. ✅ **Use conventional commit format when applicable**
5. ✅ **For breaking changes, clearly mark them with `BREAKING CHANGE` or `!`**
6. ❌ **Don't manually edit version numbers** (let the automation handle it)
7. ❌ **Don't create git tags manually** (automation creates them)
8. ❌ **Don't skip updating the CHANGELOG** (it's the user-facing record of changes)

## Troubleshooting

### Version Mismatch Between Files

If `manifest.json` and `pyproject.toml` have different versions:

```bash
# Fix by running the script (it will sync to manifest.json version)
python bump_version.py patch --dry-run
```

### Workflow Didn't Trigger

Check that:
1. Changes were pushed to the `main` branch
2. Changes affected files in the trigger paths
3. Commit message doesn't contain "Bump version to" (which would skip versioning)
4. The workflow has proper permissions (needs `contents: write`)

### Manual Recovery

If automation fails, you can manually bump:

```bash
python bump_version.py [major|minor|patch]
git add -A
git commit -m "Bump version to X.Y.Z [skip ci]"
git push && git push --tags
```

## References

- [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html)
- [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
- [Conventional Commits](https://www.conventionalcommits.org/)
