# DateMe blog automation

Three rungs on the same ladder — climb when ready:

## Rung 1 (now, Option A): one command, human-gated
```sh
.venv/bin/python scripts/generate_post.py     # writes + lints + builds the next backlog post
# read blog/src/<slug>.md, edit if needed, then:
./scripts/deploy.sh                            # build + vercel --prod + IndexNow ping
```
Topics come from `blog/topics.txt` (first slug without a file wins). Pass a custom
topic inline: `generate_post.py "my-slug | My Title | target query/angle"`.

The generator runs `claude -p` headlessly (model: sonnet, tools: WebSearch/WebFetch/
Read/Write only) with `automation/post-prompt.md` — the same research-verified,
banned-phrase-guarded spec the first five posts were written to. A lint gate
(frontmatter lengths, word count, FAQ present, banned phrases/competitor names,
source links) quarantines failures to `.md.rejected` instead of building them.

## Rung 2: scheduled drafts on the Mac mini (still human-gated)
Target machine: **mhnds-mac-mini** (Tailscale: `mhnds-mac-mini.tail881b7b.ts.net` /
`100.80.31.105`; enable Tailscale SSH on it to drive setup remotely). On the mini:
```sh
git clone https://github.com/MHNDhq/dateme-site.git ~/dateme-site
sh ~/dateme-site/automation/setup-mini.sh   # venv, deps, claude check, launchd install
```
Every Monday 09:00 it generates a post and commits it to an `auto-post/<stamp>-<slug>`
branch + sends a macOS notification. You review, merge, `./scripts/deploy.sh`. Nothing
publishes on its own. Review remotely from any machine on the tailnet:
`ssh mhnds-mac-mini.tail881b7b.ts.net` (or open the repo in a Claude Code session there
and ask it to show the draft). Keep the mini's Tailscale key from expiring (currently
~2 months) or set the device to not expire in the admin console.

## Rung 3: fully unattended (the Max-tweet mode)
Uncomment the `AUTO_PUBLISH` block in the plist (vercel CLI must be logged in on the
mini). The weekly run then commits to main, deploys to prod, and pings IndexNow.
The lint gate is the only reviewer — flip this only once rung-2 drafts have been
consistently clean for a few weeks.

Test any rung manually: `sh scripts/weekly_run.sh` (or `AUTO_PUBLISH=1 sh scripts/weekly_run.sh`).
