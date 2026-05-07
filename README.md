# Claude Code Config

My personal Claude Code configuration synced across devices.

## Quick Start

```bash
# Clone this repo
git clone git@github.com:YOUR_USERNAME/claude-config.git
cd claude-config

# Install config on this machine
npm run push    # or: pnpm push
```

## Usage

### After making changes locally (on any machine)

```bash
# 1. Pull changes from ~/.claude to repo
npm run pull    # or: pnpm pull

# 2. Commit and push
git add -A && git commit -m "Update config" && git push
```

### To get changes on another machine

```bash
# 1. Pull from git
git pull

# 2. Push config to ~/.claude
npm run push    # or: pnpm push

# 3. Restart Claude Code
```

## Commands

| Command | Description |
|---------|-------------|
| `npm run pull` / `pnpm pull` | Copy from `~/.claude` → repo (for committing) |
| `npm run push` / `pnpm push` | Copy from repo → `~/.claude` (install config) |
| `npm run status` / `pnpm status` | Show what's synced |

## What's Synced

- `CLAUDE.md` - Main instructions file
- `settings.json` - Settings and permissions
- `rules/` - Custom rules
- `agents/` - Custom agents
- `commands/` - Custom slash commands
- `scripts/` - Helper scripts
- `skills/` - Custom skills
- `plugins/installed_plugins.json` + `plugins/known_marketplaces.json` - plugin metadata only (marketplaces and cache are restored automatically on push)

## Path Handling

The script automatically handles different paths between Linux (Ubuntu/WSL) and macOS:

- **In repo:** Paths use placeholder `{{CLAUDE_HOME}}`
- **On push:** Placeholder is replaced with this machine's actual `~/.claude` path
- **On pull:** Any `/Users/<user>/.claude` or `/home/<user>/.claude` path is normalized back to the placeholder — even if it came from a different machine

The pull-side regex catches foreign-system paths too, so a repo polluted by a manual copy from another machine is self-healing on the next pull.

## Plugin Sync

Only the two metadata files (`installed_plugins.json`, `known_marketplaces.json`) are committed. On push the script automatically:

1. `git clone --depth=1` any marketplace listed in `known_marketplaces.json` if its `installLocation` is missing.
2. Copies plugin files from the marketplace into the cache `installPath` if it's empty.

Requires `git` and `jq` on PATH. If either is missing, the metadata still pushes but plugin restore is skipped with a warning.
