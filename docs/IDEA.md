# IDEA: ScholarPeer Open-Source Implementation (Master Seed Document)

## 1. Executive Summary & Core Vision
The objective of this project is to develop a robust, open-source, community-driven implementation of the **ScholarPeer** academic paper ("A Context-Aware Multi-Agent Framework for Automated Peer Review"). The goal is to translate this theoretical, multi-agent academic framework into functional, highly adaptable code.

**The Core Philosophy:** Eliminate vendor lock-in and UI dependency. 
Users must be able to leverage this methodology using their own API keys, local LLMs, or existing agentic environments without being forced into a specific subscription or proprietary web interface. The system must live where the developers and researchers already work.

**Primary Deliverables:**
1. **The Ecosystem Integrations:** A portable suite of Plugins, Extensions, Skills, Subagents, and Hooks that users can install directly into their preferred Terminal Code Agents or IDEs (Claude Code, Cursor, Gemini CLI, Antigravity, etc.).
2. **The Standalone Web Application:** A pre-built, easy-to-use web application powered by **DeepAgents JS** (backend) and a customized **Deep Agents UI** (frontend). This version will feature an intuitive, step-by-step progress UI, deployable via a simple configuration file.

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

---

## 4. Guardrails via Templates & State Files
To prevent prompt brittleness across different LLMs (Gemini, Claude, GPT-4o), we do not rely on the LLM to creatively format its output.
* **Template Driven Outputs:** The `.brain` directory contains a `templates/` folder. For every phase, the Workflow strictly instructs the agent to read the template and populate it (e.g., `.brain/templates/interrogation_log.template.md`). This guarantees cross-model compatibility.

---

## 4. The Component Matrix: How the Magic Happens

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

---

## 5. The `.brain` State Management System
To manage the complex, multi-step flow of a peer review and ensure high agent observability, the framework relies on a `.brain` directory located at the **root of the repository/workspace**.

* **Initialization:** When the user installs the framework (via the install scripts), the `.brain` folder is scaffolded at the root.
* **Architecture of `.brain`:**
  * `/templates/`: Contains the rigid markdown/JSON templates for agent outputs.
  * `session.json`: A state-tracking file (inspired by `reviewer-os`). The workflows read and update this file to know exactly where the methodology left off, what the current progress is, and which subagent is currently active.
  * `/artifacts/`: Where the populated templates (e.g., `extracted_claims.json`, `domain_narrative.md`) are saved by the agents as they complete their isolated tasks.

---

## 6. Target Ecosystems & Native Integrations
The repository will be structured as a Monorepo, providing localized configurations for all major terminal agents and IDEs. We will use install scripts (e.g., `install_claude.sh`, `install_cursor.sh`, `install_gemini.sh`) to seamlessly inject our methodology into the user's environment.

### 6.1. Claude & Claude Code
* **Mechanism:** Utilizing `.claude/` structure for Plugins, Commands, Skills, and Hooks.
* **Delegation:** Utilizing Claude Code's Subagent delegation for isolated context execution.

### 6.2. Cursor IDE
* **Mechanism:** Utilizing `.cursor/` structure for Plugins, Slash Commands (`.cursor/commands/`), and Rules (`.cursor/rules/reviewer-os.mdc`).

### 6.3. Gemini CLI & Antigravity
* **Mechanism:** Utilizing `.gemini/` Extensions (`.gemini/commands/` TOML files), Subagents, Rules, Workflows, Skills (`.gemini/skills/`), and Hooks.


---

## 7. The Standalone Web Application (DeepAgents)
For users who prefer a graphical interface over the terminal, we provide a complete web solution built on LangChain technologies.

### 7.1. Backend Engine: DeepAgentsJS
* **Framework:** We use **DeepAgents JS** to construct the LangGraph network.
* **Orchestration:** The graph nodes map exactly to the ScholarPeer pipeline (Summary -> Search -> History -> Scout -> Q&A -> Review).
* **Isolation:** As stated in the design principles, we will leverage DeepAgentsJS to create actual, distinct subagents for each phase to ensure maximum context isolation.

### 7.2. Frontend Interface: Custom Deep Agents UI
* **Base:** A customized fork of `langchain-ai/deep-agents-ui`.
* **The "Stepper" UX Enhancement:** To make the complex multi-agent workflow intuitive, we will add a progress-bar/stepper component to the UI.
* **User Visibility:** As the DeepAgentsJS backend transitions between subagents (e.g., from Historian to Scout), the frontend stepper updates dynamically. The user always knows exactly where they are in the methodology workflow and what the system is currently analyzing.

---

## 8. Comprehensive Reference & Documentation Links

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

**LangChain DeepAgents Ecosystem (Standalone Web App):**
* Deep Agents UI Repository: [https://github.com/langchain-ai/deep-agents-ui](https://github.com/langchain-ai/deep-agents-ui)
* DeepAgents JS Repository: [https://github.com/langchain-ai/deepagentsjs](https://github.com/langchain-ai/deepagentsjs)
* DeepAgents Python/General Overview: [https://docs.langchain.com/oss/python/deepagents/overview](https://docs.langchain.com/oss/python/deepagents/overview)
* DeepAgents Deployment Guide: [https://docs.langchain.com/oss/python/deepagents/deploy](https://docs.langchain.com/oss/python/deepagents/deploy)
