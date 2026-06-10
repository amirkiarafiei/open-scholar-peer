#!/usr/bin/env bash
# test_install.sh — Structure-validation smoke test for all installers.
#
# Runs each install_*.sh in a clean temp directory and verifies the expected
# files appear. Skips Python venv creation (slow, network-bound) by stubbing
# init_mcp.sh — pip install is exercised separately.
#
# Pass: exit 0. Any installer producing missing/wrong artifacts: exit 1.

set -e
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FAIL=0

stub_init_mcp() {
  # Replace init_mcp.sh with a fast no-network stub for the duration of the test.
  local target="$1/scripts/init_mcp.sh"
  cat > "$target" << 'STUB'
#!/usr/bin/env bash
# Smoke-test stub: skip venv creation, just create the directory tree and export paths.
TARGET_DIR="$(pwd)/.open-scholar-peer/mcp"
mkdir -p "$TARGET_DIR/.venv/bin"
touch "$TARGET_DIR/osp_mcp.py" "$TARGET_DIR/.venv/bin/python"
export OSP_MCP_PYTHON="$TARGET_DIR/.venv/bin/python"
export OSP_MCP_SERVER="$TARGET_DIR/osp_mcp.py"
echo "  [stub] init_mcp skipped venv setup"
STUB
  chmod +x "$target"
}

run_install_smoke() {
  local tool_name="$1"
  local installer="$2"
  shift 2
  local expected_files=("$@")

  echo ""
  echo "==> ${tool_name}"

  local sandbox repo_copy
  sandbox=$(mktemp -d)
  repo_copy=$(mktemp -d)

  # Copy the entire repo to a writable temp location so we can stub init_mcp.sh
  cp -r "$REPO_ROOT/." "$repo_copy/"
  stub_init_mcp "$repo_copy"

  # Run installer from sandbox (the installer's CWD becomes the user's project)
  pushd "$sandbox" >/dev/null
  if ! bash "$repo_copy/scripts/$installer" </dev/null > /tmp/osp_install_${tool_name}.log 2>&1; then
    echo -e "  ${RED}✗ installer exited non-zero. Tail of log:${NC}"
    tail -15 /tmp/osp_install_${tool_name}.log
    FAIL=1
    popd >/dev/null
    rm -rf "$sandbox" "$repo_copy"
    return
  fi
  popd >/dev/null

  # Verify expected files exist
  local missing=0
  for rel in "${expected_files[@]}"; do
    if [[ ! -e "$sandbox/$rel" ]]; then
      echo -e "  ${RED}✗ missing: $rel${NC}"
      missing=$((missing+1))
    fi
  done
  if [[ $missing -eq 0 ]]; then
    echo -e "  ${GREEN}✓ ${#expected_files[@]} expected files present${NC}"
  else
    FAIL=1
  fi

  rm -rf "$sandbox" "$repo_copy"
}

# Per-tool expected file lists (relative to the user's project dir)
COMMON=(
  ".brain/session.json"
  ".brain/raw"
  ".brain/review"
  ".brain/input"
  ".open-scholar-peer/mcp/osp_mcp.py"
  ".gitignore"
)

run_install_smoke "claude" "install_claude.sh" \
  "${COMMON[@]}" \
  ".claude/commands/0-osp-onboarding.md" \
  ".claude/commands/open-scholar-peer.md" \
  ".claude/skills/osp-orchestrator/SKILL.md" \
  ".claude/rules/osp-rules.md" \
  ".mcp.json"

run_install_smoke "cursor" "install_cursor.sh" \
  "${COMMON[@]}" \
  ".cursor/commands/0-osp-onboarding.md" \
  ".cursor/skills/osp-summary-agent/SKILL.md" \
  ".cursor/rules/osp-rules.mdc" \
  ".cursor/mcp.json"

run_install_smoke "gemini" "install_gemini.sh" \
  "${COMMON[@]}" \
  ".gemini/commands/0-osp-onboarding.toml" \
  ".gemini/skills/osp-query-agent/SKILL.md" \
  ".gemini/GEMINI.md" \
  ".gemini/settings.json"

run_install_smoke "antigravity" "install_antigravity.sh" \
  "${COMMON[@]}" \
  ".agents/workflows/0-osp-onboarding.md" \
  ".agent/workflows/0-osp-onboarding.md" \
  ".agent/skills/osp-historian-agent/SKILL.md" \
  ".open-scholar-peer/antigravity_mcp_snippet.json"

run_install_smoke "copilot" "install_copilot.sh" \
  "${COMMON[@]}" \
  ".github/prompts/0-osp-onboarding.md" \
  ".github/skills/osp-reviewer-agent/SKILL.md" \
  ".github/instructions/osp-rules.md" \
  "AGENTS.md"

run_install_smoke "junie" "install_junie.sh" \
  "${COMMON[@]}" \
  ".junie/commands/0-osp-onboarding.md" \
  ".junie/skills/osp-orchestrator/SKILL.md" \
  ".junie/guidelines.md" \
  ".junie/mcp/mcp.json"

run_install_smoke "kiro" "install_kiro.sh" \
  "${COMMON[@]}" \
  ".kiro/hooks/0-osp-onboarding.md" \
  ".kiro/skills/osp-orchestrator/SKILL.md" \
  ".kiro/steering/osp-rules.md" \
  ".kiro/settings/mcp.json"

run_install_smoke "codex" "install_codex.sh" \
  "${COMMON[@]}" \
  ".codex/prompts/0-osp-onboarding.md" \
  ".codex/skills/osp-orchestrator/SKILL.md" \
  "AGENTS.md" \
  ".open-scholar-peer/codex_mcp_snippet.toml"

run_install_smoke "kimi" "install_kimi.sh" \
  "${COMMON[@]}" \
  ".kimi/commands/0-osp-onboarding.md" \
  ".kimi/skills/osp-orchestrator/SKILL.md" \
  ".agents/skills/osp-orchestrator/SKILL.md" \
  "AGENTS.md"

run_install_smoke "qwen" "install_qwen.sh" \
  "${COMMON[@]}" \
  ".qwen/commands/0-osp-onboarding.md" \
  ".qwen/agents/osp-orchestrator/SKILL.md" \
  "QWEN.md" \
  ".qwen/settings.json"

run_install_smoke "vibe" "install_vibe.sh" \
  "${COMMON[@]}" \
  ".vibe/commands/0-osp-onboarding.md" \
  ".vibe/skills/osp-orchestrator/SKILL.md" \
  ".agents/skills/osp-orchestrator/SKILL.md" \
  "AGENTS.md" \
  ".open-scholar-peer/vibe_mcp_snippet.toml"

run_install_smoke "opencode" "install_opencode.sh" \
  "${COMMON[@]}" \
  ".opencode/commands/0-osp-onboarding.md" \
  ".opencode/agents/osp-orchestrator/SKILL.md" \
  "AGENTS.md" \
  ".open-scholar-peer/opencode_mcp_snippet.json"

run_install_smoke "openhands" "install_openhands.sh" \
  "${COMMON[@]}" \
  ".openhands/commands/0-osp-onboarding.md" \
  ".openhands/skills/osp-orchestrator/SKILL.md" \
  ".agents/skills/osp-orchestrator/SKILL.md" \
  "AGENTS.md" \
  ".open-scholar-peer/openhands_mcp_snippet.json"

echo ""
if [[ $FAIL -eq 0 ]]; then
  echo -e "${GREEN}✅ All installer smoke tests passed.${NC}"
  exit 0
else
  echo -e "${RED}❌ One or more installers failed. See logs in /tmp/osp_install_*.log${NC}"
  exit 1
fi
