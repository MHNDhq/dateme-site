#!/bin/sh
# Build the blog, deploy to Vercel prod, ping IndexNow.
set -e
export PATH=/opt/homebrew/bin:$PATH
cd "$(dirname "$0")/.."
.venv/bin/python scripts/build_blog.py
vercel --prod
.venv/bin/python scripts/indexnow_ping.py
