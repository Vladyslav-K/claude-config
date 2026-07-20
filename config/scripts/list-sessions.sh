#!/bin/bash

# List Claude Code sessions of a project: date - title - session id, newest first.
# Shows the 20 most recent sessions by default.
# Usage:
#   list-sessions.sh [options]                    sessions of the project in the current directory
#   list-sessions.sh [options] <project-path>     sessions of the project at the given path
#   list-sessions.sh [options] <storage-folder>   folder name inside ~/.claude/projects (e.g. -workspace-my-app)
# Options:
#   -n N        show N most recent sessions (default 20)
#   -a, --all   show all sessions
# Resume a session with: claude --resume <session-id>

set -euo pipefail

# In a POSIX locale (bare containers) bash counts bytes, not characters,
# so ${var:0:n} would cut multi-byte UTF-8 titles in half
case "${LC_ALL:-${LC_CTYPE:-${LANG:-}}}" in
  *[Uu][Tt][Ff]*) ;;
  *) export LC_ALL=C.UTF-8 ;;
esac

CLAUDE_DIR="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
PROJECTS_DIR="$CLAUDE_DIR/projects"

usage() {
  sed -n '3,12p' "$0" | sed 's/^# \{0,1\}//'
}

# Claude Code names project storage folders by replacing every
# non-alphanumeric character of the absolute project path with "-"
path_to_slug() {
  printf '%s' "$1" | sed 's/[^a-zA-Z0-9]/-/g'
}

resolve_storage_dir() {
  local arg="${1:-}"
  if [ -z "$arg" ]; then
    printf '%s' "$PROJECTS_DIR/$(path_to_slug "$PWD")"
  elif [ -d "$PROJECTS_DIR/$arg" ]; then
    printf '%s' "$PROJECTS_DIR/$arg"
  elif [ -d "$arg" ]; then
    printf '%s' "$PROJECTS_DIR/$(path_to_slug "$(cd "$arg" && pwd)")"
  elif [ "${arg:0:1}" = "/" ]; then
    # Absolute path that does not exist locally (deleted project,
    # devcontainer path like /workspace/...) - try its slug anyway
    printf '%s' "$PROJECTS_DIR/$(path_to_slug "$arg")"
  else
    return 1
  fi
}

# GNU coreutils (Linux) and BSD tools (macOS) take different flags.
# Probe GNU first: BSD stat rejects -c cleanly, while GNU stat treats
# BSD's -f as --file-system and pollutes stdout before failing.
if stat -c '%Y' / >/dev/null 2>&1; then
  file_epoch() { stat -c '%Y' "$1"; }
  fmt_date() { date -d "@$1" '+%Y-%m-%d %H:%M'; }
else
  file_epoch() { stat -f '%m' "$1"; }
  fmt_date() { date -r "$1" '+%Y-%m-%d %H:%M'; }
fi

session_title() {
  local f="$1" title=""
  # Newest ai-title record wins: Claude Code appends one per session start
  title=$(grep -h '"type":"ai-title"' "$f" 2>/dev/null | tail -1 | jq -r '.aiTitle // empty' 2>/dev/null || true)
  if [ -z "$title" ]; then
    # Fallback: slash-command name or the first real user prompt
    title=$(jq -Rrn '
      [limit(10; inputs | fromjson?
        | select(.type == "user" and (.isSidechain != true))
        | .message.content
        | if type == "string" then . else ([.[]? | select(.type? == "text") | .text] | join(" ")) end
        | select(type == "string" and length > 0)
      )] as $msgs
      | ([$msgs[] | capture("<command-name>(?<c>[^<]+)</command-name>").c] | first) as $cmd
      | ([$msgs[] | select((startswith("Caveat:") or startswith("<")) | not)] | first) as $plain
      | $cmd // $plain // ""
    ' <"$f" 2>/dev/null || true)
  fi
  [ -z "$title" ] && title="(no title)"
  # Strip control chars so multi-line prompts and ANSI codes cannot break the table
  printf '%s' "$title" | tr -s '[:cntrl:]' ' '
}

main() {
  local limit=20 project=""
  while [ $# -gt 0 ]; do
    case "$1" in
      -h | --help)
        usage
        exit 0
        ;;
      -n)
        shift
        limit="${1:-}"
        ;;
      -a | --all)
        limit=0
        ;;
      *)
        project="$1"
        ;;
    esac
    shift
  done
  if ! [[ "$limit" =~ ^[0-9]+$ ]]; then
    echo "Invalid -n value: expected a number" >&2
    exit 1
  fi

  local dir
  if ! dir=$(resolve_storage_dir "$project"); then
    echo "Project not found: $project" >&2
    echo "Looked for a folder in $PROJECTS_DIR and a project path on disk." >&2
    exit 1
  fi
  if [ ! -d "$dir" ]; then
    echo "No session storage for this project: $dir" >&2
    exit 1
  fi

  shopt -s nullglob
  local files=("$dir"/*.jsonl)
  if [ ${#files[@]} -eq 0 ]; then
    echo "No sessions found in $dir" >&2
    exit 0
  fi

  # Sort by mtime first and take the newest N, so titles are parsed
  # only for the files that will actually be shown. Both index fields
  # are always non-empty: adjacent tabs would collapse during read,
  # since tab is whitespace IFS
  local f index=""
  for f in "${files[@]}"; do
    index+="$(file_epoch "$f")"$'\t'"$f"$'\n'
  done

  # C locale keeps sort byte-safe; herestring instead of a pipe so an
  # early head exit cannot SIGPIPE the whole script under pipefail
  local shown
  shown=$(printf '%s' "$index" | LC_ALL=C sort -rn)
  if [ "$limit" -gt 0 ]; then
    shown=$(head -n "$limit" <<<"$shown")
  fi

  local count
  count=$(grep -c . <<<"$shown" || true)
  if [ "$count" -lt ${#files[@]} ]; then
    echo "Sessions for $(basename "$dir") ($count of ${#files[@]}, use -a for all):" >&2
  else
    echo "Sessions for $(basename "$dir") (${#files[@]}):" >&2
  fi

  local epoch id fdate title
  while IFS=$'\t' read -r epoch f; do
    [ -z "$f" ] && continue
    id=$(basename "$f" .jsonl)
    fdate=$(fmt_date "$epoch")
    title=$(session_title "$f")
    # Trim and pad by characters, not bytes: printf %.60s would cut
    # multi-byte UTF-8 titles in half and produce invalid sequences
    title=${title:0:60}
    printf '%s  %s%*s  %s\n' "$fdate" "$title" $((60 - ${#title})) '' "$id"
  done <<<"$shown"
}

main "$@"
