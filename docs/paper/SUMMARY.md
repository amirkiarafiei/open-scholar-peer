### 1. The Core Scientific Philosophy
Current LLM-based peer review systems suffer from the "parametric vacuum" problem: they evaluate papers purely based on their static, frozen training data. Because they lack an up-to-date, dynamic mental graph of prior art and concurrent work, they excel at surface-level summaries but fail to catch missing baselines or accurately assess true novelty. 

ScholarPeer solves this by shifting the paradigm from **passive text generation** to **active research and verification**. It treats the review process as an active investigation, actively fetching external context from the live web to ground its critiques in reality.

---

### 2. The Architecture Breakdown (The "What")
Based on the provided text and diagram, the authors implemented a highly orchestrated, dual-stream multi-agent pipeline. It is divided into three sequential phases:

#### Phase 1: Knowledge Acquisition & Contextualization
Before critiquing the paper, the system compresses both the *internal* contents of the paper and the *external* state of the research field.

* **Summary Agent (Internal Compression):** To avoid the "lost-in-the-middle" phenomenon and cognitive overload, this agent does not write a generic abstract. It extracts a structured representation consisting of three distinct components: the core claims, the proposed method, and the reported evidence. 
* **Literature Review & Expansion Agent (External Context):** This agent uses a live search engine to construct a reference frame. It works in two steps: first, it identifies the sub-domain and does an initial search; second, it looks for gaps and performs an "expansion search" specifically targeting recent pre-prints and concurrent work.
* **Sub-Domain Historian Agent (External Context):** Raw abstracts are not enough. This agent takes the retrieved literature and compresses it into a chronological "domain narrative". This mimics a senior researcher's mental model, allowing the system to understand the "arc of progress" and assess if a paper is a paradigm shift or an incremental tweak.
* **Baseline Scout Agent (External Context):** Acting as an "adversarial auditor," this agent independently searches for the current state-of-the-art methods and related benchmarks for the paper's specific task. It explicitly hunts for baselines and datasets that the authors *failed* to compare against.

#### Phase 2: Multi-Aspect Q&A Engine (Active Verification)
This phase acts as the system's "skeptic." Instead of passively generating a review, it actively interrogates the paper's claims.

* **Query & Answer Generation:** Fed by the structured summary, the domain narrative, and the missing baselines, this engine generates a set of probing questions targeting weaknesses in technical soundness and novelty. 
* **The Interrogation Log:** For each question, it self-answers, verifies claims against the retrieved external domain narrative, and explicitly logs any discrepancies between what the paper claims and what the external verification found.

#### Phase 3: Review Generator Agent (Synthesis)
* **Guidelines-Driven Output:** This final agent takes the structured paper summary and the verified facts from the interrogation log to synthesize the final report. Crucially, it is decoupled from the investigation phase and is conditioned on specific conference guidelines (e.g., ICLR, NeurIPS), formatting the raw findings into the expected tone and structure.

---

### 3. Technical Implementation Details (The "How")
To replicate their results, here are the specific technical parameters and tools the authors used for their implementation:

* **LLM Backbone:** The authors used **Gemini 3.0 Pro** via Google Cloud Vertex AI as the core reasoning engine for all agents in their primary configuration. 
* **Tooling:** A critical differentiator is that they did *not* use static API wrappers like Semantic Scholar. They utilized the native `Google Search` tool within the API to parse non-standard academic sources like blog posts, GitHub repos, and recent pre-prints.
* **Hyperparameters:** * **Temperature:** Set to `0.7` for all generation tasks to balance creativity with instruction adherence.
    * **Search Depth ($k$):** They found that performance gains saturate after `k=3` literature expansion rounds; beyond that, tangentially related papers begin to dilute the context window.
    * **Verification Depth ($N_{QA}$):** They generated exactly `10` probing Q&A pairs, which maximized performance while containing computational costs.
* **Computational Cost:** The architecture requires approximately `20` LLM inference calls per paper review (a fixed overhead of roughly 7 calls for the core agents, plus the variable costs of the 3 search rounds and 10 Q&A pairs)
