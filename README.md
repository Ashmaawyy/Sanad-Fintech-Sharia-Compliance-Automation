# Sanad

Open-source fintech Shariah-compliance AI reviewer.

Sanad is the product name. Al-Furqan is the underlying reasoning engine that powers source-grounded evaluation, evidence retrieval, and review workflows. Sanad is designed to help teams review fintech products, contracts, transaction structures, and policies through a disciplined Shariah workflow: extract facts, retrieve authoritative sources, apply rule logic, surface evidence, and require human oversight before a conclusion is treated as a compliance decision.

This repository is not a generic chatbot and it is not positioned as an autonomous Shariah certification engine. The product goal is a transparent review assistant for Islamic-finance compliance work: grounded analysis, auditability, and controlled human review.

---

## Product strategy

The current strategy is to combine:

- a general reasoning engine for source-grounded evaluation,
- a fintech review layer for contracts, products, and product facts,
- a rule/evidence model for Islamic-finance findings,
- a human review flow that keeps final approval with qualified Shariah governance.

The high-level principle is simple:

```text
The model extracts and explains.
The rule engine evaluates known product facts.
The KB retrieves source-backed evidence.
The reviewer validates the finding and decides the final compliance outcome.
```

A generated result is treated as a review artifact, not as a final Shariah certificate.

---

## What this repository contains

At the code level, the project currently combines the Al-Furqan reasoning engine with the Sanad product layer.

### Core engine

The underlying reasoning engine is Al-Furqan, and the product surface is Sanad. The core package under `src/al_furqan/` includes:

- `api/` — FastAPI app, routes, schemas, orchestration
- `auth/` — API keys, RBAC, rate limiting, security middleware
- `engine/` — axioms, gates, chains, symbolics, review workflow
- `kb/` — Elasticsearch-backed knowledge retrieval, indexing, and source integrations
- `fintech/` — product models, rule evaluation, evidence findings, review artifacts
- `store/` — verdict and feedback persistence
- `review/` — human review helpers and review workflows
- `tokenizer/` — Quran/tokenization utilities
- `providers/` — LLM/provider abstraction

### Fintech review layer

The repo includes a dedicated fintech model layer for reviewable product facts and compliance findings:

- `src/al_furqan/fintech/models.py` defines normalized product, contract, and transaction structures.
- `src/al_furqan/fintech/rules.py` contains rule-based evaluation of product structures.
- `src/al_furqan/fintech/evidence.py` defines evidence citations and compliance findings.
- `src/al_furqan/fintech/__init__.py` exports the review-facing model surface.

This is the clearest signal of the current product direction: Sanad is the product experience built on top of the Al-Furqan reasoning engine for Shariah-compliance analysis of fintech products.

---

## Architecture in practice

The codebase follows a layered model:

```text
API + auth + review surfaces
    -> orchestrates request handling and human review workflow
    -> calls engine + fintech rule logic + KB retrieval
    -> stores results and evidence

Engine layer
    -> axioms, gates, reasoning pipeline, symbolic verification
    -> outputs structured verdicts and explanations

Fintech layer
    -> product normalization, contract facts, rule checks
    -> evidence-grounded findings and review status

Knowledge layer
    -> Elasticsearch-backed Quran, hadith, fiqh, IIFA, and fatwa evidence
    -> retrieval context for grounded reasoning

Storage layer
    -> verdicts, feedback, audit records, and review metadata
```

This is intentionally different from a “chatbot-first” or “fully autonomous certification” design. The design preserves human accountability, explicit evidence chains, and separate rule evaluation from final review approval.

---

## Current runtime surfaces

| Surface | Typical entry point | Purpose |
| --- | --- | --- |
| CLI | `al-furqan` | Local reasoning entry point |
| REST API | `uvicorn al_furqan.api.app:app --reload` | Evaluation and review API |
| RaaS MCP | `python -m furqan_raas.mcp_server` | Reasoning-as-a-skill wrapper |
| Memory MCP | `python -m furqan_memory.mcp_server` | Local recall/memory server |

The API is organized around evaluation, review, and health endpoints under `/api/v1` in the core application. The exact routes evolve with the package, so the best source of truth is the API implementation rather than the older README tables.

---

## Knowledge and evidence model

The project stores and retrieves Islamic-finance evidence in Elasticsearch, with the runtime knowledge model centered on:

- Quran and hadith corpora
- fiqh and IIFA sources
- financial fatwa Q&A content
- verdicts and feedback records
- product and review evidence metadata

The repo also includes active training and data-processing artifacts under `training/`, `scripts/`, and `data-archive/` to support retrieval preparation and knowledge ingestion.

Notably, the repository is a research and platform codebase, not a polished SaaS product. The project remains in active engineering and product-shaping work, with the fintech review layer being the clearest current product direction.

---

## Repository layout

```text
al-furqan/
  src/al_furqan/            Core runtime and reasoning engine
  tests/                    Automated tests
  furqan-raas/              MCP reasoning server package
  furqan-memory/            Local memory MCP package
  docs/                     Current and legacy architecture docs
  plan/                     Product and technical plans
  scripts/                  Data and retrieval tooling
  training/                 Training and staging pipelines
  data-archive/             Archive and sourced data materials
  environment.yml
  pyproject.toml
  requirements.txt
  docker-compose.yml
  README.md
```

The exact artifact and archive layout can vary by branch or dataset snapshot; the implementation in `src/al_furqan/paths.py` and the `kb` ingestion modules should be treated as the most authoritative source when filesystem paths differ.

---

## Quick start

Install the package in editable mode:

```bash
pip install -e ".[dev]"
```

Run the test suite (excluding slower tests when needed):

```bash
pytest -m "not slow"
```

Run the API locally:

```bash
uvicorn al_furqan.api.app:app --reload
```

Start the supporting services used by the project:

```bash
docker compose up elasticsearch redis
```

For the local development environment:

```bash
conda env update --file environment.yml --name al-furqan
conda activate al-furqan
```

---

## Product principles

1. Grounded review first
   - every finding should point to evidence, source context, and reviewable reasoning.

2. Human governance remains central
   - the system may assist, structure, and highlight issues, but final Shariah compliance judgment remains human-governed.

3. Transparent evidence over opaque scoring
   - compliance findings should be explainable, traceable, and reviewable.

4. Rule logic is distinct from certification
   - a product may be logically consistent while still failing a Shariah rule or requiring a qualified reviewer decision.

5. Open-source reuse and extension
   - the project is designed to be usable as a reasoning foundation rather than a closed, single-purpose tool.

---

## Documentation and next steps

The code and docs in this repo are the starting point for a broader fintech compliance review workflow. The current strategy is best understood as:

- generic source-grounded reasoning engine,
- fintech review abstractions and rule layer,
- evidence-based Shariah compliance review assistance,
- human review governance and auditability.

For deeper architecture context, see:

- `docs/README.md`
- `docs/adr/ADR-001-fintech-contract-review-and-iifa-source-of-truth.md`
- `docs/active_docs/AL-FURQAN-ARCHITECTURE-v3.0.md`

This README reflects the current product direction of the codebase and intentionally avoids presenting the project as a finished autonomous certification system.

Operational note: `docker-compose.yml` includes an `es-seed` service, but the
current `Dockerfile.es-seed` still references a legacy `data/` directory and a
`scripts/seed_es.sh` file that is not present in this checkout. Use the explicit
commands above until that container path is reconciled.

---

## Documentation

Start with [docs/README.md](docs/README.md). The most useful active documents:

| Document | Role |
| --- | --- |
| [AL-FURQAN-ARCHITECTURE-v3.0](docs/active_docs/AL-FURQAN-ARCHITECTURE-v3.0.md) | Baseline architecture plus post-v3 update notes |
| [PROJECT-STATUS](docs/active_docs/PROJECT-STATUS.md) | Latest project status and decisions |
| [ELASTICSEARCH-MIGRATION](docs/active_docs/ELASTICSEARCH-MIGRATION.md) | ES migration rationale and schemas |
| [QURAN-TOKENIZER-v1.0](docs/active_docs/QURAN-TOKENIZER-v1.0.md) | Current tokenizer architecture |
| [RAG-IMPLEMENTATION-PLAN-v1.0](docs/active_docs/RAG-IMPLEMENTATION-PLAN-v1.0.md) | Engine-guided RAG design |
| [FURQAN-AXIOM-SECURITY-POLICY-v1.0](docs/active_docs/FURQAN-AXIOM-SECURITY-POLICY-v1.0.md) | Security model |
| [FURQAN-RAAS-DOCS](docs/active_docs/FURQAN-RAAS-DOCS.md) | Reasoning MCP docs |
| [FURQAN-MEMORY-DOCS](docs/active_docs/FURQAN-MEMORY-DOCS.md) | Local memory MCP docs |

The architecture document is still the baseline source of truth, but the live
code has post-v3 updates: ES is the core backend, the tokenizer uses
`TransitionToken` rather than a phonetic/tajweed layer, and training now includes
graph/history staging outputs.

---

## Architecture Rules

- Do not normalize, strip, transliterate, or stem Arabic text outside the
  tokenizer/analyzer paths that already define this behavior.
- Do not edit axiom definitions without updating the anchored SHA-256 integrity
  expectations.
- Route LLM calls through `providers/`; avoid raw provider HTTP calls in feature
  code.
- Keep layer boundaries: orchestration connects engine, KB, stores, and security.
- Treat `furqan-memory/` as local client memory, not core engine storage.
- Treat generated JSONL as rebuildable pipeline output; edit sources or
  extractors instead.

---

## Tech Stack

| Layer | Technology |
| --- | --- |
| Language | Python 3.10+ |
| API | FastAPI, uvicorn |
| Tasks/cache | Celery + Redis in dependencies; Redis in compose |
| LLM providers | Anthropic, DashScope/Qwen, Ollama, OpenAI-compatible |
| Formal verification | Z3 SMT solver |
| Runtime storage/search | Elasticsearch 8.x with custom Arabic analyzer |
| Local memory skill | SQLite + ChromaDB |
| Optional embeddings | sentence-transformers / MiniLM-style 384-dim vectors |
| Optional transcription | faster-whisper |
| Graph tooling | ES graph edges; Neo4j loaders for visualization/exploration |

---

## License / Classification

Apache-2.0
