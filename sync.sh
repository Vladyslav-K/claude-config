#!/bin/bash

# =============================================================================
# Claude Code Config Sync Script
# Syncs configuration between this repo and ~/.claude
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="$SCRIPT_DIR/config"
CLAUDE_DIR="$HOME/.claude"

# Placeholder used in repo files (will be replaced with actual path)
PLACEHOLDER="{{CLAUDE_HOME}}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# =============================================================================
# Helper Functions
# =============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Files and folders to sync
SYNC_ITEMS=(
    "CLAUDE.md"
    "settings.json"
    "rules"
    "agents"
    "commands"
    "scripts"
)

# Files to exclude from sync
EXCLUDE_PATTERNS=(
    ".DS_Store"
    "*.bak"
    "*~"
)

# Build rsync exclude arguments
build_excludes() {
    local excludes=""
    for pattern in "${EXCLUDE_PATTERNS[@]}"; do
        excludes="$excludes --exclude=$pattern"
    done
    echo "$excludes"
}

# Replace placeholder with actual path in a file
replace_placeholder_with_path() {
    local file="$1"
    if [[ -f "$file" ]]; then
        if grep -q "$PLACEHOLDER" "$file" 2>/dev/null; then
            if [[ "$OSTYPE" == "darwin"* ]]; then
                sed -i '' "s|$PLACEHOLDER|$CLAUDE_DIR|g" "$file"
            else
                sed -i "s|$PLACEHOLDER|$CLAUDE_DIR|g" "$file"
            fi
            log_info "  Replaced paths in: $(basename "$file")"
        fi
    fi
}

# Replace actual path with placeholder in a file
replace_path_with_placeholder() {
    local file="$1"
    if [[ -f "$file" ]]; then
        if grep -q "$CLAUDE_DIR" "$file" 2>/dev/null; then
            if [[ "$OSTYPE" == "darwin"* ]]; then
                sed -i '' "s|$CLAUDE_DIR|$PLACEHOLDER|g" "$file"
            else
                sed -i "s|$CLAUDE_DIR|$PLACEHOLDER|g" "$file"
            fi
            log_info "  Normalized paths in: $(basename "$file")"
        fi
    fi
}

# =============================================================================
# PULL: Copy from ~/.claude to repo (for committing changes)
# =============================================================================

do_pull() {
    log_info "Pulling config from $CLAUDE_DIR to repo..."
    echo ""

    # Check if .claude exists
    if [[ ! -d "$CLAUDE_DIR" ]]; then
        log_error "Claude config directory not found: $CLAUDE_DIR"
        exit 1
    fi

    # Create config directory if needed
    mkdir -p "$CONFIG_DIR"

    local excludes=$(build_excludes)

    for item in "${SYNC_ITEMS[@]}"; do
        local src="$CLAUDE_DIR/$item"
        local dst="$CONFIG_DIR/$item"

        if [[ -e "$src" ]]; then
            if [[ -d "$src" ]]; then
                mkdir -p "$dst"
                eval rsync -av --delete $excludes "$src/" "$dst/"
                log_success "Synced folder: $item"
            else
                cp "$src" "$dst"
                log_success "Synced file: $item"
            fi
        else
            log_warning "Not found (skipped): $item"
        fi
    done

    echo ""
    log_info "Normalizing paths (replacing $CLAUDE_DIR with $PLACEHOLDER)..."

    # Replace actual paths with placeholder in JSON files
    find "$CONFIG_DIR" -name "*.json" -type f | while read -r file; do
        replace_path_with_placeholder "$file"
    done

    # Also check .sh files for paths
    find "$CONFIG_DIR" -name "*.sh" -type f | while read -r file; do
        replace_path_with_placeholder "$file"
    done

    echo ""
    log_success "Pull complete! Config copied to: $CONFIG_DIR"
    log_info "Now you can commit and push changes to git."
}

# =============================================================================
# PUSH: Copy from repo to ~/.claude (install config)
# =============================================================================

do_push() {
    log_info "Pushing config from repo to $CLAUDE_DIR..."
    echo ""

    # Check if config directory exists
    if [[ ! -d "$CONFIG_DIR" ]]; then
        log_error "Config directory not found: $CONFIG_DIR"
        log_info "Run './sync.sh pull' first to populate it."
        exit 1
    fi

    # Create .claude directory if needed
    mkdir -p "$CLAUDE_DIR"

    local excludes=$(build_excludes)

    for item in "${SYNC_ITEMS[@]}"; do
        local src="$CONFIG_DIR/$item"
        local dst="$CLAUDE_DIR/$item"

        if [[ -e "$src" ]]; then
            if [[ -d "$src" ]]; then
                mkdir -p "$dst"
                eval rsync -av --delete $excludes "$src/" "$dst/"
                log_success "Installed folder: $item"
            else
                cp "$src" "$dst"
                log_success "Installed file: $item"
            fi
        else
            log_warning "Not in repo (skipped): $item"
        fi
    done

    echo ""
    log_info "Fixing paths (replacing $PLACEHOLDER with $CLAUDE_DIR)..."

    # Replace placeholder with actual path in JSON files
    find "$CLAUDE_DIR" -maxdepth 1 -name "*.json" -type f | while read -r file; do
        replace_placeholder_with_path "$file"
    done

    # Also fix paths in scripts
    if [[ -d "$CLAUDE_DIR/scripts" ]]; then
        find "$CLAUDE_DIR/scripts" -name "*.sh" -type f | while read -r file; do
            replace_placeholder_with_path "$file"
        done
    fi

    echo ""
    log_success "Push complete! Config installed to: $CLAUDE_DIR"
    log_info "Restart Claude Code to apply changes."
}

# =============================================================================
# STATUS: Show what would be synced
# =============================================================================

do_status() {
    echo ""
    log_info "Claude Config Sync Status"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "  Local .claude:  $CLAUDE_DIR"
    echo "  Repo config:    $CONFIG_DIR"
    echo ""
    echo "  Items to sync:"

    for item in "${SYNC_ITEMS[@]}"; do
        local in_claude=""
        local in_repo=""

        [[ -e "$CLAUDE_DIR/$item" ]] && in_claude="✓" || in_claude="✗"
        [[ -e "$CONFIG_DIR/$item" ]] && in_repo="✓" || in_repo="✗"

        printf "    %-20s  [local: %s]  [repo: %s]\n" "$item" "$in_claude" "$in_repo"
    done

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
}

# =============================================================================
# HELP
# =============================================================================

show_help() {
    echo ""
    echo "Claude Code Config Sync"
    echo ""
    echo "Usage: ./sync.sh <command>"
    echo ""
    echo "Commands:"
    echo "  pull     Copy config from ~/.claude to repo (before commit)"
    echo "  push     Copy config from repo to ~/.claude (after git pull)"
    echo "  status   Show sync status"
    echo "  help     Show this help"
    echo ""
    echo "Workflow:"
    echo "  1. Make changes to Claude Code settings on any machine"
    echo "  2. Run './sync.sh pull' to copy changes to repo"
    echo "  3. Commit and push to GitHub"
    echo "  4. On another machine: git pull && ./sync.sh push"
    echo ""
}

# =============================================================================
# Main
# =============================================================================

case "${1:-}" in
    pull)
        do_pull
        ;;
    push)
        do_push
        ;;
    status)
        do_status
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        log_error "Unknown command: ${1:-}"
        show_help
        exit 1
        ;;
esac
