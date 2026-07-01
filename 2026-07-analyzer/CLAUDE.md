# CLAUDE.md — 日本語アナライザー比較ブログ（2026 続編）

This project produces a Japanese-language follow-up blog post and a runnable experiment
comparing Japanese morphological analyzers for Elasticsearch search.

## What this project is

- A "one year later" sequel to the 2025 post
  「日本語アナライザーの比較（Kuromoji / Sudachi / MeCab / LLM の性能検証）」.
- Audience: Japanese-speaking Elasticsearch engineers (not necessarily advanced).
- Goal: how Japanese search changed in a year, which analyzers are usable in Elasticsearch
  now, which got upgraded, and which analyzer fits which search task.
- Framing: NOT a strict same-condition year-over-year comparison.
  It is an IMPROVED 2026 approach, and every refinement vs 2025 is declared. See `METHODOLOGY.md`.

## Work location rules

- Build everything inside this directory (`/Users/samaneharzpeima/job/analyzer`). Keep it self-contained.
- Do NOT read from or write to `/Users/samaneharzpeima/job/elastic-blogs`. It is off-limits.
- Write Docker / compose / .env from standard patterns, not by copying other repos.

## Writing conventions

- Blog text and docs are in Japanese. Use simple, clear Japanese (the reader is learning).
- Keep Markdown lines short — roughly one sentence per line, break after 。
  (The user's file-write preview truncates long lines.)
- Explain basic concepts; avoid unexplained jargon. Prefer clarity over completeness.

## Technical accuracy rules (do not break these)

- Kuromoji = OFFICIAL Elastic Japanese analysis plugin (`analysis-kuromoji`; install per node + restart
  on Self-Managed). Sudachi = EXTERNAL plugin (Works Applications `elasticsearch-sudachi`).
  Never present them as equally official.
- Environments differ:
  - Serverless: core analysis plugins are bundled (Kuromoji usable), but external-plugin upload and
    custom dictionaries are NOT supported.
  - Self-Managed (and compatible Hosted): external plugins like Sudachi can be installed.
  - So Sudachi experiments are Self-Managed / Hosted only.
- Do not invent a "Kuromoji search analyzer". The `kuromoji` analyzer is a chain
  (CJKWidthCharFilter, kuromoji_tokenizer, kuromoji_baseform, kuromoji_part_of_speech, ja_stop,
  kuromoji_stemmer, lowercase). `mode: search` is a `kuromoji_tokenizer` SETTING, not an analyzer name.
  search mode decomposes compounds, e.g. 関西国際空港 → 関西 / 関西国際空港 / 国際 / 空港.
- Normalize NFKC once in Python (`unicodedata.normalize("NFKC", text)`) up front, then feed the SAME
  input to every analyzer. Mention `icu_normalizer` as the in-ES alternative for real deployments.
- MeCab / Janome / Lindera are not treated as official ES plugins; they are used via Python
  pre-tokenization. Do not claim they "do not exist" as plugins.
- LLM is a REFERENCE category, not a head-to-head analyzer. The tokenizer itself is deterministic;
  only LLM generation (keyword extraction / segmentation prompts) is non-deterministic.
  Record model name, prompt, temperature.
- Compare more than token similarity: include real search-query expected-hit tests
  (空港, 関西空港, NSAIDs, 300mg, アセトアミノフェン). Findability matters more than "pretty" tokens.
- Record full version metadata for reproducibility (ES version, `_cat/plugins`, analyzer settings,
  plugin/dictionary/library versions, Python version, input-text hash, LLM model/prompt/temperature, run date).

## Analyzer lineup

- In Elasticsearch: Kuromoji (standard + `mode: search`), Sudachi A / B / C.
- Python pre-tokenized (reference): MeCab, Janome, Lindera.
- LLM reference category: gpt-oss-120b (via EIS ES|QL COMPLETION), GPT-5.5, Claude.

## Environment

- Local Self-Managed Elasticsearch in Docker. Use v9.4.1 (not 9.4.2): the Sudachi plugin 3.6.0
  ships a 9.4.1 asset but no 9.4.2 asset, and the asset must match the ES patch version exactly.
- Cloud Connect + EIS available: ES|QL COMPLETION (gpt-oss-120b), Jina embeddings, Jina reranker.

## Deliverable layout (planned)

- `METHODOLOGY.md` — methodology + declared refinements vs 2025.
- `BLOG.md` — the Japanese blog prose draft (links back to the 2025 post).
- `README.md` — companion-repo overview (how to run).
- `data/` — test texts + their README.
- `Dockerfile-es01`, `docker-compose.yml`, `.env.sample`, `requirements.txt` — local ES + run setup.
- `es_scripts/` — Dev Tools requests (index creation, `_analyze`, search tests, version capture).
- `analyzer_compare/` — Python: tokenization, cleaning, comparison, LLM reference, results.
- `results/` — generated outputs (token lists, tables, version metadata).
