#!/usr/bin/env bash
# Publish AnomalyMatrix GitHub Release from VERSION file.
# Usage (from repo root, on master, clean tree):
#   ./scripts/publish_github_release.sh [--draft] [--dry-run]
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

DRAFT=false
DRY_RUN=false
for arg in "$@"; do
  case "$arg" in
    --draft) DRAFT=true ;;
    --dry-run) DRY_RUN=true ;;
    -h|--help)
      echo "Usage: $0 [--draft] [--dry-run]"
      exit 0
      ;;
    *)
      echo "Unknown arg: $arg" >&2
      exit 1
      ;;
  esac
done

VERSION="$(tr -d '\r\n' < VERSION)"
TAG="v${VERSION}"
NOTES="docs/RELEASE_NOTES_v${VERSION}.md"
TITLE="AnomalyMatrix ${TAG}"

if [[ ! -f "$NOTES" ]]; then
  echo "Missing release notes: $NOTES" >&2
  exit 1
fi

if [[ "$(git rev-parse --abbrev-ref HEAD)" != "master" ]]; then
  echo "Warn: not on master (current: $(git rev-parse --abbrev-ref HEAD))" >&2
fi

if [[ -n "$(git status --porcelain)" ]]; then
  echo "Working tree not clean — commit or stash first." >&2
  exit 1
fi

echo "==> Building installer"
bash scripts/build_installer.sh
INSTALLER="dist/AnomalyMatrix-installer-v${VERSION}.run"
LEGACY="dist/AnomalyMatrix-installer.run"
SUMS="dist/SHA256SUMS.txt"
sha256sum "$INSTALLER" "$LEGACY" > "$SUMS"
cat "$SUMS"

if [[ "$DRY_RUN" == "true" ]]; then
  echo "==> Dry-run: would create tag $TAG and GitHub release"
  echo "    title: $TITLE"
  echo "    notes: $NOTES"
  echo "    assets: $INSTALLER $LEGACY $SUMS"
  echo "    draft: $DRAFT"
  exit 0
fi

if git rev-parse "$TAG" >/dev/null 2>&1; then
  echo "Tag $TAG already exists locally."
else
  echo "==> Creating annotated tag $TAG"
  git tag -a "$TAG" -m "Release ${TAG}"
fi

echo "==> Pushing tag $TAG"
git push origin "$TAG"

GH_ARGS=(release create "$TAG" --title "$TITLE" --notes-file "$NOTES" "$INSTALLER" "$LEGACY" "$SUMS")
if [[ "$DRAFT" == "true" ]]; then
  GH_ARGS+=(--draft)
fi

echo "==> Creating GitHub release"
gh "${GH_ARGS[@]}"

echo "Done: https://github.com/TheRealByteCommander/AnomalyMatrix/releases/tag/${TAG}"
