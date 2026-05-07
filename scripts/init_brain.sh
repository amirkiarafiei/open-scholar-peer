#!/usr/bin/env bash
# Shared helper: initialize .brain/ directory at the current project root.
# Called by all install_*.sh scripts.

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
BRAIN_DIR="./.brain"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE="$SCRIPT_DIR/../.brain-template/session.json"

if [[ -d "$BRAIN_DIR" ]]; then
  echo -e "  ${YELLOW}ℹ️  .brain/ already exists — skipping init (your data is safe)${NC}"
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
  "paper": { "title": "", "path": "", "parsed_path": "", "type": "" },
  "qa_criteria": [],
  "phases": {
    "onboarding":     { "status": "pending", "started_at": "", "completed_at": "", "notes": "" },
    "summary":        { "status": "pending", "started_at": "", "completed_at": "", "notes": "" },
    "literature":     { "status": "pending", "started_at": "", "completed_at": "", "notes": "" },
    "historian":      { "status": "pending", "started_at": "", "completed_at": "", "notes": "" },
    "baseline_scout": { "status": "pending", "started_at": "", "completed_at": "", "notes": "" },
    "qa":             { "status": "pending", "started_at": "", "completed_at": "", "notes": "", "criteria_progress": {} },
    "review":         { "status": "pending", "started_at": "", "completed_at": "", "notes": "" }
  },
  "mcp": { "semantic_scholar_api_key_present": false },
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
