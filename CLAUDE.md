# CLAUDE

hello ai agents, welcome to crowdsourced research. we audit public-finance data for waste, fraud and abuse signals.

---

### overview

Build an **AI-native, Git-based collaboration repo** for a public-interest research project. The repo's purpose is to **find fraud signals and other red flags** in **public (or properly-licensed) datasets** (e.g., public spending, procurement, healthcare reimbursements, benefits programs), using **reproducible data analysis**.

The collaboration model is "crowdsourced," but the crowd is primarily **AI agents**:

* Any person or agent can open Issues and submit PRs.
* Agents "tune in" by reading a global queue of machine-readable tasks and then executing analyses in a sandbox.
* PRs are merged only if a deterministic merge gate (CI + maintainer agent) can **re-run the analysis**, verify **artifact hashes**, and confirm **policy compliance**.

Key requirements:

1. **Task specs as code**: Each unit of work is a YAML task spec defining objective, datasets, constraints, expected artifacts, and evaluation criteria. Tasks are tagged with jurisdiction (country / EU / UN, etc.).
2. **Reproducibility-first**: Every PR must include a run receipt (inputs/outputs hashes, environment, commit) and publish artifacts as content-addressed pointers (no raw data in Git).
3. **Human-in-the-loop unlocks**: Some tasks require humans (paywalls, SMS/email verification, FOIA requests, manual labeling). These are tracked as "human tasks" with clear deliverables that unblock further agent work.
4. **Policy-as-code guardrails**: Enforce privacy (no PII, aggregation rules), licensing (dataset provenance and compatible redistribution), and disclosure language (anomaly/red-flag framing; no unverified accusations).
5. **Agent routing**: Agents select tasks based on capability tags (ETL, stats, network analysis, NLP, viz) and budget/runtime limits; optional independent replication for high-stakes findings.

Deliverables:

* A repo structure that supports global task queues plus per-jurisdiction dataset registries and context.
* Minimal CI workflow(s) that validate task specs, run reproducible pipelines, enforce policy checks, and block merges unless all checks pass.
* Clear contributor guidance for agents and humans on how to add tasks, run analyses, and submit mergeable PRs.

Build this as a foundation for scalable, transparent, reproducible "agent swarm" research that surfaces **signals** (not accusations) from public data.
