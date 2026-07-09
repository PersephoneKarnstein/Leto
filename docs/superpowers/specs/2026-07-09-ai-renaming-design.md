# AI-Assisted Renaming for Decompiled Hermes Bytecode

**Date:** 2026-07-09
**Project:** A (skill addition). Project B (`~/Hermes2Predict`, trained statistical model) is a separate spec.
**Status:** Approved design, ready for implementation plan.

## Problem

Decompiling Hermes bytecode (via `hbc-decompiler` or `r2 pd:ha`) produces JavaScript whose
identifiers are meaningless: global function ids (`f123`), and per-function locals/params
(`r0`, `p1`, closure vars). This makes reverse engineering slow. We want JSNice/Nice2Predict-style
renaming — context-driven, whole-program-consistent, meaningful names — delivered by a local code
LLM (ollama + `qwen3-coder:30b`) so it burns no paid context and needs no training corpus.

### Why not r2ai

r2ai's `autoname`/`varnames` operate on radare2's native function database (Ghidra decompiler +
`afn`), not on the decompiled `.js` that Hermes analysts actually read. Renames there would not
propagate into that file. r2ai is also uninstalled, drags in a plugin stack with unproven Hermes
compatibility, and its docs never mention Hermes. Rejected.

### Why not adapt Nice2Predict (CRF) now

Mechanically possible (decompiled Hermes is JS-shaped), but: (1) the shipped model was trained on
hand-written minified web JS — wrong distribution for register-style decompiled Hermes; (2) making
it work needs retraining on an aligned corpus (decompiled ↔ original names) that does not exist —
Hermes strips local names at compile time; (3) Nice2Predict is effectively unmaintained. Building
that corpus and model is Project B (`~/Hermes2Predict`), designed separately. A pretrained code LLM
reaches ~80% of the goal today with no corpus.

## Scope

One new script, `scripts/ai_rename.py`, plus skill docs and an optional tool check. Targeted
renaming by default (not whole-bundle), local-only, resumable.

Out of scope: training any model (Project B), AST-based semantic rewriting, non-Hermes targets.

## Input

- A decompiled `.js` file (from `hbc-decompiler`, preferred, or `r2 pd:ha`).
- If given a raw Hermes bundle, auto-run `hbc-decompiler` first.

## Identifiers renamed

- Global function ids: `f<N>` (unique tokens → global scope).
- Per-function locals/params/closure vars: `r<N>`, `p<N>` etc. (unique within a function).

Because these are regular, unique token patterns, renames are applied with **scope-aware
word-boundary substitution** — no JS-AST rewriting, no Node dependency (decompiled output does not
always parse cleanly).

## Targeting

Default (no selector): rename only functions with surviving string/name hints (highest signal/payoff).

Selectors:
- `--function f123` — that function plus callees to `--depth N`.
- `--range 100-140` — a contiguous id range.
- `--all` — whole bundle, resumable via cache.

## Pipeline (3 passes, whole-program-consistent)

1. **Collect** — parse decompiled JS into a function table: `{id, code, string_constants, call_edges}`.
2. **Suggest** — per targeted function, send code + hints to qwen3-coder (ollama HTTP,
   `format: json`, low temperature) → proposed names for its function id + locals + params, each
   with a confidence.
3. **Reconcile & apply** — merge per-function suggestions into one global rename map; resolve
   collisions (duplicate suggested names → deterministic disambiguation suffix; a function id's
   name must be identical everywhere it is called). Apply to produce `renamed.js` + write the map.
   `--dry-run` writes only the map.

## Rename-map format (shared interface with Project B)

```json
{
  "source": "index.android.bundle",
  "model": "qwen3-coder:30b",
  "renames": [
    { "scope": "global", "original": "f123", "suggested": "parseAuthToken", "confidence": 0.82 },
    { "scope": "f123",   "original": "r0",   "suggested": "rawHeader",      "confidence": 0.7 }
  ]
}
```

- `scope: "global"` for function ids; `scope: "<functionId>"` for that function's locals/params.
- This is the contract B's trained model will also emit, so backends are interchangeable.

## Model integration, config, caching

- **Invocation:** `POST http://localhost:11434/api/generate`, `format: json`, temperature ~0.15.
- **Flags:** `--model` (default `qwen3-coder:30b`), `--ollama-url` (default `localhost:11434`),
  `--temperature`, `--depth`, `--limit`, `--dry-run`.
- **Caching:** per-function result keyed by `sha256(function_code + model + prompt_version)` in a
  cache dir; `--all` is resumable, re-runs near-instant.
- **Robustness:** sequential calls (single heavy local model); per-function `try` so one failure
  never kills the run; invalid model JSON → retry once, then skip-and-log. If ollama is down or the
  model is missing, exit with a clear, actionable message.

## Skill file integration

- New: `scripts/ai_rename.py`.
- `SKILL-common.md`: add `ollama` + `qwen3-coder` to the Shared Tool Ecosystem table; new
  "AI-Assisted Renaming" section (commands + workflow); add script to the Script Reference table.
- `SKILL-android.md` / `SKILL-ios.md`: one cross-reference line each to the new common section.
- `scripts/check_tools.py` / `scripts/check_tools_ios.py`: add `ollama` as an **optional** check
  (installed + model pulled).
- `README.md`: one line noting local-LLM renaming.

## Testing (TDD, pytest, new `tests/`)

Deterministic core is tested test-first; the LLM is mocked.

- `test_collect` — fixture JS → correct function table.
- `test_apply_renames` — `r0` renamed only within its function; `f123` globally; no substring/token
  collateral damage.
- `test_reconcile` — collision disambiguation + cross-scope consistency.
- `test_map_roundtrip` — rename-map JSON matches the schema.
- `test_pipeline_mocked` — full run with ollama mocked → valid map + renamed file.

Live integration run against a real bundle is documented in the SKILL, not automated.

## Success criteria

- Given a decompiled bundle and running ollama, produces a valid rename map + `renamed.js` where
  targeted functions and their locals have meaningful, consistent names.
- One malformed function response never aborts the run.
- `--all` is resumable via cache.
- All pytest tests pass; no Node dependency introduced.
</content>
</invoke>
