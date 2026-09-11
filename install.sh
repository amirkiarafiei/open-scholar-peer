#!/usr/bin/env bash
#
# Open ScholarPeer — interactive installer
#
#   Local:  bash install.sh
#   Remote: curl -sSL https://raw.githubusercontent.com/amirkiarafiei/open-scholar-peer/main/install.sh | bash
#
# Portability notes:
#   - Targets bash 3.2 (macOS default): no associative arrays, no mapfile, no ${x,,}.
#   - All keyboard input is read from /dev/tty so the menus work when piped from curl.
#   - The per-tool scripts under scripts/install_*.sh remain the unit of work; this
#     file only chooses which of them to run, and where.

set -o pipefail

REPO_URL="https://github.com/amirkiarafiei/open-scholar-peer"

# ---------------------------------------------------------------- data -----

# Index-aligned. Order matches the README's support table.
TOOL_NAMES=(
  "Claude Code" "Cursor" "Antigravity" "Gemini CLI" "Copilot CLI"
  "Codex CLI" "Qwen Code" "OpenCode" "Junie" "Kiro"
  "Kimi Code" "Mistral Vibe" "OpenHands" "Antigravity CLI"
)
TOOL_SLUGS=(
  "claude" "cursor" "antigravity" "gemini" "copilot"
  "codex" "qwen" "opencode" "junie" "kiro"
  "kimi" "vibe" "openhands" "antigravity-cli"
)
TOOL_SCRIPTS=(
  "install_claude.sh" "install_cursor.sh" "install_antigravity.sh"
  "install_gemini.sh" "install_copilot.sh" "install_codex.sh"
  "install_qwen.sh" "install_opencode.sh" "install_junie.sh"
  "install_kiro.sh" "install_kimi.sh" "install_vibe.sh"
  "install_openhands.sh" "install_antigravity_cli.sh"
)

# ------------------------------------------------------- capabilities ------

if [ -t 1 ] && [ -z "${NO_COLOR:-}" ] && [ "${TERM:-dumb}" != "dumb" ]; then
  B=$'\033[1m';    DIM=$'\033[2m';  R=$'\033[0m';   REV=$'\033[7m'
  RED=$'\033[31m'; GRN=$'\033[32m'; YEL=$'\033[33m'
  BLU=$'\033[34m'; CYN=$'\033[36m'; GRY=$'\033[90m'
else
  B=""; DIM=""; R=""; REV=""; RED=""; GRN=""; YEL=""; BLU=""; CYN=""; GRY=""
fi

if printf '%s' "${LC_ALL:-${LC_CTYPE:-${LANG:-}}}" | grep -qi 'utf-*8'; then
  LINE="─"; ON="◉"; OFF="○"; CHK="▣"; BOX="□"; ARROW="›"; TICK="✓"; CROSS="✗"; DOT="·"
  TL="╭"; TR="╮"; BL="╰"; BR="╯"; VT="│"
else
  LINE="-"; ON="(*)"; OFF="( )"; CHK="[x]"; BOX="[ ]"; ARROW=">"; TICK="+"; CROSS="x"; DOT="-"
  TL="+"; TR="+"; BL="+"; BR="+"; VT="|"
fi

# Subagent isolation for /5-osp-qa, and how the MCP server gets wired.
# Built here, not with the other arrays, so the separator honours the locale.
TOOL_HINTS=(
  "subagents $DOT .mcp.json auto"
  "subagents $DOT .cursor/mcp.json auto"
  "self-reflect $DOT global config auto"
  "subagents $DOT .gemini/settings.json auto"
  "subagents $DOT ~/.copilot auto"
  "subagents $DOT codex mcp add (TOML)"
  "subagents $DOT .qwen/settings.json auto"
  "subagents $DOT opencode mcp add"
  "subagents $DOT .junie/mcp/mcp.json auto"
  "subagents $DOT .kiro/settings/mcp.json auto"
  "subagents $DOT ~/.kimi/mcp.json auto"
  "self-reflect $DOT manual TOML snippet"
  "self-reflect $DOT manual snippet"
  "subagents $DOT .agents/mcp_config.json auto"
)

term_cols() { local c; c=$(tput cols 2>/dev/null) || c=80; [ "$c" -gt 0 ] 2>/dev/null || c=80; printf '%s' "$c"; }
term_rows() { local r; r=$(tput lines 2>/dev/null) || r=24; [ "$r" -gt 0 ] 2>/dev/null || r=24; printf '%s' "$r"; }

hr() {
  local w i out=""
  w=$(term_cols); [ "$w" -gt 78 ] && w=78
  i=0; while [ "$i" -lt "$w" ]; do out="$out$LINE"; i=$((i + 1)); done
  printf '%s%s%s\n' "$GRY" "$out" "$R"
}

say()  { printf '%s\n' "$*"; }
info() { printf '  %s%s%s %s\n' "$CYN" "$ARROW" "$R" "$*"; }
ok()   { printf '  %s%s%s %s\n' "$GRN" "$TICK" "$R" "$*"; }
warn() { printf '  %s!%s %s\n' "$YEL" "$R" "$*"; }
bad()  { printf '  %s%s%s %s\n' "$RED" "$CROSS" "$R" "$*" >&2; }

banner() {
  local w; w=$(term_cols)
  printf '\n'
  if [ "$w" -ge 62 ]; then
    printf '%s' "$BLU"
    cat <<'BANNER'
   ██████╗ ███████╗██████╗
  ██╔═══██╗██╔════╝██╔══██╗
  ██║   ██║███████╗██████╔╝
  ██║   ██║╚════██║██╔═══╝
  ╚██████╔╝███████║██║
   ╚═════╝ ╚══════╝╚═╝
BANNER
    printf '%s' "$R"
  else
    printf '  %s%sOSP%s\n' "$B" "$BLU" "$R"
  fi
  printf '  %sOpen ScholarPeer%s %s%s context-aware multi-agent peer review%s\n' \
    "$B" "$R" "$DIM" "$DOT" "$R"
  hr
}

# --------------------------------------------------------------- input -----

CURSOR_HIDDEN=0
hide_cursor() { [ -t 1 ] || return 0; printf '\033[?25l'; CURSOR_HIDDEN=1; }
show_cursor() { [ "$CURSOR_HIDDEN" -eq 1 ] && printf '\033[?25h'; CURSOR_HIDDEN=0; return 0; }

cleanup_all() {
  show_cursor
  [ "${IS_REMOTE:-false}" = true ] && [ -n "${TEMP_DIR:-}" ] && rm -rf "$TEMP_DIR"
  return 0
}
on_interrupt() { show_cursor; printf '\n'; bad "Cancelled."; exit 130; }
trap cleanup_all EXIT
trap on_interrupt INT TERM

# Reads one keypress from the terminal and echoes a symbolic name.
read_key() {
  local k a b seq=""
  IFS= read -rsn1 k <"$TTY" 2>/dev/null || { printf 'eof'; return; }
  case "$k" in
    "")    printf 'enter'; return ;;
    " ")   printf 'space'; return ;;
    $'\t') printf 'tab';   return ;;
    $'\033')
      # Escape, or the start of a CSI/SS3 sequence. A short timeout tells them apart.
      if ! IFS= read -rsn1 -t 1 a <"$TTY" 2>/dev/null; then printf 'esc'; return; fi
      case "$a" in
        "[" | "O") ;;
        *) printf 'esc'; return ;;
      esac
      while IFS= read -rsn1 -t 1 b <"$TTY" 2>/dev/null; do
        seq="$seq$b"
        case "$b" in [A-Za-z~]) break ;; esac
      done
      case "$seq" in
        A) printf 'up' ;;    B) printf 'down' ;;
        C) printf 'right' ;; D) printf 'left' ;;
        H | "1~") printf 'home' ;;
        F | "4~") printf 'end' ;;
        "5~") printf 'pgup' ;; "6~") printf 'pgdn' ;;
        *) printf 'other' ;;
      esac
      return ;;
    *) printf '%s' "$k"; return ;;
  esac
}

# Re-draws in place: move up N lines, clearing everything below.
rewind() { local n=$1; [ "$n" -gt 0 ] && printf '\033[%dA\033[J' "$n"; return 0; }

# Expand a leading ~ without eval.
expand_tilde() {
  case "$1" in
    "~")   printf '%s' "$HOME" ;;
    "~/"*) printf '%s/%s' "$HOME" "${1#\~/}" ;;
    *)     printf '%s' "$1" ;;
  esac
}

# --------------------------------------------------------------- button ----

BTN_W=38

# draw_button <label> <focused 0|1> <enabled 0|1> — a framed, 3-line button.
# Boxed even when unfocused, so it reads as a button at a glance.
draw_button() {
  local label=$1 focused=$2 enabled=$3
  local len pad l r bar color content i=0
  len=${#label}
  if [ "$len" -gt "$BTN_W" ]; then label=${label:0:$BTN_W}; len=$BTN_W; fi
  pad=$(( (BTN_W - len) / 2 ))
  l=$(printf '%*s' "$pad" ''); r=$(printf '%*s' $(( BTN_W - len - pad )) '')
  content="${l}${label}${r}"
  bar=""; while [ "$i" -lt "$BTN_W" ]; do bar="${bar}${LINE}"; i=$((i + 1)); done

  if [ "$focused" -eq 1 ]; then
    if [ "$enabled" -eq 1 ]; then color="$GRN$B"; else color="$YEL$B"; fi
  elif [ "$enabled" -eq 1 ]; then color="$B"
  else color="$GRY"; fi

  printf '     %s%s%s%s%s\n' "$color" "$TL" "$bar" "$TR" "$R"
  if [ "$focused" -eq 1 ]; then
    printf '   %s %s%s%s%s%s%s%s\n' "$ARROW" "$color" "$VT" "$REV" "$content" "$R$color" "$VT" "$R"
  else
    printf '     %s%s%s%s%s\n' "$color" "$VT" "$content" "$VT" "$R"
  fi
  printf '     %s%s%s%s%s\n' "$color" "$BL" "$bar" "$BR" "$R"
}

# One-line fallback for terminals too short to spare three rows.
draw_button_inline() {
  local label=$1 focused=$2 enabled=$3 color
  if [ "$focused" -eq 1 ]; then
    if [ "$enabled" -eq 1 ]; then color="$GRN$B"; else color="$YEL$B"; fi
    printf '   %s %s[ %s ]%s\n' "$ARROW" "$color$REV" "$label" "$R"
  else
    if [ "$enabled" -eq 1 ]; then color="$B"; else color="$GRY"; fi
    printf '     %s[ %s ]%s\n' "$color" "$label" "$R"
  fi
}

# ---------------------------------------------------------------- menus ----

# menu_single "Title" idx_default item... -> MENU_CHOICE (index), or -1 on cancel.
# Set MENU_SUB beforehand for a dim explanatory line under the title.
MENU_CHOICE=-1
MENU_SUB=""
menu_single() {
  local title=$1 cur=$2; shift 2
  local items=("$@") n=${#items[@]} drawn=0 i key

  hide_cursor
  while :; do
    rewind "$drawn"; drawn=0
    printf '  %s%s%s\n' "$B" "$title" "$R"; drawn=$((drawn + 1))
    if [ -n "$MENU_SUB" ]; then
      printf '  %s%s%s\n' "$DIM" "$MENU_SUB" "$R"; drawn=$((drawn + 1))
    fi
    printf '\n'; drawn=$((drawn + 1))
    i=0
    while [ "$i" -lt "$n" ]; do
      if [ "$i" -eq "$cur" ]; then
        printf '   %s%s %s %s%s\n' "$CYN$B" "$ON" "${items[$i]}" "$ARROW" "$R"
      else
        printf '   %s%s%s %s\n' "$GRY" "$OFF" "$R" "${items[$i]}"
      fi
      drawn=$((drawn + 1)); i=$((i + 1))
    done
    printf '\n'; drawn=$((drawn + 1))
    printf '   %s↑/↓ move %s enter select %s q cancel%s\n' "$DIM" "$DOT" "$DOT" "$R"
    drawn=$((drawn + 1))

    key=$(read_key)
    case "$key" in
      up | k)   cur=$((cur - 1)); [ "$cur" -lt 0 ] && cur=$((n - 1)) ;;
      down | j) cur=$((cur + 1)); [ "$cur" -ge "$n" ] && cur=0 ;;
      home)     cur=0 ;;
      end)      cur=$((n - 1)) ;;
      enter)
        rewind "$drawn"; show_cursor
        printf '  %s%s%s %s%s%s\n' "$GRN" "$TICK" "$R" "$DIM" "$title" "$R"
        printf '     %s%s%s\n' "$B" "${items[$cur]}" "$R"
        MENU_CHOICE=$cur; return 0 ;;
      q | esc | eof) show_cursor; MENU_CHOICE=-1; return 1 ;;
    esac
  done
}

# menu_tools <context> -> MULTI_SELECTED array of indices; returns 1 if cancelled.
#
# The list is the 14 tools plus one focusable Install button pinned underneath.
# Enter or space on a tool row TOGGLES it; only Enter on the button installs.
MULTI_SELECTED=()
menu_tools() {
  local context=$1
  local n=${#TOOL_NAMES[@]}
  local cur=0 top=0 drawn=0 i key win rows count layout marks=""

  i=0; while [ "$i" -lt "$n" ]; do marks="${marks}0"; i=$((i + 1)); done

  rows=$(term_rows)
  # Rows of chrome around the list: title, sub, blanks, button, two help lines.
  layout=0
  [ $(( 12 + n )) -ge "$rows" ] && layout=1
  [ $((  9 + n )) -ge "$rows" ] && layout=2
  win=$n
  if [ "$layout" -eq 2 ]; then
    win=$(( rows - 9 )); [ "$win" -lt 4 ] && win=4; [ "$win" -gt "$n" ] && win=$n
  fi

  hide_cursor
  while :; do
    if [ "$cur" -lt "$n" ]; then
      [ "$cur" -lt "$top" ] && top=$cur
      [ "$cur" -ge $((top + win)) ] && top=$((cur - win + 1))
    fi

    count=0; i=0
    while [ "$i" -lt "$n" ]; do
      [ "${marks:$i:1}" = "1" ] && count=$((count + 1))
      i=$((i + 1))
    done

    rewind "$drawn"; drawn=0
    printf '  %sWhich AI tools will you review with?%s   %s%d of %d selected%s\n' \
      "$B" "$R" "$DIM" "$count" "$n" "$R"; drawn=$((drawn + 1))
    if [ "$layout" -eq 0 ]; then
      printf '  %s%s%s\n' "$DIM" "$context" "$R"; drawn=$((drawn + 1))
    fi
    if [ "$layout" -lt 2 ]; then printf '\n'; drawn=$((drawn + 1)); fi

    i=$top
    while [ "$i" -lt $((top + win)) ] && [ "$i" -lt "$n" ]; do
      local box name hint
      if [ "${marks:$i:1}" = "1" ]; then box="${GRN}${CHK}${R}"; else box="${GRY}${BOX}${R}"; fi
      name=${TOOL_NAMES[$i]}; hint=${TOOL_HINTS[$i]}
      if [ "$i" -eq "$cur" ]; then
        printf ' %s %s %s%-17s%s %s%s%s\n' "$ARROW" "$box" "$CYN$B" "$name" "$R" "$DIM" "$hint" "$R"
      else
        printf '   %s %-17s %s%s%s\n' "$box" "$name" "$GRY" "$hint" "$R"
      fi
      drawn=$((drawn + 1)); i=$((i + 1))
    done

    if [ "$win" -lt "$n" ]; then
      printf '   %s%d-%d of %d%s\n' "$DIM" $((top + 1)) "$i" "$n" "$R"; drawn=$((drawn + 1))
    fi

    # --- Install button, pinned below the list ---
    if [ "$layout" -lt 2 ]; then printf '\n'; drawn=$((drawn + 1)); fi
    local blabel benabled=1 bfocus=0
    if [ "$count" -gt 0 ]; then
      if [ "$count" -eq 1 ]; then blabel="Install for 1 tool"; else blabel="Install for $count tools"; fi
    else
      benabled=0; blabel="Install"
      [ "$cur" -eq "$n" ] && blabel="Pick at least one tool"
    fi
    [ "$cur" -eq "$n" ] && bfocus=1
    if [ "$layout" -eq 2 ]; then
      draw_button_inline "$blabel" "$bfocus" "$benabled"; drawn=$((drawn + 1))
    else
      draw_button "$blabel" "$bfocus" "$benabled"; drawn=$((drawn + 3))
    fi

    if [ "$layout" -eq 0 ]; then
      printf '\n'; drawn=$((drawn + 1))
      printf '     %s↑/↓ move %s space or enter toggle %s a all %s n none%s\n' \
        "$DIM" "$DOT" "$DOT" "$DOT" "$R"; drawn=$((drawn + 1))
      printf '     %spast the last tool is the Install button %s q cancel%s\n' \
        "$DIM" "$DOT" "$R"; drawn=$((drawn + 1))
    else
      printf '     %s↑/↓ %s space toggle %s a all %s n none %s q cancel%s\n' \
        "$DIM" "$DOT" "$DOT" "$DOT" "$DOT" "$R"; drawn=$((drawn + 1))
    fi

    key=$(read_key)
    case "$key" in
      up | k)   cur=$((cur - 1)); [ "$cur" -lt 0 ] && cur=$n ;;
      down | j) cur=$((cur + 1)); [ "$cur" -gt "$n" ] && cur=0 ;;
      pgup)     cur=$((cur - win)); [ "$cur" -lt 0 ] && cur=0 ;;
      pgdn)     cur=$((cur + win)); [ "$cur" -gt "$n" ] && cur=$n ;;
      home)     cur=0 ;;
      end)      cur=$n ;;
      a | A)    marks=""; i=0; while [ "$i" -lt "$n" ]; do marks="${marks}1"; i=$((i + 1)); done ;;
      n | N)    marks=""; i=0; while [ "$i" -lt "$n" ]; do marks="${marks}0"; i=$((i + 1)); done ;;
      space | left | right | h | l)
        if [ "$cur" -lt "$n" ]; then
          if [ "${marks:$cur:1}" = "1" ]; then marks="${marks:0:$cur}0${marks:$((cur + 1))}"
          else marks="${marks:0:$cur}1${marks:$((cur + 1))}"; fi
        fi ;;
      enter)
        if [ "$cur" -lt "$n" ]; then
          # On a tool row Enter toggles. It must never start the install.
          if [ "${marks:$cur:1}" = "1" ]; then marks="${marks:0:$cur}0${marks:$((cur + 1))}"
          else marks="${marks:0:$cur}1${marks:$((cur + 1))}"; fi
        elif [ "$count" -gt 0 ]; then
          MULTI_SELECTED=()
          i=0; while [ "$i" -lt "$n" ]; do
            [ "${marks:$i:1}" = "1" ] && MULTI_SELECTED[${#MULTI_SELECTED[@]}]=$i
            i=$((i + 1))
          done
          rewind "$drawn"; show_cursor
          printf '  %s%s%s %sSelected %d tool(s)%s\n' \
            "$GRN" "$TICK" "$R" "$DIM" "${#MULTI_SELECTED[@]}" "$R"
          return 0
        fi ;;
      q | esc | eof) show_cursor; MULTI_SELECTED=(); return 1 ;;
    esac
  done
}

# ----------------------------------------------------------- tool lookup ---

# slug_to_index <slug> -> echoes index, or nothing when unknown.
slug_to_index() {
  local want=$1 i=0
  while [ "$i" -lt "${#TOOL_SLUGS[@]}" ]; do
    [ "${TOOL_SLUGS[$i]}" = "$want" ] && { printf '%s' "$i"; return 0; }
    i=$((i + 1))
  done
  return 1
}

list_slugs() {
  local i=0
  while [ "$i" -lt "${#TOOL_SLUGS[@]}" ]; do
    printf '    %-18s %s\n' "${TOOL_SLUGS[$i]}" "${TOOL_NAMES[$i]}"
    i=$((i + 1))
  done
}

usage() {
  cat <<USAGE
Open ScholarPeer installer

  bash install.sh                        interactive install into the current directory
  bash install.sh --tool claude          install for one tool, no prompts
  bash install.sh --tool claude,cursor   install for several
  bash install.sh --dir ~/papers/acl     install into another directory
  bash install.sh --list                 list tool slugs
  bash install.sh -h | --help            this message

Interactive keys:
  up/down move  ·  space or enter toggle  ·  a all  ·  n none  ·  q cancel
  Arrow past the last tool to reach the Install button, then press enter.

Tool slugs:
USAGE
  list_slugs
}

# ----------------------------------------------------------------- main ----

TARGET=""
CLI_TOOLS=""
while [ $# -gt 0 ]; do
  case "$1" in
    -h | --help) usage; exit 0 ;;
    --list)      list_slugs; exit 0 ;;
    --tool)      CLI_TOOLS="$2"; shift 2 || { bad "--tool needs a value"; exit 2; } ;;
    --tool=*)    CLI_TOOLS="${1#--tool=}"; shift ;;
    --dir)       TARGET="$2"; shift 2 || { bad "--dir needs a value"; exit 2; } ;;
    --dir=*)     TARGET="${1#--dir=}"; shift ;;
    *) printf 'Unknown option: %s\n\n' "$1" >&2; usage >&2; exit 2 ;;
  esac
done

# Local checkout, or piped from curl? BASH_SOURCE is empty under `curl | bash`,
# so the reliable signal is whether a scripts/ directory sits beside us.
SOURCE_DIR=$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" 2>/dev/null && pwd) || SOURCE_DIR=$(pwd)
IS_REMOTE=false
TEMP_DIR=""
# A bare `scripts/` directory is not proof: the caller may be sitting in an
# unrelated project that has one. Require files only an OSP checkout carries.
if [ ! -f "$SOURCE_DIR/scripts/init_brain.sh" ] || [ ! -d "$SOURCE_DIR/extensions/_shared" ]; then
  IS_REMOTE=true
fi

# Where are we installing? Default is the caller's working directory, resolved
# before any clone changes anything underneath us.
INVOKED_FROM=$(pwd)

banner

# --- Preflight ---------------------------------------------------------------
if ! command -v python3 >/dev/null 2>&1; then
  bad "python3 not found in PATH. Install Python 3.10+ and re-run."
  exit 1
fi
if ! python3 -c "import ensurepip" >/dev/null 2>&1; then
  py_minor=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null || printf '3')
  bad "python3 is missing the venv module (ensurepip)."
  say "     On Debian/Ubuntu:  sudo apt install python${py_minor}-venv"
  exit 1
fi

if [ "$IS_REMOTE" = true ]; then
  if ! command -v git >/dev/null 2>&1; then
    bad "git not found in PATH; it is needed to fetch Open ScholarPeer. Install git and re-run."
    exit 1
  fi
  info "Remote install — fetching Open ScholarPeer"
  TEMP_DIR=$(mktemp -d) || { bad "Could not create a temporary directory."; exit 1; }
  if ! git clone --depth 1 "$REPO_URL" "$TEMP_DIR" >/dev/null 2>&1; then
    bad "Failed to clone $REPO_URL. Check your network and retry."
    exit 1
  fi
  SOURCE_DIR="$TEMP_DIR"
else
  info "Local checkout — installing from $SOURCE_DIR"
fi

# --- Non-interactive path ----------------------------------------------------
# Chosen when --tool is given, or forced when there is no terminal to draw on.
TTY="/dev/tty"
HAVE_TTY=1
{ [ -r "$TTY" ] && [ -t 1 ]; } || HAVE_TTY=0

SELECTED_IDX=""
if [ -n "$CLI_TOOLS" ]; then
  OLD_IFS=$IFS; IFS=','
  for slug in $CLI_TOOLS; do
    IFS=$OLD_IFS
    slug=$(printf '%s' "$slug" | tr -d '[:space:]')
    [ -z "$slug" ] && continue
    if idx=$(slug_to_index "$slug"); then
      SELECTED_IDX="$SELECTED_IDX $idx"
    else
      bad "Unknown tool: $slug"
      say ""
      list_slugs >&2
      exit 2
    fi
    IFS=','
  done
  IFS=$OLD_IFS
  if [ -z "$SELECTED_IDX" ]; then bad "--tool given but no tool parsed."; exit 2; fi
elif [ "$HAVE_TTY" -eq 0 ]; then
  hr
  bad "No interactive terminal available, and no --tool given."
  say ""
  say "  The menus need a terminal. Either run it interactively:"
  say ""
  say "      git clone $REPO_URL && cd open-scholar-peer && bash install.sh"
  say ""
  say "  or name the tool up front, which works over a pipe:"
  say ""
  say "      curl -sSL $REPO_URL/raw/main/install.sh | bash -s -- --tool claude"
  say ""
  say "  Tool slugs:"
  list_slugs
  exit 1
fi

# --- Interactive path --------------------------------------------------------
if [ -z "$SELECTED_IDX" ]; then
  hr; printf '\n'

  # Step 1 — where. Guards against running `curl | bash` in the wrong directory.
  if [ -z "$TARGET" ]; then
    MENU_SUB="Your paper, the .brain/ working state and the MCP runtime all live here."
    if ! menu_single "Step 1 of 2 $DOT Where should Open ScholarPeer be installed?" 0 \
      "This directory   $INVOKED_FROM" \
      "Another path..."; then
      printf '\n'; bad "Cancelled — nothing was installed."; exit 130
    fi
    MENU_SUB=""
    if [ "$MENU_CHOICE" -eq 1 ]; then
      printf '\n  %sEnter the target directory:%s ' "$B" "$R"
      show_cursor
      IFS= read -r TARGET <"$TTY" || TARGET=""
      TARGET=$(expand_tilde "$TARGET")
      if [ -z "$TARGET" ]; then printf '\n'; bad "No path given."; exit 1; fi
    else
      TARGET="$INVOKED_FROM"
    fi
  fi
  printf '\n'; hr; printf '\n'

  # Step 2 — which tools.
  if ! menu_tools "Into $TARGET"; then
    printf '\n'; bad "Cancelled — nothing was installed."; exit 130
  fi
  SELECTED_IDX="${MULTI_SELECTED[*]}"
fi

[ -z "$TARGET" ] && TARGET="$INVOKED_FROM"
TARGET=$(expand_tilde "$TARGET")
mkdir -p "$TARGET" 2>/dev/null || { bad "Cannot create $TARGET"; exit 1; }
TARGET=$(cd "$TARGET" && pwd) || { bad "Cannot enter $TARGET"; exit 1; }

# --- Install -----------------------------------------------------------------
cd "$TARGET" || { bad "Cannot enter $TARGET"; exit 1; }

printf '\n'; hr
printf '  %sInstalling into%s %s\n' "$B" "$R" "$TARGET"
hr

installed=0; failed=0; failed_names=""; installed_names=""
for i in $SELECTED_IDX; do
  name=${TOOL_NAMES[$i]}
  script=${TOOL_SCRIPTS[$i]}
  printf '\n'
  printf '  %s%s %s%s\n' "$CYN$B" "$ARROW" "$name" "$R"
  hr
  # Tells the per-tool script to skip its own "type /open-scholar-peer" block;
  # the consolidated summary below prints that once instead of once per tool.
  if OSP_DRIVEN=1 bash "$SOURCE_DIR/scripts/$script"; then
    installed=$((installed + 1)); installed_names="$installed_names $name"
  else
    failed=$((failed + 1)); failed_names="$failed_names $name"
    bad "$name — installer exited non-zero (see the output above)"
  fi
done

# --- Summary -----------------------------------------------------------------
printf '\n'; hr
if [ "$failed" -eq 0 ]; then
  printf '  %s%s Open ScholarPeer installed for %d tool(s)%s\n' "$GRN$B" "$TICK" "$installed" "$R"
else
  printf '  %s%s %d installed, %d failed:%s%s\n' \
    "$YEL$B" "$ARROW" "$installed" "$failed" "$failed_names" "$R"
fi
printf '  %s%s%s\n' "$DIM" "$TARGET" "$R"
printf '\n'
printf '  %sWhat to do next%s\n\n' "$B" "$R"
printf '    %s1.%s Put the paper you want reviewed anywhere in this directory.\n' "$B" "$R"
printf '    %s2.%s Open your AI coding tool %sin this directory%s —%s\n' "$B" "$R" "$B" "$R" ""
printf '       %se.g. run %sclaude%s, or open the folder in Cursor.%s\n' "$DIM" "$R$CYN" "$R$DIM" "$R"
printf '    %s3.%s %sInside that tool'"'"'s chat%s — not in your shell — type:\n' "$B" "$R" "$B" "$R"
printf '\n         %s/open-scholar-peer%s\n\n' "$CYN$B" "$R"
printf '       %sThe orchestrator reads your session state and walks you through%s\n' "$DIM" "$R"
printf '       %sall seven steps, one command at a time.%s\n' "$DIM" "$R"
if [ "$failed" -ne 0 ]; then
  printf '\n  %sRe-run for the failed tool(s), or install one directly:%s\n' "$DIM" "$R"
  printf '  %sbash install.sh --tool <slug>%s\n' "$DIM" "$R"
fi
printf '\n'
[ "$failed" -eq 0 ] || exit 1
exit 0
