# Claude Code Config

My personal Claude Code configuration synced across devices.

## Quick Start

```bash
# Clone this repo
git clone git@github.com:YOUR_USERNAME/claude-config.git
cd claude-config

# Install config on this machine
./sync.sh push
```

## Usage

### After making changes locally (on any machine)

```bash
# 1. Pull changes from ~/.claude to repo
./sync.sh pull

# 2. Commit and push
git add -A && git commit -m "Update config" && git push
```

### To get changes on another machine

```bash
# 1. Pull from git
git pull

# 2. Push config to ~/.claude
./sync.sh push

# 3. Restart Claude Code
```

## Commands

| Command | Description |
|---------|-------------|
| `./sync.sh pull` | Copy from `~/.claude` → repo (for committing) |
| `./sync.sh push` | Copy from repo → `~/.claude` (install config) |
| `./sync.sh status` | Show what's synced |

## What's Synced

- `CLAUDE.md` - Main instructions file
- `settings.json` - Settings and permissions
- `rules/` - Custom rules
- `agents/` - Custom agents
- `commands/` - Custom slash commands
- `scripts/` - Helper scripts

## Path Handling

The script automatically handles different paths between Linux/WSL and macOS:

- **In repo:** Paths use placeholder `{{CLAUDE_HOME}}`
- **On push:** Placeholder is replaced with actual `~/.claude` path
- **On pull:** Actual paths are normalized back to placeholder

This means the same config works on both systems! 🎉
