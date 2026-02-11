#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="/Users/ashimaverma/visionflow"
MESSAGE="${1:-chore: sync changes}"

git -C "$REPO_DIR" add -A

if git -C "$REPO_DIR" diff --cached --quiet; then
  echo "No changes to commit."
  exit 0
fi

git -C "$REPO_DIR" commit -m "$MESSAGE"
git -C "$REPO_DIR" push
echo "Pushed to origin/main."
