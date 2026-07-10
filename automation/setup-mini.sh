#!/bin/sh
# One-shot setup for the always-on Mac mini (mhnds-mac-mini.tail881b7b.ts.net).
# Run ON the mini (locally or over Tailscale SSH):
#   git clone https://github.com/MHNDhq/dateme-site.git ~/dateme-site
#   sh ~/dateme-site/automation/setup-mini.sh
#
# Prereqs the script checks but can't do for you:
#   - claude CLI installed + logged in  (curl -fsSL https://claude.ai/install.sh | bash)
#   - vercel CLI logged in + project linked (only needed for AUTO_PUBLISH rung 3)
set -e
REPO="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO"

echo "== venv + deps"
[ -d .venv ] || python3 -m venv .venv
.venv/bin/pip -q install markdown pillow

echo "== checking claude CLI"
CLAUDE_BIN="${CLAUDE_BIN:-$HOME/.local/bin/claude}"
if [ ! -x "$CLAUDE_BIN" ] && ! command -v claude >/dev/null; then
  echo "!! claude CLI not found — install and log in first:"
  echo "   curl -fsSL https://claude.ai/install.sh | bash && claude"
  exit 1
fi

echo "== smoke test (generates nothing; validates backlog + prompt parse)"
.venv/bin/python - <<'EOF'
import sys; sys.path.insert(0, "scripts")
import importlib.util
spec = importlib.util.spec_from_file_location("gp", "scripts/generate_post.py")
gp = importlib.util.module_from_spec(spec); spec.loader.exec_module(gp)
slug, topic = gp.pick_topic(None)
print(f"   next topic ready: {slug}")
EOF

echo "== installing launchd job (weekly drafts, Mondays 09:00, human-gated)"
PLIST="$HOME/Library/LaunchAgents/com.mhndlabs.dateme-blog.plist"
mkdir -p "$HOME/Library/LaunchAgents" "$REPO/automation/logs"
sed "s|__REPO__|$REPO|g" "$REPO/automation/com.mhndlabs.dateme-blog.plist" > "$PLIST"
launchctl bootout "gui/$(id -u)/com.mhndlabs.dateme-blog" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST"
echo "== done. Test now with: sh $REPO/scripts/weekly_run.sh"
echo "   (rung 3 later: uncomment AUTO_PUBLISH in $PLIST + vercel login)"
