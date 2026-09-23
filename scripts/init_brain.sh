#!/usr/bin/env bash
# Shared helper: initialize .brain/ directory at the current project root.
# Called by all install_*.sh scripts.

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
BRAIN_DIR="./.brain"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE="$SCRIPT_DIR/../.brain-template/session.json"

# Say which version this is, and what it is replacing, before anything is written.
. "$SCRIPT_DIR/_version.sh"
osp_announce_version

if [[ -d "$BRAIN_DIR" ]]; then
  echo -e "  ${YELLOW}ℹ️  .brain/ already exists — skipping init (your data is safe)${NC}"

  # The session file's shape grows between releases, and .brain/ is never
  # overwritten, so an older review lacks fields the newer prompts describe.
  # Offer to add them — additive, backed up, and never without being told.
  _osp_py="$(command -v python3 || true)"
  if [[ -n "$_osp_py" && -f "$BRAIN_DIR/session.json" ]]; then
    _osp_n="$("$_osp_py" "$SCRIPT_DIR/migrate_session.py" --check 2>/dev/null | grep -c . || true)"
    if [[ "${_osp_n:-0}" -gt 0 ]]; then
      echo -e "  ${YELLOW}ℹ️  This review is from an older version — $_osp_n field(s) the new"
      echo -e "      prompts use are missing. Adding them changes nothing you wrote.${NC}"

      _osp_do=""
      if [[ -n "${OSP_MIGRATE:-}" ]]; then
        # Scripted installs decide up front; never prompt.
        [[ "$OSP_MIGRATE" == "1" ]] && _osp_do=yes
      elif [[ -t 0 ]]; then
        read -r -p "      Add them? [Y/n] " _osp_ans
        [[ "$_osp_ans" =~ ^([Nn]) ]] || _osp_do=yes
      else
        # No terminal to answer on — curl | bash, or a scripted --tool run.
        # Never write to someone's review unasked, and never wait for an answer
        # that cannot arrive.
        echo -e "      ${YELLOW}Not a terminal, so nothing changed. To add them, re-run with"
        echo -e "      OSP_MIGRATE=1 in front of the same command.${NC}"
      fi

      if [[ -n "$_osp_do" ]]; then
        if "$_osp_py" "$SCRIPT_DIR/migrate_session.py" --apply >/dev/null 2>&1; then
          echo -e "  ${GREEN}✅ session.json updated — $_osp_n field(s) added, previous file kept"
          echo -e "      as session.json.before-upgrade${NC}"
        else
          echo -e "  ${YELLOW}⚠️  Could not update session.json; it was left alone.${NC}"
        fi
      fi
      unset _osp_n _osp_do _osp_ans
    fi
  fi
  unset _osp_py
else
  mkdir -p "$BRAIN_DIR/raw" "$BRAIN_DIR/review"
  TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date -u +"%Y-%m-%dT%H:%M:%SZ")

  if command -v python3 &>/dev/null && [[ -f "$TEMPLATE" ]]; then
    python3 -c "
import json
with open('$TEMPLATE') as f:
    d = json.load(f)
d['created_at'] = '$TIMESTAMP'
d['updated_at'] = '$TIMESTAMP'
with open('$BRAIN_DIR/session.json', 'w') as f:
    json.dump(d, f, indent=2)
" 2>/dev/null || cp "$TEMPLATE" "$BRAIN_DIR/session.json"
  elif [[ -f "$TEMPLATE" ]]; then
    cp "$TEMPLATE" "$BRAIN_DIR/session.json"
  else
    # Bare-minimum v2 fallback if template is missing
    cat > "$BRAIN_DIR/session.json" << JSON
{
  "protocol": "OpenScholarPeer",
  "version": "2.0",
  "created_at": "$TIMESTAMP",
  "updated_at": "$TIMESTAMP",
  "venue": { "name": "", "year": "", "source_url": "", "criteria_source": "pending" },
  "paper": { "title": "", "path": "", "parsed_path": "", "type": "", "id": "", "cutoff_date": "" },
  "qa_criteria": [],
  "qa_pairs_per_criterion": 2,
  "_phase_status_values": ["pending", "in_progress", "completed", "skipped"],
  "phases": {
    "onboarding":     { "status": "pending", "started_at": "", "completed_at": "", "notes": "", "skip_reason": "" },
    "summary":        { "status": "pending", "started_at": "", "completed_at": "", "notes": "", "skip_reason": "" },
    "literature":     { "status": "pending", "started_at": "", "completed_at": "", "notes": "", "skip_reason": "", "rounds_completed": 0 },
    "historian":      { "status": "pending", "started_at": "", "completed_at": "", "notes": "", "skip_reason": "" },
    "baseline_scout": { "status": "pending", "started_at": "", "completed_at": "", "notes": "", "skip_reason": "" },
    "qa":             { "status": "pending", "started_at": "", "completed_at": "", "notes": "", "skip_reason": "", "criteria_progress": {} },
    "review":         { "status": "pending", "started_at": "", "completed_at": "", "notes": "", "skip_reason": "" }
  },
  "_interface_values": ["mcp", "cli", "none"],
  "mcp": { "semantic_scholar_api_key_present": false, "interface": "" },
  "resume_from": "onboarding",
  "notes": ""
}
JSON
  fi
  # Ensure input/ subdir exists for paper drop-off
  mkdir -p "$BRAIN_DIR/input"
  echo -e "  ${GREEN}✅ .brain/ initialized${NC}"
fi

# Add .brain/ to .gitignore
GITIGNORE="./.gitignore"
if [[ -f "$GITIGNORE" ]]; then
  if ! grep -qF ".brain/" "$GITIGNORE" 2>/dev/null; then
    printf "\n# Open ScholarPeer working files (may contain confidential paper content)\n.brain/\n" >> "$GITIGNORE"
    echo -e "  ${GREEN}✅ Added .brain/ to .gitignore${NC}"
  fi
else
  printf "# Open ScholarPeer working files (may contain confidential paper content)\n.brain/\n" > "$GITIGNORE"
  echo -e "  ${GREEN}✅ Created .gitignore with .brain/ entry${NC}"
fi
