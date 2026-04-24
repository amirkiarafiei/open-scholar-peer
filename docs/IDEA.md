# IDEA: ScholarPeer Open-Source Implementation (Master Seed Document)

## 1. Executive Summary & Core Vision
The objective of this project is to develop a robust, open-source, community-driven implementation of the **ScholarPeer** academic paper ("A Context-Aware Multi-Agent Framework for Automated Peer Review"). The goal is to translate this theoretical, multi-agent academic framework into functional, highly adaptable code.

**The Core Philosophy:** Eliminate vendor lock-in and UI dependency. 
Users must be able to leverage this methodology using their own API keys, local LLMs, or existing agentic environments without being forced into a specific subscription or proprietary web interface. The system must live where the developers and researchers already work.

**Primary Deliverables:**
1. **The Ecosystem Integrations (Now):** A portable, install-script-based set of tool-native folders and files (Skills, Commands/Workflows, Subagents, MCP config, and rules/instructions) copied into the user project root (ReviewerOS style), without relying on plugin marketplaces.
2. **The Standalone Web Application (Later):** A pre-built web app powered by **DeepAgents JS** (backend) and a customized **Deep Agents UI** (frontend), with BYOK support and phase progress UX.

---

## 1.1 Current Scope Decisions (Locked)

### A. Monorepo top-level structure
At the root of this project, we standardize on:
- `docs/`
- `src/`
  - `src/frontend/` (later phase)
  - `src/backend/` (later phase)
- `extensions/` (current priority)

### B. Supported tools in current phase
For now, we support exactly:
1. Cursor (`.cursor`)
2. Claude Code (`.claude`)
3. Antigravity (`.agent` target, with compatibility for `.agents`)
4. GitHub Copilot / VS Code (`.github` + `AGENTS.md` as needed)
5. Gemini CLI (`.gemini`)

### C. Delivery model to avoid ecosystem lock-in
- Do **not** depend on marketplace plugins as the primary packaging model.
- Keep all tool-specific assets as plain files in this repository under `extensions/`.
- Use shell installers to copy the relevant folder into the user project root.
- This intentionally mirrors the operational style of ReviewerOS.

---

## 2. The Scientific Foundation: The ScholarPeer Methodology
Before defining the code architecture, we must explicitly define the scientific pipeline we are replicating. ScholarPeer solves the "parametric vacuum" problem of LLM peer reviews by actively fetching external context from the live web. It relies on a three-phase, dual-stream architecture:

### Phase 1: Knowledge Acquisition & Contextualization
* **Summary Agent (Internal Compression):** Extracts core claims, the proposed method, and reported evidence from the paper to avoid cognitive overload.
* **Literature Review & Expansion Agent:** Conducts iterative web searches to find foundational papers, SOTA benchmarks, and concurrent work up to a strict `cutoff_date`.
* **Historian Agent:** Synthesizes the retrieved literature into a chronological "Domain Narrative", allowing the system to understand the arc of progress.
* **Baseline Scout Agent:** Acts as an adversarial auditor, hunting for SOTA methods and datasets the authors explicitly *failed* to compare against.

### Phase 2: Active Verification (Q&A Engine)
* **Q&A Skeptic:** Generates probing questions regarding technical soundness and novelty based on the inputs from Phase 1.
* **Interrogation Log:** Self-answers and verifies claims against the external domain narrative, logging discrepancies as hard evidence.

### Phase 3: Synthesis
* **Review Generator:** Uses the verified interrogation log and specific venue guidelines (e.g., ICLR, NeurIPS) to draft the final review.

---

## 3. Architectural Philosophy & Agentic Design

This project avoids the pitfall of building a monolithic, rigid application. Instead, it relies on modular agentic design principles derived from the latest AI developer tools.

### 3.1. The "Single Manager Agent" Paradigm
We do not necessarily need to hardcode a completely new, isolated agent instance for every single role in the paper. Instead, **WE ALWAYS HAVE ONE Manager Agent**. 
* The Manager Agent acts as the orchestrator.
* Instead of becoming a bloated "swiss-army knife" with a massive, confused system prompt, the Manager Agent dynamically shifts its persona. 
* The distinction between the "Agents" (Historian vs. Scout vs. Skeptic) is achieved dynamically through:
    * **Tools:** Standardized external calls (handled by MCP).
    * **System Prompts:** Dynamically injected or swapped by activating specific **Skills**.
    * **User Prompts:** Controlled via step-by-step **Workflows** or **Commands**.

### 3.2. Subagent Task Delegation (When Supported)
While the Manager Agent *can* adopt personas, **if the native system or tool allows for delegating tasks to subagents, we will utilize them.** * Orchestrating and delegating tasks to specialized subagents ensures that each subagent operates within its own **isolated context window**, preventing cross-contamination of instructions or context overload.
* *Note on DeepAgents:* For our standalone web app built on DeepAgentsJS, we are certain the architecture supports subagents, so we will explicitly develop and utilize isolated subagents for the backend orchestration.

### 3.3. Strict MCP Scope: Dumb Tools Only
Model Context Protocol (MCP) servers must be strictly reserved for executing **atomic, stateless external functions**. **MCP is NEVER used for agentic logic, orchestration, or multi-step heuristics.**
* The framework does not define complex tools like `fetch_literature`. The cognitive task of determining *what* to search and *when* to stop searching belongs entirely to the Manager Agent/Subagent.
* The system utilizes standard, open-source MCP implementations:
    * **ArXiv MCP Server:** Exposes basic functions like `search_arxiv(query)`.
    * **Semantic Scholar MCP Server:** Exposes basic graph searches (users can optionally provide their own API keys).
    * **Microsoft MarkItDown MCP Server:** Used exclusively as a dumb parser to convert local PDF files into clean Markdown for the agent to read.

  ### 3.4. Drift Mitigation Strategy (Adapters)
  Even with per-tool folders, drift risk remains. We handle it with a strict source hierarchy:
  1. Canonical protocol content lives once (phase logic, templates, artifact schema).
  2. Tool adapters in `extensions/` are generated/synced from canonical content.
  3. Installers only copy already-synced tool folders into user projects.

  This keeps the "plain files" approach while still controlling cross-tool divergence.

---

## 4. Guardrails via Templates & State Files
To prevent prompt brittleness across different LLMs (Gemini, Claude, GPT-4o), we do not rely on the LLM to creatively format its output.
* **Template Driven Outputs:** The `.brain` directory contains a `templates/` folder. For every phase, the Workflow strictly instructs the agent to read the template and populate it (e.g., `.brain/templates/interrogation_log.template.md`). This guarantees cross-model compatibility.

---

## 5. The Component Matrix: How the Magic Happens

To deploy this across various IDEs and CLIs, we break the system down into universal components. Drawing inspiration from the `reviewer-os` repository structure, our implementation will consist of:

### A. Skills (Dynamic Personas)
Skills are modular markdown files injected into the LLM's context to change its behavior.
* Examples: `.agents/skills/historian/SKILL.md` or `.agents/skills/baseline-scout/SKILL.md`.
* These files contain the precise system instructions to make the Manager Agent act like a specific persona from the ScholarPeer paper.

### B. Commands & Workflows (User Prompts & Orchestration)
We define the ScholarPeer methodology as a deterministic sequence of steps. By using Slash Commands or Workflow files, we guide the Manager Agent through the pipeline.
* Step 0: Venue Setup (`0-venue-setup.md`)
* Step 1: Paper Intake (`1-paper-intake.md`)
* Step 3: Literature Search & Expansion (`3-literature-search.md`)
* Step 4: Technical Verification (`4-technical-verify.md`)
* Step 6: Synthesize Review (`6-synthesize.md`)

### C. MCP Configuration (Tool-Native)
Unlike ReviewerOS, this project includes MCP configuration artifacts so each installed tool can immediately expose required external resources/tools.

### D. Installers (Project Scaffolding)
Installer scripts copy selected tool assets from `extensions/` into target root directories (e.g., `.cursor`, `.claude`, `.gemini`, `.agent`/`.agents`, `.github`) and initialize `.brain/`.

---

## 6. The `.brain` State Management System
To manage the complex, multi-step flow of a peer review and ensure high agent observability, the framework relies on a `.brain` directory located at the **root of the repository/workspace**.

* **Initialization:** When the user installs the framework (via the install scripts), the `.brain` folder is scaffolded at the root.
* **Architecture of `.brain`:**
  * `/templates/`: Contains the rigid markdown/JSON templates for agent outputs.
  * `session.json`: A state-tracking file (inspired by `reviewer-os`). The workflows read and update this file to know exactly where the methodology left off, what the current progress is, and which subagent is currently active.
  * `/artifacts/`: Where the populated templates (e.g., `extracted_claims.json`, `domain_narrative.md`) are saved by the agents as they complete their isolated tasks.

---

## 7. Target Ecosystems & Native Integrations (Current Phase)
The repository uses an `extensions/` folder as the source of installable tool configurations.

### 7.1 Repository layout for adapters
Planned structure:

```
extensions/
├── .cursor/
├── .claude/
├── .gemini/
├── .agent/
├── .github/
└── _shared/
```

### 7.2 Tool-by-tool targets

#### Cursor
- Target install path: `.cursor/`
- Includes: commands/workflows, skills, rules, and MCP config (if supported in-project by Cursor format)

#### Claude Code
- Target install path: `.claude/`
- Includes: skills, commands, rules, hooks, and MCP-related config artifacts where applicable

#### Antigravity
- Target install path: `.agent/` (primary in this project decision)
- Compatibility: duplicate/sync to `.agents/` because current Antigravity docs and ecosystem usage still reference `.agents` with backward support for `.agent`
- Includes: rules, workflows, skills, and MCP bridge instructions

#### GitHub Copilot (VS Code)
- Target install path: `.github/` (+ `AGENTS.md` when needed)
- Includes: always-on instructions, prompts, optional agent/skill files, and MCP guidance files

#### Gemini CLI
- Target install path: `.gemini/`
- Includes: commands (TOML), skills, agents/subagents, settings/hooks, and MCP server configuration

### 7.3 Install behavior
Installers should:
1. Copy selected adapter folder to target project root.
2. Initialize `.brain/` and session state.
3. Add `.brain/` to `.gitignore` if missing.
4. Avoid overwriting user-local secrets unless explicitly confirmed.


---

## 8. The Standalone Web Application (DeepAgents)
For users who prefer a graphical interface over the terminal, we provide a complete web solution built on LangChain technologies.

### 7.1. Backend Engine: DeepAgentsJS
* **Framework:** We use **DeepAgents JS** to construct the LangGraph network.
* **Orchestration:** The graph nodes map exactly to the ScholarPeer pipeline (Summary -> Search -> History -> Scout -> Q&A -> Review).
* **Isolation:** As stated in the design principles, we will leverage DeepAgentsJS to create actual, distinct subagents for each phase to ensure maximum context isolation.

### 7.2. Frontend Interface: Custom Deep Agents UI
* **Base:** A customized fork of `langchain-ai/deep-agents-ui`.
* **The "Stepper" UX Enhancement:** To make the complex multi-agent workflow intuitive, we will add a progress-bar/stepper component to the UI.
* **User Visibility:** As the DeepAgentsJS backend transitions between subagents (e.g., from Historian to Scout), the frontend stepper updates dynamically. The user always knows exactly where they are in the methodology workflow and what the system is currently analyzing.

> Implementation path note: backend and frontend code will live in `src/backend` and `src/frontend` in later phases. Current phase remains focused on `extensions/` and installers.

---

## 9. MCP Support Strategy by Tool (Researched)

This section reflects current research and practical constraints.

### 9.1 Claude Code
- Supports MCP in native configuration and plugin packaging.
- Plugin structure explicitly supports `.mcp.json` at plugin root.
- Hooks can call MCP tools directly (`type: mcp_tool`).

### 9.2 Gemini CLI
- Supports MCP servers via extension manifest (`gemini-extension.json` with `mcpServers`).
- Supports per-agent MCP isolation via `mcpServers` in subagent frontmatter.
- Hooks and settings can coordinate with MCP-enabled workflows.

### 9.3 Antigravity
- MCP is supported via Antigravity MCP integrations.
- Custom MCP server config is managed in `~/.gemini/antigravity/mcp_config.json` (global editor config), not a project-local `.mcp.json` equivalent.
- Project installer must therefore write guidance and optional helper scripts rather than assume in-repo MCP authority.

### 9.4 GitHub Copilot / VS Code
- Current VS Code Copilot customization surface supports instructions, prompts, skills, custom agents, hooks, and MCP server integration via customization features.
- File-based project conventions are centered around `.github/*`, `AGENTS.md`, and instruction files; MCP server setup is managed through VS Code Copilot customization flows.

### 9.5 Cursor
- Cursor supports repository-level command/rule/skill patterns in practical usage (as seen in ReviewerOS integration style).
- MCP configuration file-path conventions require a dedicated verification pass before freezing final schema in this repo.
- Until verified, keep Cursor MCP integration behind a clearly marked experimental adapter.

---

## 10. Capability Report (What is supported by what)

### 10.1 Confirmed from research
- **Claude Code:** Skills, commands, hooks, subagents, plugin and standalone modes, MCP-aware workflows.
- **Gemini CLI:** Extensions, commands, skills, hooks, subagents, MCP servers, agent-local MCP isolation.
- **Antigravity:** Rules/workflows, skills, MCP integrations, custom MCP config via global `mcp_config.json`; `.agents` is default, `.agent` backward supported.
- **VS Code Copilot:** Always-on instructions, file-scoped instructions, prompt files, custom agents, agent skills, hooks, MCP server customization.

### 10.2 Confirmed from ReviewerOS repository patterns
- Multi-tool file-distribution via installers works well.
- Per-tool folders with copied commands/skills/rules are practical and maintainable.
- `.brain` session persistence pattern is robust and should be reused.

### 10.3 Open verification item
- Cursor MCP config exact format/path must be validated before hard-coding implementation.

---

## 11. Comprehensive Reference & Documentation Links

The following official documentation links serve as the architectural blueprint and constraints for our implementation. All development must align with the standards outlined in these resources:

**Claude Ecosystem:**
* Claude Plugins: [https://code.claude.com/docs/en/plugins](https://code.claude.com/docs/en/plugins)
* Claude Commands: [https://code.claude.com/docs/en/commands](https://code.claude.com/docs/en/commands)
* Claude Skills: [https://code.claude.com/docs/en/skills](https://code.claude.com/docs/en/skills)
* Claude Hooks Guide: [https://code.claude.com/docs/en/hooks-guide](https://code.claude.com/docs/en/hooks-guide)
* Claude Hooks Reference: [https://code.claude.com/docs/en/hooks](https://code.claude.com/docs/en/hooks)

**Cursor Ecosystem:**
* Cursor Plugins: [https://cursor.com/docs/plugins](https://cursor.com/docs/plugins)
* Cursor Slash Commands: [https://cursor.com/docs/cli/reference/slash-commands](https://cursor.com/docs/cli/reference/slash-commands)
* Cursor Hooks: [https://cursor.com/docs/hooks](https://cursor.com/docs/hooks)

**Gemini & Google Ecosystem:**
* Gemini CLI Extensions: [https://geminicli.com/docs/extensions/](https://geminicli.com/docs/extensions/)
* Gemini CLI Writing Extensions: [https://geminicli.com/docs/extensions/writing-extensions/](https://geminicli.com/docs/extensions/writing-extensions/)
* Gemini CLI Best Practices: [https://geminicli.com/docs/extensions/best-practices/](https://geminicli.com/docs/extensions/best-practices/)
* Gemini CLI Hooks: [https://geminicli.com/docs/hooks/](https://geminicli.com/docs/hooks/)
* Gemini Subagents Announcement: [https://developers.googleblog.com/subagents-have-arrived-in-gemini-cli/](https://developers.googleblog.com/subagents-have-arrived-in-gemini-cli/)
* Gemini CLI Subagents Docs: [https://github.com/google-gemini/gemini-cli/blob/main/docs/core/subagents.md](https://github.com/google-gemini/gemini-cli/blob/main/docs/core/subagents.md)
* Antigravity Rules & Workflows: [https://antigravity.google/docs/rules-workflows](https://antigravity.google/docs/rules-workflows)
* Antigravity Skills: [https://antigravity.google/docs/skills](https://antigravity.google/docs/skills)
* Antigravity MCP: [https://antigravity.google/docs/mcp](https://antigravity.google/docs/mcp)

**GitHub Copilot / VS Code Customization:**
* VS Code Copilot Customization Overview: [https://code.visualstudio.com/docs/copilot/copilot-customization](https://code.visualstudio.com/docs/copilot/copilot-customization)
* VS Code Custom Instructions: [https://code.visualstudio.com/docs/copilot/customization/custom-instructions](https://code.visualstudio.com/docs/copilot/customization/custom-instructions)
* VS Code Manage Context: [https://code.visualstudio.com/docs/copilot/chat/copilot-chat-context](https://code.visualstudio.com/docs/copilot/chat/copilot-chat-context)

**LangChain DeepAgents Ecosystem (Standalone Web App):**
* Deep Agents UI Repository: [https://github.com/langchain-ai/deep-agents-ui](https://github.com/langchain-ai/deep-agents-ui)
* DeepAgents JS Repository: [https://github.com/langchain-ai/deepagentsjs](https://github.com/langchain-ai/deepagentsjs)
* DeepAgents Python/General Overview: [https://docs.langchain.com/oss/python/deepagents/overview](https://docs.langchain.com/oss/python/deepagents/overview)
* DeepAgents Deployment Guide: [https://docs.langchain.com/oss/python/deepagents/deploy](https://docs.langchain.com/oss/python/deepagents/deploy)
