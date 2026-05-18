#!/bin/bash
# Cross-platform completion sound for Claude Code Stop hook.
# Works on macOS, WSL 2 (Ubuntu), and native Linux.

case "$(uname -s)" in
  Darwin)
    afplay /System/Library/Sounds/Hero.aiff >/dev/null 2>&1 &
    ;;
  Linux)
    if grep -qi microsoft /proc/version 2>/dev/null; then
      powershell.exe -NoProfile -Command \
        "(New-Object Media.SoundPlayer 'C:\Windows\Media\Windows Notify.wav').PlaySync()" \
        >/dev/null 2>&1 &
    else
      { paplay /usr/share/sounds/freedesktop/stereo/complete.oga \
        || aplay /usr/share/sounds/alsa/Front_Center.wav \
        || printf '\a'; } >/dev/null 2>&1 &
    fi
    ;;
esac

exit 0
