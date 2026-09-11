#!/usr/bin/env bash
# _post_install.sh — the shared closing message for every per-tool installer.
#
# Sourced (not executed) by scripts/install_*.sh after the colour variables are
# defined, so the "where do I type the slash command?" wording lives in exactly
# one place and cannot drift across 14 scripts.
#
#   osp_post_install "<Tool display name>" ["<tool-specific action>" ...]
#
# Tool-specific actions are always printed. The shared instruction — open the
# agent and type the command inside its chat — is printed only when the script
# is run on its own; when install.sh is driving (OSP_DRIVEN=1) it prints that
# block once at the end instead of once per tool.

osp_post_install() {
  local tool="$1"; shift
  local n=0 line

  printf '\n%bDone!%b\n' "${GREEN:-}" "${NC:-}"

  # Driven by install.sh with nothing tool-specific to say? Then say nothing —
  # install.sh prints the shared next steps once, at the end.
  if [ -n "${OSP_DRIVEN:-}" ] && [ "$#" -eq 0 ]; then return 0; fi

  printf '\nNext for %s:\n' "$tool"

  for line in "$@"; do
    n=$((n + 1))
    # %s, not %b: these are plain text, and %b would eat a backslash in a
    # future action string (a \n, or a Windows path).
    printf '  (%d) %s\n' "$n" "$line"
  done

  if [ -z "${OSP_DRIVEN:-}" ]; then
    n=$((n + 1))
    printf '  (%d) Open %s here, and in its interactive chat run %b/open-scholar-peer%b\n' \
      "$n" "$tool" "${CYAN:-}" "${NC:-}"
  fi
}
