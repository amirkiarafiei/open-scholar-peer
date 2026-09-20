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
  UTF8=1
  ELL="…"; LINE="─"; ON="◉"; OFF="○"; CHK="▣"; BOX="□"; ARROW="›"; TICK="✓"; CROSS="✗"; DOT="·"
  TL="╭"; TR="╮"; BL="╰"; BR="╯"; VT="│"; UPDN="↑/↓"
  BTL="╔"; BTR="╗"; BBL="╚"; BBR="╝"; BVT="║"; BHZ="═"; BML="╠"; BMR="╣"
else
  UTF8=0
  ELL="~"; LINE="-"; ON="(*)"; OFF="( )"; CHK="[x]"; BOX="[ ]"; ARROW=">"; TICK="+"; CROSS="x"; DOT="-"
  TL="+"; TR="+"; BL="+"; BR="+"; VT="|"; UPDN="up/down"
  BTL="+"; BTR="+"; BBL="+"; BBR="+"; BVT="|"; BHZ="="; BML="+"; BMR="+"
fi

# Subagent isolation for /5-osp-qa, and how the MCP server gets wired.
# Built here, not with the other arrays, so the separator honours the locale.
TOOL_HINTS=(
  "subagents $DOT .mcp.json auto"
  "subagents $DOT .cursor/mcp.json auto"
  "subagents* $DOT global config auto"
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

# The paper databases the MCP server can use. Index-aligned, like the tools.
# Built here because the domain column uses $DOT, which the locale decides.
# Order matches mcp-server/README.md.
DB_NAMES=(
  "arXiv" "Semantic Scholar" "Google Scholar"
  "Europe PMC" "Zenodo" "OpenAlex"
)
DB_SLUGS=(
  "arxiv" "semantic_scholar" "google_scholar"
  "europepmc" "zenodo" "openalex"
)
# Empty means no key exists at all. Otherwise it is the .env variable an
# optional key goes in. No database here ever REQUIRES a key — that would
# break the promise that OSP runs on open sources (MANIFESTO rule 1).
DB_ENVVARS=(
  "" "SEMANTIC_SCHOLAR_API_KEY" ""
  "" "ZENODO_API_TOKEN" "OPENALEX_API_KEY"
)
# Selected when the picker opens. arXiv and Semantic Scholar only: they are
# the two that serve every field, and a reviewer can add the rest with one
# keypress. Starting with all six hands a CS reviewer four sources they will
# never use, and a longer tool list on every agent request.
DB_DEFAULTS=(1 1 0 0 0 0)

DB_DOMAINS=(
  "preprints $DOT CS, physics, maths"
  "all fields $DOT citation graph"
  "broad $DOT best-effort scraping"
  "biomedical $DOT full text"
  "code, data and software releases"
  "all fields $DOT retraction flags"
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
  if [ "$w" -ge 62 ] && [ "$UTF8" -eq 1 ]; then
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
trap on_interrupt INT TERM HUP

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
    printf '   %s%s move %s enter select %s q cancel%s\n' "$DIM" "$UPDN" "$DOT" "$DOT" "$R"
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
  local context=$1 verb=${2:-Install}
  local n=${#TOOL_NAMES[@]}
  local cur=0 top=0 drawn=0 i key win rows count layout marks=""

  i=0; while [ "$i" -lt "$n" ]; do marks="${marks}0"; i=$((i + 1)); done

  hide_cursor
  while :; do
    # Re-measured every frame: the window can be resized mid-menu, and geometry
    # captured once would make every later rewind clamp at row 0 and clip the
    # top of the menu permanently.
    rows=$(term_rows)
    layout=0
    [ $(( 13 + n )) -ge "$rows" ] && layout=1
    [ $((  9 + n )) -ge "$rows" ] && layout=2
    win=$n
    if [ "$layout" -eq 2 ]; then
      # Layout 2's chrome is 4 lines (title, scroll indicator, inline button,
      # help), plus one row left in hand so a full-height frame does not scroll.
      win=$(( rows - 5 )); [ "$win" -lt 1 ] && win=1; [ "$win" -gt "$n" ] && win=$n
    fi
    [ "$cur" -gt "$n" ] && cur=$n
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
      if [ "$count" -eq 1 ]; then blabel="$verb for 1 tool"; else blabel="$verb for $count tools"; fi
    else
      benabled=0; blabel="$verb"
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
      printf '     %s* Antigravity falls back to self-reflection if delegation is unavailable%s\n' \
        "$DIM" "$R"; drawn=$((drawn + 1))
      printf '     %s%s move %s space toggle %s a all %s n none %s tab %s button%s\n' \
        "$DIM" "$UPDN" "$DOT" "$DOT" "$DOT" "$DOT" "$ARROW" "$R"; drawn=$((drawn + 1))
      printf '     %spast the last tool is the %s button %s q cancel%s\n' \
        "$DIM" "$verb" "$DOT" "$R"; drawn=$((drawn + 1))
    else
      printf '     %s%s %s space toggle %s a all %s tab to the button %s q cancel%s\n' \
        "$DIM" "$UPDN" "$DOT" "$DOT" "$DOT" "$DOT" "$R"; drawn=$((drawn + 1))
    fi

    key=$(read_key)
    case "$key" in
      up | k)   cur=$((cur - 1)); [ "$cur" -lt 0 ] && cur=$n ;;
      down | j) cur=$((cur + 1)); [ "$cur" -gt "$n" ] && cur=0 ;;
      pgup)     cur=$((cur - win)); [ "$cur" -lt 0 ] && cur=0 ;;
      pgdn)     cur=$((cur + win)); [ "$cur" -gt "$n" ] && cur=$n ;;
      home)     cur=0 ;;
      end | tab) cur=$n ;;
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


# The six paper databases, plus one focusable Continue button underneath.
# Same keyboard model as menu_tools, and the same rule about geometry: the
# window can be resized mid-menu, so every frame re-measures.
DB_SELECTED=()
menu_databases() {
  local verb=${1:-Continue}
  local n=${#DB_NAMES[@]}
  local cur=0 top=0 drawn=0 i key win rows count layout marks=""

  # From DB_DEFAULTS, not all-on.
  i=0; while [ "$i" -lt "$n" ]; do marks="${marks}${DB_DEFAULTS[$i]}"; i=$((i + 1)); done

  hide_cursor
  while :; do
    rows=$(term_rows)
    layout=0
    [ $(( 13 + n )) -ge "$rows" ] && layout=1
    [ $((  9 + n )) -ge "$rows" ] && layout=2
    win=$n
    if [ "$layout" -eq 2 ]; then
      win=$(( rows - 5 )); [ "$win" -lt 1 ] && win=1; [ "$win" -gt "$n" ] && win=$n
    fi
    [ "$cur" -gt "$n" ] && cur=$n
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
    printf '  %sWhich paper databases should the agent search?%s   %s%d of %d selected%s\n' \
      "$B" "$R" "$DIM" "$count" "$n" "$R"; drawn=$((drawn + 1))
    if [ "$layout" -eq 0 ]; then
      printf '  %sFewer databases means a shorter tool list and faster searches.%s\n' \
        "$DIM" "$R"; drawn=$((drawn + 1))
    fi
    if [ "$layout" -lt 2 ]; then printf '\n'; drawn=$((drawn + 1)); fi

    i=$top
    while [ "$i" -lt $((top + win)) ] && [ "$i" -lt "$n" ]; do
      local box name keycol domain
      if [ "${marks:$i:1}" = "1" ]; then box="${GRN}${CHK}${R}"; else box="${GRY}${BOX}${R}"; fi
      name=${DB_NAMES[$i]}; domain=${DB_DOMAINS[$i]}
      if [ -n "${DB_ENVVARS[$i]}" ]; then
        keycol="${YEL}optional key${R}"
      else
        keycol="${GRN}free${R}        "
      fi
      if [ "$i" -eq "$cur" ]; then
        printf ' %s %s %s%-17s%s %s  %s%s%s\n' \
          "$ARROW" "$box" "$CYN$B" "$name" "$R" "$keycol" "$DIM" "$domain" "$R"
      else
        printf '   %s %-17s %s  %s%s%s\n' "$box" "$name" "$keycol" "$GRY" "$domain" "$R"
      fi
      drawn=$((drawn + 1)); i=$((i + 1))
    done

    if [ "$win" -lt "$n" ]; then
      printf '   %s%d-%d of %d%s\n' "$DIM" $((top + 1)) "$i" "$n" "$R"; drawn=$((drawn + 1))
    fi

    if [ "$layout" -lt 2 ]; then printf '\n'; drawn=$((drawn + 1)); fi
    # The button says what pressing it actually does. If anything currently
    # ticked can take a key, a question follows and this is not yet the
    # install — promising "Install" and then asking one more thing is the
    # kind of small lie that makes an installer feel untrustworthy.
    local vnow=$verb j
    if [ "$verb" = "Install" ]; then
      j=0
      while [ "$j" -lt "$n" ]; do
        if [ "${marks:$j:1}" = "1" ] && [ -n "${DB_ENVVARS[$j]}" ]; then
          local kv; eval "kv=\${${DB_ENVVARS[$j]}:-}"
          [ -z "$kv" ] && { vnow="Continue"; break; }
        fi
        j=$((j + 1))
      done
    fi

    local blabel benabled=1 bfocus=0
    if [ "$count" -gt 0 ]; then
      if [ "$count" -eq 1 ]; then blabel="$vnow with 1 database"; else blabel="$vnow with $count databases"; fi
    else
      benabled=0; blabel="$vnow"
      [ "$cur" -eq "$n" ] && blabel="Pick at least one database"
    fi
    [ "$cur" -eq "$n" ] && bfocus=1
    if [ "$layout" -eq 2 ]; then
      draw_button_inline "$blabel" "$bfocus" "$benabled"; drawn=$((drawn + 1))
    else
      draw_button "$blabel" "$bfocus" "$benabled"; drawn=$((drawn + 3))
    fi

    if [ "$layout" -eq 0 ]; then
      printf '\n'; drawn=$((drawn + 1))
      printf '     %soptional key = works without one, but a key lifts the rate limit%s\n' \
        "$DIM" "$R"; drawn=$((drawn + 1))
      printf '     %s%s move %s space toggle %s a all %s n none %s tab %s button%s\n' \
        "$DIM" "$UPDN" "$DOT" "$DOT" "$DOT" "$DOT" "$ARROW" "$R"; drawn=$((drawn + 1))
      printf '     %spast the last row is the %s button %s q cancel%s\n' \
        "$DIM" "$vnow" "$DOT" "$R"; drawn=$((drawn + 1))
    else
      printf '     %s%s %s space toggle %s a all %s tab to the button %s q cancel%s\n' \
        "$DIM" "$UPDN" "$DOT" "$DOT" "$DOT" "$DOT" "$R"; drawn=$((drawn + 1))
    fi

    key=$(read_key)
    case "$key" in
      up | k)   cur=$((cur - 1)); [ "$cur" -lt 0 ] && cur=$n ;;
      down | j) cur=$((cur + 1)); [ "$cur" -gt "$n" ] && cur=0 ;;
      pgup)     cur=$((cur - win)); [ "$cur" -lt 0 ] && cur=0 ;;
      pgdn)     cur=$((cur + win)); [ "$cur" -gt "$n" ] && cur=$n ;;
      home)     cur=0 ;;
      end | tab) cur=$n ;;
      a | A)    marks=""; i=0; while [ "$i" -lt "$n" ]; do marks="${marks}1"; i=$((i + 1)); done ;;
      n | N)    marks=""; i=0; while [ "$i" -lt "$n" ]; do marks="${marks}0"; i=$((i + 1)); done ;;
      space | left | right | h | l)
        if [ "$cur" -lt "$n" ]; then
          if [ "${marks:$cur:1}" = "1" ]; then marks="${marks:0:$cur}0${marks:$((cur + 1))}"
          else marks="${marks:0:$cur}1${marks:$((cur + 1))}"; fi
        fi ;;
      enter)
        if [ "$cur" -lt "$n" ]; then
          if [ "${marks:$cur:1}" = "1" ]; then marks="${marks:0:$cur}0${marks:$((cur + 1))}"
          else marks="${marks:0:$cur}1${marks:$((cur + 1))}"; fi
        elif [ "$count" -gt 0 ]; then
          DB_SELECTED=()
          i=0; while [ "$i" -lt "$n" ]; do
            [ "${marks:$i:1}" = "1" ] && DB_SELECTED[${#DB_SELECTED[@]}]=$i
            i=$((i + 1))
          done
          rewind "$drawn"; show_cursor
          printf '  %s%s%s %sSelected %d database(s)%s\n' \
            "$GRN" "$TICK" "$R" "$DIM" "${#DB_SELECTED[@]}" "$R"
          return 0
        fi ;;
      q | esc | eof) show_cursor; DB_SELECTED=(); return 1 ;;
    esac
  done
}

# db_slug_to_index <slug> -> echoes index, or nothing when unknown.
db_slug_to_index() {
  local want=$1 i=0
  # Same aliases osp_mcp.py accepts, so a name that works in .env is not
  # rejected here.
  case "$want" in
    europe_pmc|epmc|pmc) want="europepmc" ;;
    s2|semanticscholar)  want="semantic_scholar" ;;
    scholar|gscholar)    want="google_scholar" ;;
    open_alex|openalex_works) want="openalex" ;;
  esac
  while [ "$i" -lt "${#DB_SLUGS[@]}" ]; do
    [ "${DB_SLUGS[$i]}" = "$want" ] && { printf '%s' "$i"; return 0; }
    i=$((i + 1))
  done
  return 1
}

# True when at least one selected database can take a key that is not already
# in the environment. Without this the yes/no question would be asked even
# when there is nothing to ask for.
keyed_databases_selected() {
  local idx var val
  for idx in $SELECTED_DB; do
    var=${DB_ENVVARS[$idx]}
    [ -z "$var" ] && continue
    eval "val=\${$var:-}"
    [ -z "$val" ] && return 0
  done
  return 1
}

# Offer to type each optional key, once, before anything is installed.
# A key is NEVER required to finish: every database here answers without one.
# Keys are read with `read -rs`, so they are not echoed and never reach a log.
collect_keys() {
  local i idx var name val asked=0
  for idx in $SELECTED_DB; do
    var=${DB_ENVVARS[$idx]}
    [ -z "$var" ] && continue
    name=${DB_NAMES[$idx]}
    # Already in the environment? Leave it alone and say nothing.
    eval "val=\${$var:-}"
    [ -n "$val" ] && continue
    if [ "$asked" -eq 0 ]; then
      printf '\n  %sOptional API keys%s\n' "$B" "$R"
      printf '  %sPress Enter to skip any of these. Everything works without them.%s\n\n' \
        "$DIM" "$R"
      asked=1
    fi
    printf '  %s key for %s%s%s (Enter to skip): ' "$var" "$CYN" "$name" "$R"
    IFS= read -rs val <"$TTY" || val=""
    printf '\n'
    # Trim: a key pasted from a web page often brings a leading or trailing
    # space, and a key that is silently wrong is worse than no key.
    val=$(printf '%s' "$val" | tr -d '[:space:]')
    if [ -n "$val" ]; then
      OSP_KEY_NAMES="$OSP_KEY_NAMES $var"
      eval "OSP_KEY_$var=\$val"
      ok "$name key noted"
    else
      printf '     %sskipped%s\n' "$DIM" "$R"
    fi
  done
  if [ "$asked" -eq 1 ]; then
    printf '\n  %sYou can add or change keys later in %s.env%s%s\n' \
      "$DIM" "$B" "$R$DIM" "$R"
  fi
}

# Turn the chosen indices into the OSP_SOURCES line the MCP server reads, and
# export the keys so init_mcp.sh can write them. init_mcp.sh is sourced once
# per selected tool, so it must not prompt; everything is collected here.
export_source_env() {
  local idx list=""
  for idx in $SELECTED_DB; do
    if [ -z "$list" ]; then list="${DB_SLUGS[$idx]}"; else list="$list,${DB_SLUGS[$idx]}"; fi
  done
  [ -n "$list" ] && export OSP_SOURCES="$list"
  export OSP_KEY_NAMES
  local var
  for var in $OSP_KEY_NAMES; do
    eval "export OSP_KEY_$var"
  done
}

# --------------------------------------------------------------- box ------
#
# The closing panel. Width is measured on PLAIN text and the colour is wrapped
# around it afterwards, the same discipline draw_button uses — a colour code
# counted as visible characters would push every right-hand border out of line.

BOXW=74

# Display columns, not characters and not bytes. `${#s}` counts characters in
# a UTF-8 locale and bytes in C, and neither is the width a terminal gives a
# CJK glyph — a path with wide characters pushed the right border out by one
# column per glyph. `wc -L` knows; where it does not exist, fall back.
_dispw() {
  local n
  n=$(printf '%s' "$1" | wc -L 2>/dev/null | tr -d ' ')
  case "$n" in ''|*[!0-9]*) n=${#1} ;; esac
  printf '%s' "$n"
}

# Fit the panel to the terminal. hr() already clamps at 78; the box did not,
# so a narrow window shredded all seventeen rows.
box_fit() {
  local cols; cols=$(term_cols)
  BOXW=74
  [ "$cols" -lt 78 ] && BOXW=$(( cols - 4 ))
  [ "$BOXW" -lt 24 ] && BOXW=24
}

box_rule() {   # box_rule <left glyph> <right glyph>
  local i=0 bar=""
  while [ "$i" -lt "$BOXW" ]; do bar="${bar}${BHZ}"; i=$((i + 1)); done
  printf '  %s%s%s%s%s\n' "$GRN" "$1" "$bar" "$2" "$R"
}

box_row() {    # box_row <plain text>  |  box_row <plain text> <coloured text>
  local plain=$1 shown=${2:-$1} pad w
  w=$(_dispw "$plain")
  if [ "$w" -gt "$BOXW" ]; then
    # Say it was cut. Silently truncating the line that tells the user where
    # the thing installed is worse than an ugly line.
    plain="${plain:0:$((BOXW - 1))}$ELL"; shown=$plain; w=$(_dispw "$plain")
  fi
  pad=$(( BOXW - w )); [ "$pad" -lt 0 ] && pad=0
  printf '  %s%s%s%s%*s%s%s%s\n' \
    "$GRN" "$BVT" "$R" "$shown" "$pad" "" "$GRN" "$BVT" "$R"
}

# join_names <array-name> <index list> -> "A · B · C", truncated to fit
join_names() {
  local arr=$1 out="" name i
  shift
  for i in $@; do
    eval "name=\${${arr}[$i]}"
    if [ -z "$out" ]; then out="$name"; else out="$out $DOT $name"; fi
  done
  printf '%s' "$out"
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
  bash install.sh --sources arxiv,openalex
                                        choose the paper databases, no prompts
  bash install.sh --dir ~/papers/acl     install into another directory
  bash install.sh --list                 list tool slugs
  bash install.sh -h | --help            this message

Interactive keys:
  up/down move  |  space or enter toggle  |  a all  |  n none  |  q cancel
  Arrow past the last tool to reach the Install button, then press enter.

Tool slugs:
USAGE
  list_slugs
}

# ----------------------------------------------------------------- main ----

TARGET=""
CLI_TOOLS=""
TOOL_FLAG_SEEN=0
SOURCES_FLAG_SEEN=0
CLI_SOURCES=""
SELECTED_DB=""
OSP_KEY_NAMES=""
while [ $# -gt 0 ]; do
  case "$1" in
    -h | --help) usage; exit 0 ;;
    --list)      list_slugs; exit 0 ;;
    --tool)      CLI_TOOLS="$2"; TOOL_FLAG_SEEN=1; shift 2 || { bad "--tool needs a value"; exit 2; } ;;
    --tool=*)    CLI_TOOLS="${1#--tool=}"; TOOL_FLAG_SEEN=1; shift ;;
    --sources)   CLI_SOURCES="$2"; SOURCES_FLAG_SEEN=1; shift 2 || { bad "--sources needs a value"; exit 2; } ;;
    --sources=*) CLI_SOURCES="${1#--sources=}"; SOURCES_FLAG_SEEN=1; shift ;;
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
  info "Remote install - fetching Open ScholarPeer"
  TEMP_DIR=$(mktemp -d) || { bad "Could not create a temporary directory."; exit 1; }
  if ! git clone --depth 1 "$REPO_URL" "$TEMP_DIR" >/dev/null 2>&1; then
    bad "Failed to clone $REPO_URL. Check your network and retry."
    exit 1
  fi
  SOURCE_DIR="$TEMP_DIR"
else
  info "Local checkout - installing from $SOURCE_DIR"
fi

# --- Non-interactive path ----------------------------------------------------
# Chosen when --tool is given, or forced when there is no terminal to draw on.
TTY="/dev/tty"
HAVE_TTY=1
{ [ -r "$TTY" ] && [ -t 1 ]; } || HAVE_TTY=0

SELECTED_IDX=""
if [ "$TOOL_FLAG_SEEN" -eq 1 ]; then
  OLD_IFS=$IFS; IFS=','
  for slug in $CLI_TOOLS; do
    IFS=$OLD_IFS
    slug=$(printf '%s' "$slug" | tr -d '[:space:]')
    [ -z "$slug" ] && continue
    if idx=$(slug_to_index "$slug"); then
      # Skip a repeat: `--tool claude,claude` must install once, not twice.
      case " $SELECTED_IDX " in
        *" $idx "*) ;;
        *) SELECTED_IDX="$SELECTED_IDX $idx" ;;
      esac
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
fi

# --sources works with or without --tool, so it is parsed on its own.
if [ "$SOURCES_FLAG_SEEN" -eq 1 ]; then
  OLDIFS=$IFS; IFS=','
  for slug in $CLI_SOURCES; do
    slug=$(printf '%s' "$slug" | tr -d '[:space:]')
    [ -z "$slug" ] && continue
    if ! idx=$(db_slug_to_index "$slug"); then
      IFS=$OLDIFS
      bad "Unknown database: $slug"
      say ""
      say "  Known databases:"
      i=0
      while [ "$i" -lt "${#DB_SLUGS[@]}" ]; do
        printf '    %s%-18s%s %s\n' "$B" "${DB_SLUGS[$i]}" "$R" "${DB_NAMES[$i]}"
        i=$((i + 1))
      done
      exit 2
    fi
    case " $SELECTED_DB " in
      *" $idx "*) ;;
      *) SELECTED_DB="$SELECTED_DB $idx" ;;
    esac
  done
  IFS=$OLDIFS
  if [ -z "$SELECTED_DB" ]; then bad "--sources given but no database parsed."; exit 2; fi
fi

# The no-TTY refusal belongs to --tool, and nothing else. M13 briefly hung it
# off the --sources block instead, which meant `install.sh --tool claude > log`
# refused to run at all — breaking every pipe, tee, CI job and Dockerfile, and
# contradicting the README. It tests whether the TOOL flag was seen, which is
# also what finding 7 of the M9 review established.
if [ "$TOOL_FLAG_SEEN" -eq 0 ] && [ "$HAVE_TTY" -eq 0 ]; then
  hr
  if [ -r "$TTY" ]; then
    bad "Standard output is not a terminal, and no --tool given."
    say ""
    say "  The menus draw to stdout, so redirecting it (a pipe, > file, tee)"
    say "  would hide them. Either drop the redirection, or name the tool up front."
  else
    bad "No interactive terminal available, and no --tool given."
    say ""
    say "  The menus need a terminal."
  fi
  say ""
  say "  Run it interactively:"
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
  # Step 1 — where. Guards against running `curl | bash` in the wrong directory.
  # Skipped entirely when --dir already answered it, separator included.
  if [ -z "$TARGET" ]; then
    hr; printf '\n'
    MENU_SUB="Your paper, the .brain/ working state and the MCP runtime all live here."
    if ! menu_single "Step 1 of 3 $DOT Where should Open ScholarPeer be installed?" 0 \
      "This directory   $INVOKED_FROM" \
      "Another path..."; then
      printf '\n'; bad "Cancelled - nothing was installed."; exit 130
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

  # Whichever picker runs last is the one that starts the install, so only it
  # says "Install". With --sources the database step is skipped and the tool
  # menu is last; otherwise the database menu is.
  tools_verb="Continue"
  # Install only when this really is the last thing: the database step must be
  # skipped AND no key question can follow. Checking only the flag made the
  # button promise an install and then ask one more question — the exact lie
  # the per-frame check on the database menu exists to prevent.
  if [ "$SOURCES_FLAG_SEEN" -eq 1 ] && ! keyed_databases_selected; then
    tools_verb="Install"
  fi

  # Step 2 — which agents.
  if ! menu_tools "Into $TARGET" "$tools_verb"; then
    printf '\n'; bad "Cancelled - nothing was installed."; exit 130
  fi
  SELECTED_IDX="${MULTI_SELECTED[*]}"

  # Step 3 — which databases, then the keys they may want.
  if [ "$SOURCES_FLAG_SEEN" -eq 0 ]; then
    printf '\n'; hr; printf '\n'
    if ! menu_databases "Install"; then
      printf '\n'; bad "Cancelled - nothing was installed."; exit 130
    fi
    SELECTED_DB="${DB_SELECTED[*]}"
  fi

  # Ask once whether to enter keys at all, rather than walking the user
  # through a prompt per database. Only asked when a selected database
  # actually takes one — with the default arXiv + Semantic Scholar that is a
  # single question.
  if keyed_databases_selected; then
    printf '\n'
    MENU_SUB="Every database works without a key. A key only lifts a rate limit."
    if menu_single "Do you want to enter API keys now?" 1 \
      "Yes - ask me for each one" \
      "No - I will add them to .env later"; then
      [ "$MENU_CHOICE" -eq 0 ] && collect_keys
    fi
    MENU_SUB=""
  fi
fi

# Nothing chosen — a scripted run with --tool and no --sources. Enable every
# database, which is what an unset OSP_SOURCES already means to the server.
if [ -z "$SELECTED_DB" ]; then
  i=0
  while [ "$i" -lt "${#DB_SLUGS[@]}" ]; do
    SELECTED_DB="$SELECTED_DB $i"; i=$((i + 1))
  done
fi
export_source_env

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
    bad "$name - installer exited non-zero (see the output above)"
  fi
done

# --- Summary -----------------------------------------------------------------
printf '\n'
if [ "$installed" -eq 0 ]; then
  hr
  printf '  %s%s Nothing was installed - %d tool(s) failed:%s%s\n' \
    "$RED$B" "$CROSS" "$failed" "$failed_names" "$R"
  printf '\n  %sRe-run for the failed tool(s), or install one directly:%s\n' "$DIM" "$R"
  printf '  %sbash install.sh --tool <slug>%s\n\n' "$DIM" "$R"
  exit 1
fi

# What the user ended up with. Built before drawing so each row is one string
# whose length can be measured.
# What actually installed, not what was asked for: a failed tool was being
# named as installed four lines under the line reporting it failed.
agents_line=${installed_names# }
[ -z "$agents_line" ] && agents_line="(none)"
agents_line=$(printf '%s' "$agents_line" | sed "s/  */ $DOT /g")
dbs_line=$(join_names DB_NAMES $SELECTED_DB)

keys_set=0; keys_possible=0
for i in $SELECTED_DB; do
  var=${DB_ENVVARS[$i]}
  [ -z "$var" ] && continue
  keys_possible=$((keys_possible + 1))
  # Either already in the environment, or typed during this run — collect_keys
  # stores those under OSP_KEY_<name>, so reading only $var reported "none set"
  # right after the user had entered one.
  eval "val=\${$var:-}"
  [ -z "$val" ] && eval "val=\${OSP_KEY_$var:-}"
  [ -n "$val" ] && keys_set=$((keys_set + 1))
done
if [ "$keys_possible" -eq 0 ]; then
  keys_line="none needed - every database you picked is key-free"
elif [ "$keys_set" -eq 0 ]; then
  keys_line="none set $DOT optional, see .env"
else
  keys_line="$keys_set of $keys_possible set $DOT the rest are optional"
fi

box_fit
box_rule "$BTL" "$BTR"
box_row  "  $TICK  Open ScholarPeer installed at:" \
         "  ${GRN}${B}${TICK}${R}  ${B}Open ScholarPeer installed at:${R}"
box_row  "       $TARGET" "       ${DIM}${TARGET}${R}"
if [ "$failed" -ne 0 ]; then
  box_row "       $failed tool(s) failed:$failed_names" \
          "       ${YEL}${failed} tool(s) failed:${failed_names}${R}"
fi
box_rule "$BML" "$BMR"
box_row  ""
box_row  "  AGENTS" "  ${B}AGENTS${R}"
box_row  "       $agents_line"
box_row  ""
box_row  "  DATABASES" "  ${B}DATABASES${R}"
box_row  "       $dbs_line"
box_row  ""
box_row  "  API KEYS" "  ${B}API KEYS${R}"
box_row  "       $keys_line"
box_row  ""
box_rule "$BML" "$BMR"
box_row  ""
box_row  "  WHAT TO DO NEXT" "  ${B}WHAT TO DO NEXT${R}"
box_row  ""
box_row  "       1  Put the paper you want reviewed in this directory"
box_row  "       2  Open your code agent here and run"
box_row  ""
box_row  "          /open-scholar-peer" "          ${CYN}${B}/open-scholar-peer${R}"
box_row  ""
box_rule "$BBL" "$BBR"

printf '\n     %s%s%s  Add API keys any time in %s.env%s  %s- every database works without one%s\n' \
  "$YEL" "$OFF" "$R" "$B" "$R" "$DIM" "$R"

if [ "$failed" -ne 0 ]; then
  printf '\n  %sRe-run for the failed tool(s), or install one directly:%s\n' "$DIM" "$R"
  printf '  %sbash install.sh --tool <slug>%s\n' "$DIM" "$R"
fi
printf '\n'
[ "$failed" -eq 0 ] || exit 1
exit 0
