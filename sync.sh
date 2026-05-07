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

# Files and folders to sync.
# For plugins we sync only the two metadata files — marketplaces and the cache
# itself are restored from those metadata on push (see restore_plugins).
SYNC_ITEMS=(
    "CLAUDE.md"
    "settings.json"
    "rules"
    "agents"
    "commands"
    "scripts"
    "skills"
    "plugins/installed_plugins.json"
    "plugins/known_marketplaces.json"
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

# Match any absolute .claude path on Linux or macOS:
#   /Users/<user>/.claude  or  /home/<user>/.claude
# This catches both the current machine's path AND foreign paths that may
# have been left over after copying ~/.claude between machines.
ANY_CLAUDE_PATH_REGEX='(/Users/[^/]+|/home/[^/]+)/\.claude'

# Cross-platform in-place sed (BSD sed on macOS needs an empty backup arg)
sed_inplace() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "$@"
    else
        sed -i "$@"
    fi
}

# Push direction: placeholder -> this machine's actual path
replace_placeholder_with_path() {
    local file="$1"
    [[ ! -f "$file" ]] && return 0
    if grep -qF "$PLACEHOLDER" "$file" 2>/dev/null; then
        sed_inplace "s|$PLACEHOLDER|$CLAUDE_DIR|g" "$file"
        log_info "  Replaced paths in: $file"
    fi
}

# Pull direction: any /Users/<u>/.claude or /home/<u>/.claude -> placeholder
replace_path_with_placeholder() {
    local file="$1"
    [[ ! -f "$file" ]] && return 0
    if grep -qE "$ANY_CLAUDE_PATH_REGEX" "$file" 2>/dev/null; then
        sed_inplace -E "s@$ANY_CLAUDE_PATH_REGEX@$PLACEHOLDER@g" "$file"
        log_info "  Normalized paths in: $file"
    fi
}

# Walk every synced item and apply a rewriter to .json/.sh files under it.
# Used for both pull (path -> placeholder) and push (placeholder -> path).
normalize_paths_in_synced_items() {
    local root="$1"
    local rewriter="$2"
    for item in "${SYNC_ITEMS[@]}"; do
        local target="$root/$item"
        [[ ! -e "$target" ]] && continue
        if [[ -f "$target" ]]; then
            case "$target" in
                *.json|*.sh) "$rewriter" "$target" ;;
            esac
        elif [[ -d "$target" ]]; then
            while IFS= read -r file; do
                "$rewriter" "$file"
            done < <(find "$target" -type f \( -name "*.json" -o -name "*.sh" \))
        fi
    done
}

# After push, rebuild plugin marketplaces (git clone) and plugin cache (copy
# from marketplace) using the metadata in plugins/*.json. Idempotent.
restore_plugins() {
    local marketplaces_file="$CLAUDE_DIR/plugins/known_marketplaces.json"
    local installed_file="$CLAUDE_DIR/plugins/installed_plugins.json"

    [[ ! -f "$marketplaces_file" && ! -f "$installed_file" ]] && return 0

    if ! command -v jq >/dev/null 2>&1; then
        log_warning "jq not installed — skipping plugin restore. Install jq, then re-run './sync.sh push'."
        return 0
    fi
    if ! command -v git >/dev/null 2>&1; then
        log_warning "git not installed — skipping plugin restore."
        return 0
    fi

    echo ""
    log_info "Restoring plugins (marketplaces + cache)..."

    if [[ -f "$marketplaces_file" ]]; then
        while IFS= read -r mp_name; do
            [[ -z "$mp_name" ]] && continue
            local install_loc repo
            install_loc=$(jq -r --arg n "$mp_name" '.[$n].installLocation // ""' "$marketplaces_file")
            repo=$(jq -r --arg n "$mp_name" '.[$n].source.repo // ""' "$marketplaces_file")
            [[ -z "$install_loc" || "$install_loc" == "null" ]] && continue
            if [[ -d "$install_loc/.claude-plugin" || -d "$install_loc/.git" ]]; then
                log_info "  Marketplace present: $mp_name"
                continue
            fi
            if [[ -z "$repo" ]]; then
                log_warning "  Marketplace $mp_name has no source.repo — skipped"
                continue
            fi
            mkdir -p "$(dirname "$install_loc")"
            log_info "  Cloning $mp_name from github.com/$repo..."
            if git clone --depth=1 "https://github.com/$repo" "$install_loc" >/dev/null 2>&1; then
                log_success "  Cloned: $mp_name"
            else
                log_error "  Failed to clone $mp_name"
            fi
        done < <(jq -r 'keys[]' "$marketplaces_file")
    fi

    if [[ -f "$installed_file" ]]; then
        while IFS= read -r plugin_key; do
            [[ -z "$plugin_key" ]] && continue
            local plugin_name="${plugin_key%@*}"
            local mp_name="${plugin_key#*@}"
            local install_path
            install_path=$(jq -r --arg k "$plugin_key" '.plugins[$k][0].installPath // ""' "$installed_file")
            [[ -z "$install_path" || "$install_path" == "null" ]] && continue
            if [[ -d "$install_path" && -n "$(ls -A "$install_path" 2>/dev/null)" ]]; then
                log_info "  Plugin cached: $plugin_key"
                continue
            fi
            local mp_loc=""
            [[ -f "$marketplaces_file" ]] && mp_loc=$(jq -r --arg n "$mp_name" '.[$n].installLocation // ""' "$marketplaces_file")
            local source_dir="$mp_loc/plugins/$plugin_name"
            if [[ -z "$mp_loc" || ! -d "$source_dir" ]]; then
                log_warning "  Plugin source missing for $plugin_key (looked in $source_dir)"
                continue
            fi
            mkdir -p "$install_path"
            cp -r "$source_dir/." "$install_path/"
            log_success "  Restored: $plugin_key"
        done < <(jq -r '.plugins | keys[]' "$installed_file")
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
                mkdir -p "$(dirname "$dst")"
                cp "$src" "$dst"
                log_success "Synced file: $item"
            fi
        else
            log_warning "Not found (skipped): $item"
        fi
    done

    echo ""
    log_info "Normalizing paths (any /Users/* or /home/*/.claude -> $PLACEHOLDER)..."
    normalize_paths_in_synced_items "$CONFIG_DIR" replace_path_with_placeholder

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
                mkdir -p "$(dirname "$dst")"
                cp "$src" "$dst"
                log_success "Installed file: $item"
            fi
        else
            log_warning "Not in repo (skipped): $item"
        fi
    done

    echo ""
    log_info "Fixing paths (replacing $PLACEHOLDER with $CLAUDE_DIR)..."
    normalize_paths_in_synced_items "$CLAUDE_DIR" replace_placeholder_with_path

    restore_plugins

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

        printf "    %-40s  [local: %s]  [repo: %s]\n" "$item" "$in_claude" "$in_repo"
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
