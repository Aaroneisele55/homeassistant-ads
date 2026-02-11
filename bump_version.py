#!/usr/bin/env python3
"""
Version bumping script for homeassistant-ads integration.

This script updates version numbers in manifest.json and pyproject.toml,
and optionally creates a git tag.

Usage:
    python bump_version.py [major|minor|patch] [--no-tag]
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def get_current_version(manifest_path: Path) -> str:
    """Read current version from manifest.json."""
    with open(manifest_path) as f:
        manifest = json.load(f)
    return manifest["version"]


def parse_version(version: str) -> tuple[int, int, int]:
    """Parse semantic version string into (major, minor, patch) tuple."""
    match = re.match(r"^(\d+)\.(\d+)\.(\d+)$", version)
    if not match:
        raise ValueError(f"Invalid version format: {version}")
    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def bump_version(current: str, bump_type: str) -> str:
    """Bump version according to semantic versioning rules."""
    major, minor, patch = parse_version(current)
    
    if bump_type == "major":
        return f"{major + 1}.0.0"
    elif bump_type == "minor":
        return f"{major}.{minor + 1}.0"
    elif bump_type == "patch":
        return f"{major}.{minor}.{patch + 1}"
    else:
        raise ValueError(f"Invalid bump type: {bump_type}")


def update_manifest(manifest_path: Path, new_version: str) -> None:
    """Update version in manifest.json."""
    with open(manifest_path) as f:
        manifest = json.load(f)
    
    manifest["version"] = new_version
    
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")  # Add trailing newline
    
    print(f"✓ Updated {manifest_path}")


def update_pyproject(pyproject_path: Path, new_version: str) -> None:
    """Update version in pyproject.toml."""
    content = pyproject_path.read_text()
    
    # Replace version line
    new_content = re.sub(
        r'^version = "[^"]+"',
        f'version = "{new_version}"',
        content,
        flags=re.MULTILINE
    )
    
    pyproject_path.write_text(new_content)
    print(f"✓ Updated {pyproject_path}")


def update_changelog(changelog_path: Path, new_version: str) -> None:
    """Add a new version section to CHANGELOG.md if [Unreleased] section exists."""
    content = changelog_path.read_text()
    
    # Check if there's an [Unreleased] section with content
    unreleased_pattern = r"## \[Unreleased\]\s*\n(.*?)(?=\n## \[|$)"
    match = re.search(unreleased_pattern, content, re.DOTALL)
    
    if match and match.group(1).strip():
        # There's unreleased content, convert it to a version section
        today = datetime.now().strftime("%Y-%m-%d")
        new_section = f"## [{new_version}] - {today}"
        
        # Replace [Unreleased] with the new version
        new_content = content.replace("## [Unreleased]", new_section, 1)
        
        # Add a new [Unreleased] section at the top
        insert_pos = new_content.find(f"## [{new_version}]")
        new_content = (
            new_content[:insert_pos] +
            "## [Unreleased]\n\n" +
            new_content[insert_pos:]
        )
        
        changelog_path.write_text(new_content)
        print(f"✓ Updated {changelog_path} with version {new_version}")
    else:
        print(f"ℹ No [Unreleased] changes found in {changelog_path}, skipping update")


def create_git_tag(version: str, dry_run: bool = False) -> None:
    """Create and push a git tag for the new version."""
    tag_name = f"v{version}"
    
    if dry_run:
        print(f"ℹ Dry run: Would create tag {tag_name}")
        return
    
    try:
        # Check if tag already exists
        result = subprocess.run(
            ["git", "tag", "-l", tag_name],
            capture_output=True,
            text=True,
            check=True
        )
        
        if result.stdout.strip():
            print(f"⚠ Tag {tag_name} already exists")
            return
        
        # Create annotated tag
        subprocess.run(
            ["git", "tag", "-a", tag_name, "-m", f"Release version {version}"],
            check=True
        )
        print(f"✓ Created git tag {tag_name}")
        
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to create git tag: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Bump version in homeassistant-ads integration"
    )
    parser.add_argument(
        "bump_type",
        choices=["major", "minor", "patch"],
        help="Type of version bump to perform"
    )
    parser.add_argument(
        "--no-tag",
        action="store_true",
        help="Don't create a git tag"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes"
    )
    
    args = parser.parse_args()
    
    # Get repository root
    repo_root = Path(__file__).parent
    manifest_path = repo_root / "custom_components" / "ads_custom" / "manifest.json"
    pyproject_path = repo_root / "pyproject.toml"
    changelog_path = repo_root / "CHANGELOG.md"
    
    # Verify files exist
    if not manifest_path.exists():
        print(f"✗ manifest.json not found at {manifest_path}", file=sys.stderr)
        sys.exit(1)
    
    if not pyproject_path.exists():
        print(f"✗ pyproject.toml not found at {pyproject_path}", file=sys.stderr)
        sys.exit(1)
    
    # Get current version
    current_version = get_current_version(manifest_path)
    print(f"Current version: {current_version}")
    
    # Calculate new version
    new_version = bump_version(current_version, args.bump_type)
    print(f"New version: {new_version}")
    
    if args.dry_run:
        print("\n🔍 Dry run - no changes made")
        print(f"Would update manifest.json: {current_version} → {new_version}")
        print(f"Would update pyproject.toml: {current_version} → {new_version}")
        if changelog_path.exists():
            print(f"Would update {changelog_path}")
        if not args.no_tag:
            print(f"Would create git tag: v{new_version}")
        return
    
    # Update version files
    print("\n📝 Updating version files...")
    update_manifest(manifest_path, new_version)
    update_pyproject(pyproject_path, new_version)
    
    # Update changelog if it exists
    if changelog_path.exists():
        update_changelog(changelog_path, new_version)
    
    # Create git tag
    if not args.no_tag:
        print("\n🏷️  Creating git tag...")
        create_git_tag(new_version)
    
    print(f"\n✅ Version bumped successfully: {current_version} → {new_version}")
    print("\nNext steps:")
    print("  1. Review the changes: git diff")
    print("  2. Commit the changes: git add -A && git commit -m 'Bump version to {}'".format(new_version))
    if not args.no_tag:
        print("  3. Push with tags: git push && git push --tags")
    else:
        print("  3. Push changes: git push")


if __name__ == "__main__":
    main()
