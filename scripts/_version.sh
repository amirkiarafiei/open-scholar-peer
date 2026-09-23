#!/usr/bin/env bash
# Shared helper: what version is this, what is already installed, and say so.
#
# Sourced by init_brain.sh (which announces) and init_mcp.sh (which stamps).
# Both are run by all 21 installers, so no per-tool script needs to know.
#
# The stamp lives at `.open-scholar-peer/osp.json`, one level ABOVE `mcp/`,
# because init_mcp.sh wipes everything inside `mcp/` on every run. It is the
# runtime directory rather than `.brain/`, which holds the user's review and
# is not ours to write version metadata into.
#
# Note `session.json` also carries a `version`. That is the PROTOCOL version
# from the paper — the shape of the artifacts — and it has read "2.0" since
# before this file existed. It is not the product release, and conflating the
# two would make both meaningless.

_OSP_VERSION_SCRIPTS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

osp_repo_version() {
  local f="$_OSP_VERSION_SCRIPTS/../VERSION"
  [ -f "$f" ] && tr -d ' \t\n\r' < "$f" || printf 'unknown'
}

osp_project_version() {
  # What is already installed here, or empty if this is the first time.
  local f="./.open-scholar-peer/osp.json"
  [ -f "$f" ] || return 0
  sed -n 's/.*"version"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' "$f" | head -1
}

# Sort two dotted versions; prints "older", "same" or "newer" for $1 vs $2.
osp_version_cmp() {
  [ "$1" = "$2" ] && { printf 'same'; return; }
  local first
  first="$(printf '%s\n%s\n' "$1" "$2" | sort -V 2>/dev/null | head -1)"
  # sort -V is absent on some BSDs; without it we can still detect equality,
  # and an unknown ordering is reported as a plain change rather than guessed.
  if [ -z "$first" ]; then printf 'changed'; return; fi
  [ "$first" = "$1" ] && printf 'older' || printf 'newer'
}

osp_announce_version() {
  local new prev rel
  new="$(osp_repo_version)"
  prev="$(osp_project_version)"
  local GREEN='\033[0;32m' YELLOW='\033[1;33m' CYAN='\033[0;36m' NC='\033[0m'

  if [ -z "$prev" ]; then
    if [ -d "./.open-scholar-peer" ] || [ -d "./.brain" ]; then
      # Installed before stamping existed — every release up to 1.2.0.
      echo -e "  ${CYAN}↑ Updating Open ScholarPeer → ${new}  ${NC}${YELLOW}(previous version predates stamping)${NC}"
    else
      echo -e "  ${GREEN}✓ Installing Open ScholarPeer ${new}${NC}"
    fi
    return
  fi

  rel="$(osp_version_cmp "$prev" "$new")"
  case "$rel" in
    same)  echo -e "  ${GREEN}✓ Open ScholarPeer ${new} — reinstalling over the same version${NC}" ;;
    older) echo -e "  ${CYAN}↑ Updating Open ScholarPeer ${prev} → ${new}${NC}" ;;
    newer) echo -e "  ${YELLOW}⚠️  Downgrading Open ScholarPeer ${prev} → ${new}. Your review is"
           echo -e "     untouched; the prompts become the older ones.${NC}" ;;
    *)     echo -e "  ${CYAN}↑ Open ScholarPeer ${prev} → ${new}${NC}" ;;
  esac
}

osp_stamp_version() {
  # Written last, so a failed install does not claim to have succeeded.
  local dir="./.open-scholar-peer" new
  new="$(osp_repo_version)"
  mkdir -p "$dir" 2>/dev/null || return 0
  cat > "$dir/osp.json" <<JSON
{
  "version": "$new",
  "installed_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null)",
  "note": "Written by the OSP installer. The protocol version, which is a different thing, is in .brain/session.json."
}
JSON
}
