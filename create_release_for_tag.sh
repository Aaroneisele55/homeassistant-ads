#!/usr/bin/env bash
# Helper script to create a GitHub Release for an existing git tag
# Usage: ./create_release_for_tag.sh <tag_name>
# Example: ./create_release_for_tag.sh v1.1.3

set -e

if [ -z "$1" ]; then
  echo "Usage: $0 <tag_name>"
  echo "Example: $0 v1.1.3"
  exit 1
fi

TAG="$1"
VERSION="${TAG#v}"  # Remove 'v' prefix

echo "Creating GitHub Release for tag: $TAG (version $VERSION)"

# Check if tag exists
if ! git rev-parse "$TAG" >/dev/null 2>&1; then
  echo "Error: Tag '$TAG' does not exist"
  exit 1
fi

# Extract changelog content for this version
# Using awk -v to safely pass VERSION variable and exact pattern matching
CHANGELOG_CONTENT=$(awk -v ver="$VERSION" '
  /^## \[/ {
    if (found) exit;
    # Use exact matching with escaped brackets for robustness
    if (index($0, "[" ver "]") > 0) {
      found=1;
      next;
    }
  }
  found && /^## \[/ { exit }
  found { print }
' CHANGELOG.md)

# If no specific version section found, use a default message
if [ -z "$CHANGELOG_CONTENT" ]; then
  CHANGELOG_CONTENT="See [CHANGELOG.md](CHANGELOG.md) for details."
fi

# Save to temporary file
TEMP_FILE=$(mktemp)

# Set up trap to ensure cleanup on exit (success or failure)
trap 'rm -f "$TEMP_FILE"' EXIT

echo "$CHANGELOG_CONTENT" > "$TEMP_FILE"

echo "Release notes:"
echo "---"
cat "$TEMP_FILE"
echo "---"

# Create the release using GitHub CLI
echo ""
echo "Creating release..."
gh release create "$TAG" \
  --title "$TAG" \
  --notes-file "$TEMP_FILE" \
  --verify-tag

echo "✅ GitHub Release created successfully for $TAG"
