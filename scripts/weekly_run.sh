#!/bin/sh
# Weekly blog automation entry point (Mac mini ready).
#
# Default (human-gated, Option A): generate + lint + build one post, commit it
# to a review branch, and notify — nothing is published.
# Set AUTO_PUBLISH=1 to go fully unattended: commit to main, deploy to Vercel
# prod, and ping IndexNow.
#
# Requirements on the machine running this: claude CLI logged in,
# and (for AUTO_PUBLISH) vercel CLI logged in + linked to the project.
set -e
export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"
cd "$(dirname "$0")/.."

LOGDIR=automation/logs
mkdir -p "$LOGDIR"
STAMP=$(date +%Y%m%d-%H%M%S)

notify() {
  osascript -e "display notification \"$1\" with title \"DateMe blog\"" 2>/dev/null || true
  echo "$1"
}

if ! .venv/bin/python scripts/generate_post.py >"$LOGDIR/$STAMP.log" 2>&1; then
  notify "Post generation FAILED — see $LOGDIR/$STAMP.log"
  exit 1
fi

SLUG=$(ls -t blog/src/*.md | head -1 | xargs basename | sed 's/\.md$//')

if [ "$AUTO_PUBLISH" = "1" ]; then
  git add blog/ sitemap.xml llms.txt
  git commit -m "blog: auto-publish $SLUG (weekly run)"
  ./scripts/deploy.sh >>"$LOGDIR/$STAMP.log" 2>&1
  notify "Published: $SLUG (live + IndexNow pinged)"
else
  BRANCH="auto-post/$STAMP-$SLUG"
  git checkout -b "$BRANCH"
  git add blog/ sitemap.xml llms.txt
  git commit -m "blog draft: $SLUG (weekly run — review before deploy)"
  git checkout -
  notify "Draft ready on branch $BRANCH — review, merge, then scripts/deploy.sh"
fi
