# AI-Assisted Hermes Renaming Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a local-LLM renamer (`scripts/ai_rename.py`) that turns meaningless identifiers in decompiled Hermes JS into meaningful, whole-program-consistent names using ollama + qwen3-coder:30b.

**Architecture:** Decompile (or accept decompiled) Hermes JS → parse into a function table → per-function LLM name suggestions → reconcile into one global rename map → scope-aware token substitution → `renamed.js` + rename-map JSON. Pure stdlib (urllib for ollama HTTP); no Node, no new pip deps beyond what the skill already ships.

**Tech Stack:** Python 3 (stdlib only: `argparse`, `re`, `json`, `hashlib`, `urllib.request`, `subprocess`, `dataclasses`, `pathlib`), pytest for tests, `hbc-decompiler` (hermes-dec, already installed), ollama HTTP API.

## Global Constraints

- Python 3, standard-library only for runtime deps (no `requests`, no Node/Babel). Copied verbatim from spec: "no JS-AST rewriting, no Node dependency."
- Default model: `qwen3-coder:30b`. Default ollama URL: `localhost:11434`.
- ollama call uses `POST /api/generate`, `stream:false`, `format:"json"`, `options.temperature` default `0.15`.
- Rename-map schema (verbatim shared interface with Project B):
  ```json
  {"source": "<file>", "model": "<model>",
   "renames": [{"scope": "global|<functionScopeId>", "original": "<id>", "suggested": "<name>", "confidence": 0.0}]}
  ```
- `scope: "global"` = a function name (consistent everywhere it is called). `scope: "<functionScopeId>"` = a register/local inside that one function.
- **Spec correction from source inspection:** hermes-dec renders locals as `r\d+` (not `f123`); function *names* survive when present. Function scope id = `fn#<appearanceIndex>` (0-based order in the decompiled file). Schema shape is unchanged.
- Robustness: sequential LLM calls; per-function `try` so one failure never aborts the run; invalid model JSON → retry once then skip-and-log.
- Default output writes `renamed.js` + map; `--dry-run` writes only the map.
- Default targeting (no selector): only functions that have surviving string constants (highest signal).

---

### Task 1: Scaffold, fixture, and `collect_functions`

**Files:**
- Create: `scripts/ai_rename.py`
- Create: `tests/__init__.py` (empty)
- Create: `tests/test_ai_rename.py`
- Create: `tests/fixtures/decompiled_sample.js`

**Interfaces:**
- Produces: `@dataclass Function{index:int, name:str|None, span:tuple[int,int], body:str, registers:set[str], strings:list[str], callees:list[str]}` and `collect_functions(js_text:str) -> list[Function]`. `span` is `(start_char, end_char)` of the whole function block within `js_text`.

- [ ] **Step 1: Create the fixture** `tests/fixtures/decompiled_sample.js`

```javascript
// Decompiled by hermes-dec (realistic shape: named funcs + r\d+ registers)

function global(r0, r1) {
    r2 = "https://api.example.com/login"
    r3 = fetchData(r0, r2)
    return r3
}

function fetchData(r0, r1) {
    r2 = r0['token']
    r3 = r1 + "/v1/session"
    r4 = normalize(r3)
    return r4
}

function normalize(r0) {
    r1 = r0['length']
    r10 = r0
    return r10
}
```

- [ ] **Step 2: Write the failing test**

```python
# tests/test_ai_rename.py
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
import ai_rename as air

FIX = pathlib.Path(__file__).parent / "fixtures" / "decompiled_sample.js"

def test_collect_functions_basic():
    funcs = air.collect_functions(FIX.read_text())
    names = [f.name for f in funcs]
    assert names == ["global", "fetchData", "normalize"]
    assert [f.index for f in funcs] == [0, 1, 2]
    fetch = funcs[1]
    assert fetch.registers == {"r0", "r1", "r2", "r3", "r4"}
    assert "https://api.example.com/login" not in fetch.strings  # belongs to global
    assert "/v1/session" in fetch.strings
    assert "fetchData" in funcs[0].callees
    assert "normalize" in fetch.callees
    # r10 must be captured distinctly from r1 (word-boundary correctness)
    assert "r10" in funcs[2].registers and "r1" in funcs[2].registers
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd /Users/persephone/Leto && python -m pytest tests/test_ai_rename.py::test_collect_functions_basic -v`
Expected: FAIL with `ModuleNotFoundError` or `AttributeError: module 'ai_rename' has no attribute 'collect_functions'`.

- [ ] **Step 4: Write minimal implementation** in `scripts/ai_rename.py`

```python
#!/usr/bin/env python3
"""AI-assisted renaming of decompiled Hermes bytecode identifiers.

Consumes decompiled Hermes JS (hbc-decompiler output, or a raw bundle which is
auto-decompiled) and uses a local ollama model to produce meaningful, whole-
program-consistent names. See SKILL-common.md "AI-Assisted Renaming".
"""
import re
from dataclasses import dataclass, field

PROMPT_VERSION = "1"

# hermes-dec renders registers as r<N> (confirmed from source: '%r%d' % register).
REGISTER_RE = re.compile(r"\br\d+\b")
# Tolerant function header: optional name, then '(' ... ')' '{'. Validate against a
# real sample in Task 7 and widen if needed.
FUNC_HEADER_RE = re.compile(r"(?m)^\s*function\s+([A-Za-z_$][\w$]*)?\s*\([^)]*\)\s*\{")
STRING_RE = re.compile(r"""(['"])((?:\\.|(?!\1).)*)\1""")


@dataclass
class Function:
    index: int
    name: str | None
    span: tuple
    body: str
    registers: set = field(default_factory=set)
    strings: list = field(default_factory=list)
    callees: list = field(default_factory=list)


def _match_block(text: str, open_brace_pos: int) -> int:
    """Return index just past the matching '}' for the '{' at open_brace_pos."""
    depth = 0
    i = open_brace_pos
    n = len(text)
    while i < n:
        c = text[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    return n


def collect_functions(js_text: str) -> list:
    funcs = []
    all_names = []
    raw = []
    for idx, m in enumerate(FUNC_HEADER_RE.finditer(js_text)):
        brace = js_text.index("{", m.end() - 1)
        end = _match_block(js_text, brace)
        body = js_text[m.start():end]
        name = m.group(1)
        registers = set(REGISTER_RE.findall(body))
        strings = [g[1] for g in STRING_RE.findall(body)]
        raw.append((idx, name, (m.start(), end), body, registers, strings))
        if name:
            all_names.append(name)
    name_set = set(all_names)
    for idx, name, span, body, registers, strings in raw:
        callees = sorted({
            c for c in re.findall(r"([A-Za-z_$][\w$]*)\s*\(", body)
            if c in name_set and c != name
        })
        funcs.append(Function(idx, name, span, body, registers, strings, callees))
    return funcs
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd /Users/persephone/Leto && python -m pytest tests/test_ai_rename.py::test_collect_functions_basic -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
cd /Users/persephone/Leto
git add scripts/ai_rename.py tests/__init__.py tests/test_ai_rename.py tests/fixtures/decompiled_sample.js
git commit -m "feat: add Hermes decompiled-JS function parser (collect_functions)"
```

---

### Task 2: Scope-aware `apply_renames`

**Files:**
- Modify: `scripts/ai_rename.py`
- Test: `tests/test_ai_rename.py`

**Interfaces:**
- Consumes: `collect_functions`, `Function`.
- Produces: `@dataclass Rename{scope:str, original:str, suggested:str, confidence:float}` and `apply_renames(js_text:str, funcs:list[Function], renames:list[Rename]) -> str`. Global-scope renames rewrite a token everywhere; function-scope renames rewrite the token only inside that function's `span`.

- [ ] **Step 1: Write the failing test**

```python
def test_apply_renames_scoped_and_global():
    js = FIX.read_text()
    funcs = air.collect_functions(js)
    renames = [
        air.Rename("global", "fetchData", "fetchLoginSession", 0.9),
        air.Rename("fn#1", "r2", "authToken", 0.8),   # local to fetchData only
        air.Rename("fn#2", "r1", "strLength", 0.7),    # local to normalize
    ]
    out = air.apply_renames(js, funcs, renames)
    # global rename hits the definition AND the call site in `global`
    assert "function fetchLoginSession(" in out
    assert "r3 = fetchLoginSession(r0, r2)" in out
    # fetchData's r2 renamed, but `global` also has an r2 that must be untouched
    assert "authToken = r0['token']" in out
    assert 'r2 = "https://api.example.com/login"' in out  # global's r2 intact
    # normalize's r1 renamed but r10 left alone (word boundary)
    assert "strLength = r0['length']" in out
    assert "r10 = r0" in out
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/persephone/Leto && python -m pytest tests/test_ai_rename.py::test_apply_renames_scoped_and_global -v`
Expected: FAIL with `AttributeError: module 'ai_rename' has no attribute 'Rename'`.

- [ ] **Step 3: Write minimal implementation** (add to `scripts/ai_rename.py`)

```python
from dataclasses import dataclass as _dc

@_dc
class Rename:
    scope: str
    original: str
    suggested: str
    confidence: float


def scope_id(func) -> str:
    return "fn#%d" % func.index


def _sub_token(text: str, original: str, suggested: str) -> str:
    return re.sub(r"(?<![\w$])" + re.escape(original) + r"(?![\w$])", suggested, text)


def apply_renames(js_text: str, funcs: list, renames: list) -> str:
    by_scope = {}
    global_renames = []
    for r in renames:
        if r.scope == "global":
            global_renames.append(r)
        else:
            by_scope.setdefault(r.scope, []).append(r)
    # Apply per-function renames inside spans, working right-to-left so earlier
    # spans' offsets stay valid.
    pieces = js_text
    for func in sorted(funcs, key=lambda f: f.span[0], reverse=True):
        local = by_scope.get(scope_id(func))
        if not local:
            continue
        start, end = func.span
        block = pieces[start:end]
        for r in local:
            block = _sub_token(block, r.original, r.suggested)
        pieces = pieces[:start] + block + pieces[end:]
    # Global (function-name) renames apply across the whole file.
    for r in global_renames:
        pieces = _sub_token(pieces, r.original, r.suggested)
    return pieces
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/persephone/Leto && python -m pytest tests/test_ai_rename.py::test_apply_renames_scoped_and_global -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
cd /Users/persephone/Leto
git add scripts/ai_rename.py tests/test_ai_rename.py
git commit -m "feat: scope-aware token substitution for renames"
```

---

### Task 3: Reconcile collisions + rename-map schema

**Files:**
- Modify: `scripts/ai_rename.py`
- Test: `tests/test_ai_rename.py`

**Interfaces:**
- Consumes: `Rename`.
- Produces: `reconcile(renames:list[Rename]) -> list[Rename]` (deterministic disambiguation of duplicate suggested names within the same scope, and of two functions given the same global name) and `to_map_dict(source:str, model:str, renames:list[Rename]) -> dict` matching the Global-Constraints schema.

- [ ] **Step 1: Write the failing test**

```python
def test_reconcile_disambiguates_within_scope():
    renames = [
        air.Rename("global", "a", "handler", 0.9),
        air.Rename("global", "b", "handler", 0.8),   # collide -> handler_2
        air.Rename("fn#1", "r0", "value", 0.7),
        air.Rename("fn#1", "r1", "value", 0.6),        # collide -> value_2
        air.Rename("fn#2", "r0", "value", 0.7),        # different scope: OK, stays 'value'
    ]
    out = {(r.scope, r.original): r.suggested for r in air.reconcile(renames)}
    assert out[("global", "a")] == "handler"
    assert out[("global", "b")] == "handler_2"
    assert out[("fn#1", "r0")] == "value"
    assert out[("fn#1", "r1")] == "value_2"
    assert out[("fn#2", "r0")] == "value"

def test_to_map_dict_schema():
    d = air.to_map_dict("bundle.js", "qwen3-coder:30b",
                        [air.Rename("global", "fetchData", "login", 0.9)])
    assert d["source"] == "bundle.js"
    assert d["model"] == "qwen3-coder:30b"
    assert d["renames"] == [
        {"scope": "global", "original": "fetchData", "suggested": "login", "confidence": 0.9}
    ]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/persephone/Leto && python -m pytest tests/test_ai_rename.py -k "reconcile or map_dict" -v`
Expected: FAIL (`reconcile` / `to_map_dict` not defined).

- [ ] **Step 3: Write minimal implementation**

```python
def reconcile(renames: list) -> list:
    used = {}   # scope -> set of taken names
    out = []
    for r in sorted(renames, key=lambda x: (x.scope, -x.confidence, x.original)):
        taken = used.setdefault(r.scope, set())
        name = r.suggested
        if name in taken:
            i = 2
            while "%s_%d" % (name, i) in taken:
                i += 1
            name = "%s_%d" % (name, i)
        taken.add(name)
        out.append(Rename(r.scope, r.original, name, r.confidence))
    return out


def to_map_dict(source: str, model: str, renames: list) -> dict:
    return {
        "source": source,
        "model": model,
        "renames": [
            {"scope": r.scope, "original": r.original,
             "suggested": r.suggested, "confidence": r.confidence}
            for r in renames
        ],
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/persephone/Leto && python -m pytest tests/test_ai_rename.py -k "reconcile or map_dict" -v`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
cd /Users/persephone/Leto
git add scripts/ai_rename.py tests/test_ai_rename.py
git commit -m "feat: reconcile name collisions + rename-map schema"
```

---

### Task 4: ollama client + `suggest_names` (mocked)

**Files:**
- Modify: `scripts/ai_rename.py`
- Test: `tests/test_ai_rename.py`

**Interfaces:**
- Consumes: `Function`, `Rename`, `scope_id`.
- Produces:
  - `build_prompt(func:Function) -> str`
  - `query_ollama(prompt:str, model:str, url:str, temperature:float, timeout:int=180) -> str` (returns the model's raw `response` string; raises `OllamaError` on transport failure).
  - `suggest_names(func:Function, model:str, url:str, temperature:float, query=query_ollama) -> list[Rename]` — parses the model JSON, retries once on invalid JSON, returns `[]` on repeated failure. `query` is injectable for tests.
- Model JSON contract (in the prompt): `{"function": {"name": "...", "confidence": 0.0}, "registers": {"r0": {"name": "...", "confidence": 0.0}}}`.

- [ ] **Step 1: Write the failing test**

```python
import json as _json

def test_suggest_names_parses_model_json():
    funcs = air.collect_functions(FIX.read_text())
    fetch = funcs[1]  # fetchData, scope fn#1
    fake_response = _json.dumps({
        "function": {"name": "fetchLoginSession", "confidence": 0.9},
        "registers": {"r2": {"name": "authToken", "confidence": 0.8}},
    })
    calls = []
    def fake_query(prompt, model, url, temperature, timeout=180):
        calls.append(prompt)
        return fake_response
    out = air.suggest_names(fetch, "m", "u", 0.15, query=fake_query)
    got = {(r.scope, r.original): (r.suggested, r.confidence) for r in out}
    assert got[("global", "fetchData")] == ("fetchLoginSession", 0.9)
    assert got[("fn#1", "r2")] == ("authToken", 0.8)
    assert "fetchData" in calls[0]  # prompt includes the function body

def test_suggest_names_retries_then_gives_up():
    funcs = air.collect_functions(FIX.read_text())
    attempts = []
    def bad_query(prompt, model, url, temperature, timeout=180):
        attempts.append(1)
        return "not json{"
    out = air.suggest_names(funcs[2], "m", "u", 0.15, query=bad_query)
    assert out == []
    assert len(attempts) == 2  # one retry
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/persephone/Leto && python -m pytest tests/test_ai_rename.py -k suggest_names -v`
Expected: FAIL (`suggest_names` not defined).

- [ ] **Step 3: Write minimal implementation**

```python
import json
import urllib.request

class OllamaError(RuntimeError):
    pass


def build_prompt(func) -> str:
    hints = ", ".join(func.strings[:20]) or "(none)"
    return (
        "You are reverse-engineering decompiled Hermes (React Native) JavaScript.\n"
        "Suggest concise, meaningful camelCase names for the function and its r<N> "
        "registers, based on behaviour and string constants.\n"
        "Respond ONLY with JSON of the form:\n"
        '{"function": {"name": "...", "confidence": 0.0}, '
        '"registers": {"r0": {"name": "...", "confidence": 0.0}}}\n'
        "Use the ORIGINAL name if it is already meaningful (confidence 0).\n"
        "String constants in scope: " + hints + "\n\n"
        "Code:\n" + func.body + "\n"
    )


def query_ollama(prompt, model, url, temperature, timeout=180) -> str:
    endpoint = "http://%s/api/generate" % url if "://" not in url else url + "/api/generate"
    payload = json.dumps({
        "model": model, "prompt": prompt, "stream": False,
        "format": "json", "options": {"temperature": temperature},
    }).encode()
    req = urllib.request.Request(endpoint, data=payload,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode()).get("response", "")
    except Exception as e:  # transport/HTTP/JSON-envelope failure
        raise OllamaError(str(e))


def suggest_names(func, model, url, temperature, query=query_ollama) -> list:
    prompt = build_prompt(func)
    for attempt in range(2):
        raw = query(prompt, model, url, temperature)
        try:
            data = json.loads(raw)
            break
        except (json.JSONDecodeError, TypeError):
            if attempt == 1:
                return []
    renames = []
    fn = data.get("function") or {}
    if func.name and fn.get("name") and fn["name"] != func.name:
        renames.append(Rename("global", func.name, fn["name"],
                              float(fn.get("confidence", 0.0))))
    for reg, info in (data.get("registers") or {}).items():
        if reg in func.registers and info.get("name") and info["name"] != reg:
            renames.append(Rename(scope_id(func), reg, info["name"],
                                  float(info.get("confidence", 0.0))))
    return renames
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/persephone/Leto && python -m pytest tests/test_ai_rename.py -k suggest_names -v`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
cd /Users/persephone/Leto
git add scripts/ai_rename.py tests/test_ai_rename.py
git commit -m "feat: ollama client + per-function name suggestion with retry"
```

---

### Task 5: Input handling + `select_functions` targeting

**Files:**
- Modify: `scripts/ai_rename.py`
- Test: `tests/test_ai_rename.py`

**Interfaces:**
- Consumes: `Function`, `collect_functions`.
- Produces:
  - `is_hermes_bundle(path:str) -> bool` (magic-byte check, mirrors `analyze_bundle.read_hermes_header`).
  - `load_decompiled(path:str, run=subprocess.run) -> str` — if `.js`/text, read it; if a Hermes bundle, run `hbc-decompiler path -` and capture stdout. `run` injectable.
  - `select_functions(funcs:list[Function], function=None, depth=1, id_range=None, all_=False, limit=None) -> list[Function]`. Precedence: `function` (+callee expansion to `depth`) → `id_range` → `all_` → default(strings-only). `limit` truncates.

- [ ] **Step 1: Write the failing test**

```python
def test_select_default_is_strings_only():
    funcs = air.collect_functions(FIX.read_text())
    sel = air.select_functions(funcs)
    # global, fetchData have strings; normalize does not
    assert {f.name for f in sel} == {"global", "fetchData"}

def test_select_range_and_function_with_depth():
    funcs = air.collect_functions(FIX.read_text())
    assert [f.index for f in air.select_functions(funcs, id_range=(1, 2))] == [1, 2]
    # global calls fetchData calls normalize; depth=2 from index 0 pulls all three
    sel = air.select_functions(funcs, function="global", depth=2)
    assert {f.name for f in sel} == {"global", "fetchData", "normalize"}

def test_select_all_and_limit():
    funcs = air.collect_functions(FIX.read_text())
    assert len(air.select_functions(funcs, all_=True)) == 3
    assert len(air.select_functions(funcs, all_=True, limit=2)) == 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/persephone/Leto && python -m pytest tests/test_ai_rename.py -k select -v`
Expected: FAIL (`select_functions` not defined).

- [ ] **Step 3: Write minimal implementation**

```python
import struct
import subprocess

def is_hermes_bundle(path: str) -> bool:
    try:
        with open(path, "rb") as f:
            magic = f.read(4)
        return magic in (b"\xc6\x1f\xbc\x03", b"\x1f\xc6\x03\xbc")
    except OSError:
        return False


def load_decompiled(path: str, run=subprocess.run) -> str:
    if is_hermes_bundle(path):
        proc = run(["hbc-decompiler", path, "/dev/stdout"],
                   capture_output=True, text=True, timeout=1800)
        if proc.returncode != 0:
            raise OllamaError("hbc-decompiler failed: " + (proc.stderr or "")[:200])
        return proc.stdout
    with open(path, "r", errors="ignore") as f:
        return f.read()


def _by_name(funcs):
    return {f.name: f for f in funcs if f.name}


def select_functions(funcs, function=None, depth=1, id_range=None,
                     all_=False, limit=None):
    if function is not None:
        index = _by_name(funcs)
        seen, frontier = set(), [function]
        for _ in range(max(depth, 1)):
            nxt = []
            for nm in frontier:
                fn = index.get(nm)
                if fn and nm not in seen:
                    seen.add(nm)
                    nxt.extend(fn.callees)
            frontier = nxt
        chosen = [f for f in funcs if f.name in seen]
    elif id_range is not None:
        lo, hi = id_range
        chosen = [f for f in funcs if lo <= f.index <= hi]
    elif all_:
        chosen = list(funcs)
    else:
        chosen = [f for f in funcs if f.strings]
    return chosen[:limit] if limit else chosen
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/persephone/Leto && python -m pytest tests/test_ai_rename.py -k select -v`
Expected: PASS (3 passed).

- [ ] **Step 5: Commit**

```bash
cd /Users/persephone/Leto
git add scripts/ai_rename.py tests/test_ai_rename.py
git commit -m "feat: bundle auto-decompile + function targeting/selection"
```

---

### Task 6: Resumable cache

**Files:**
- Modify: `scripts/ai_rename.py`
- Test: `tests/test_ai_rename.py`

**Interfaces:**
- Consumes: `Function`, `Rename`.
- Produces:
  - `cache_key(func:Function, model:str) -> str` = `sha256(func.body + model + PROMPT_VERSION)`.
  - `cache_load(cache_dir:str, key:str) -> list[Rename]|None` and `cache_store(cache_dir:str, key:str, renames:list[Rename]) -> None` (JSON files named `<key>.json`).

- [ ] **Step 1: Write the failing test**

```python
def test_cache_roundtrip_and_key_sensitivity(tmp_path):
    funcs = air.collect_functions(FIX.read_text())
    f = funcs[1]
    k1 = air.cache_key(f, "qwen3-coder:30b")
    k2 = air.cache_key(f, "other-model")
    assert k1 != k2 and len(k1) == 64
    assert air.cache_load(str(tmp_path), k1) is None
    rs = [air.Rename("global", "fetchData", "login", 0.9)]
    air.cache_store(str(tmp_path), k1, rs)
    loaded = air.cache_load(str(tmp_path), k1)
    assert loaded == rs
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/persephone/Leto && python -m pytest tests/test_ai_rename.py -k cache -v`
Expected: FAIL (`cache_key` not defined).

- [ ] **Step 3: Write minimal implementation**

```python
import hashlib
import os

def cache_key(func, model: str) -> str:
    h = hashlib.sha256()
    h.update(func.body.encode())
    h.update(model.encode())
    h.update(PROMPT_VERSION.encode())
    return h.hexdigest()


def cache_load(cache_dir: str, key: str):
    path = os.path.join(cache_dir, key + ".json")
    if not os.path.exists(path):
        return None
    with open(path) as f:
        data = json.load(f)
    return [Rename(**r) for r in data]


def cache_store(cache_dir: str, key: str, renames: list) -> None:
    os.makedirs(cache_dir, exist_ok=True)
    path = os.path.join(cache_dir, key + ".json")
    with open(path, "w") as f:
        json.dump([r.__dict__ for r in renames], f)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/persephone/Leto && python -m pytest tests/test_ai_rename.py -k cache -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
cd /Users/persephone/Leto
git add scripts/ai_rename.py tests/test_ai_rename.py
git commit -m "feat: resumable per-function rename cache"
```

---

### Task 7: `run_rename` pipeline + CLI, end-to-end (mocked)

**Files:**
- Modify: `scripts/ai_rename.py`
- Test: `tests/test_ai_rename.py`

**Interfaces:**
- Consumes: everything above.
- Produces:
  - `run_rename(js_text, source, model, url, temperature, selection_kwargs, cache_dir=None, query=query_ollama, progress=None) -> tuple[dict, str]` returning `(map_dict, renamed_js)`. Loops selected functions sequentially, uses cache when `cache_dir` set, wraps each function in `try` (logs + skips on failure), reconciles, applies.
  - `main()` — argparse CLI wiring the flags from Global Constraints; writes `<out>/rename-map.json` always and `<out>/renamed.js` unless `--dry-run`.

- [ ] **Step 1: Write the failing test**

```python
def test_run_rename_end_to_end_mocked(tmp_path):
    js = FIX.read_text()
    responses = {
        "fetchData": _json.dumps({
            "function": {"name": "fetchLoginSession", "confidence": 0.9},
            "registers": {"r2": {"name": "authToken", "confidence": 0.8}}}),
        "global": _json.dumps({
            "function": {"name": "global", "confidence": 0.0},
            "registers": {"r2": {"name": "loginUrl", "confidence": 0.7}}}),
    }
    def fake_query(prompt, model, url, temperature, timeout=180):
        for name, resp in responses.items():
            if ("function " + name + "(") in prompt:
                return resp
        return _json.dumps({"function": {}, "registers": {}})
    map_dict, out_js = air.run_rename(
        js, "bundle.js", "m", "u", 0.15,
        selection_kwargs={},  # default: strings-only -> global + fetchData
        cache_dir=str(tmp_path / "cache"), query=fake_query)
    assert "function fetchLoginSession(" in out_js
    assert "r3 = fetchLoginSession(r0, r2)" in out_js       # call site updated
    assert "authToken = r0['token']" in out_js               # fetchData r2
    assert 'loginUrl = "https://api.example.com/login"' in out_js  # global r2
    pairs = {(r["scope"], r["original"]): r["suggested"] for r in map_dict["renames"]}
    assert pairs[("global", "fetchData")] == "fetchLoginSession"
    # second run must hit cache (no query calls)
    def boom(*a, **k):
        raise AssertionError("should be cached")
    air.run_rename(js, "bundle.js", "m", "u", 0.15, selection_kwargs={},
                   cache_dir=str(tmp_path / "cache"), query=boom)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/persephone/Leto && python -m pytest tests/test_ai_rename.py -k end_to_end -v`
Expected: FAIL (`run_rename` not defined).

- [ ] **Step 3: Write minimal implementation**

```python
import argparse
import sys

def run_rename(js_text, source, model, url, temperature, selection_kwargs,
               cache_dir=None, query=query_ollama, progress=None):
    funcs = collect_functions(js_text)
    selected = select_functions(funcs, **selection_kwargs)
    all_renames = []
    for i, func in enumerate(selected):
        if progress:
            progress(i + 1, len(selected), func.name or scope_id(func))
        key = cache_key(func, model) if cache_dir else None
        cached = cache_load(cache_dir, key) if cache_dir else None
        if cached is not None:
            all_renames.extend(cached)
            continue
        try:
            rs = suggest_names(func, model, url, temperature, query=query)
        except OllamaError as e:
            sys.stderr.write("skip %s: %s\n" % (func.name or scope_id(func), e))
            rs = []
        if cache_dir:
            cache_store(cache_dir, key, rs)
        all_renames.extend(rs)
    reconciled = reconcile(all_renames)
    out_js = apply_renames(js_text, funcs, reconciled)
    return to_map_dict(source, model, reconciled), out_js


def main():
    p = argparse.ArgumentParser(description="AI-assisted Hermes identifier renaming")
    p.add_argument("input", help="Decompiled .js OR a Hermes bundle (auto-decompiled)")
    p.add_argument("-o", "--output", default="rename_out", help="Output directory")
    p.add_argument("--model", default="qwen3-coder:30b")
    p.add_argument("--ollama-url", default="localhost:11434")
    p.add_argument("--temperature", type=float, default=0.15)
    p.add_argument("--function", help="Rename this function name + its callees")
    p.add_argument("--depth", type=int, default=1)
    p.add_argument("--range", dest="id_range", help="Function index range, e.g. 100-140")
    p.add_argument("--all", action="store_true", help="Rename every function")
    p.add_argument("--limit", type=int)
    p.add_argument("--dry-run", action="store_true", help="Write map only, no renamed.js")
    p.add_argument("--no-cache", action="store_true")
    args = p.parse_args()

    js_text = load_decompiled(args.input)
    id_range = None
    if args.id_range:
        lo, hi = args.id_range.split("-")
        id_range = (int(lo), int(hi))
    selection = {"function": args.function, "depth": args.depth,
                 "id_range": id_range, "all_": args.all, "limit": args.limit}
    os.makedirs(args.output, exist_ok=True)
    cache_dir = None if args.no_cache else os.path.join(args.output, "cache")

    def progress(n, total, label):
        sys.stderr.write("[%d/%d] %s\n" % (n, total, label))

    map_dict, out_js = run_rename(
        js_text, os.path.basename(args.input), args.model, args.ollama_url,
        args.temperature, selection, cache_dir=cache_dir, progress=progress)

    with open(os.path.join(args.output, "rename-map.json"), "w") as f:
        json.dump(map_dict, f, indent=2)
    if not args.dry_run:
        with open(os.path.join(args.output, "renamed.js"), "w") as f:
            f.write(out_js)
    sys.stderr.write("Wrote %d renames to %s\n" % (len(map_dict["renames"]), args.output))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the full test suite**

Run: `cd /Users/persephone/Leto && python -m pytest tests/test_ai_rename.py -v`
Expected: PASS (all tests).

- [ ] **Step 5: Validate the parser against real decompiler output (manual gate)**

Decompile any available Hermes bundle and confirm `collect_functions` finds functions and registers on real output; widen `FUNC_HEADER_RE` only if the real headers differ (e.g. generators/`async`). Record findings in the commit message. If no bundle is available, note that and rely on the fixture.

Run:
```bash
cd /Users/persephone/Leto
# if you have a bundle:
hbc-decompiler /path/to/index.android.bundle /tmp/dec.js 2>/dev/null && \
python -c "import sys; sys.path.insert(0,'scripts'); import ai_rename as a; \
fs=a.collect_functions(open('/tmp/dec.js').read()); \
print('functions:', len(fs), '| with-strings:', sum(1 for f in fs if f.strings))"
```
Expected: non-zero function count.

- [ ] **Step 6: Commit**

```bash
cd /Users/persephone/Leto
git add scripts/ai_rename.py tests/test_ai_rename.py
git commit -m "feat: end-to-end rename pipeline + CLI (ai_rename.py)"
```

---

### Task 8: Skill documentation + optional tool check

**Files:**
- Modify: `scripts/check_tools.py` (add `ollama` entry to `TOOLS`)
- Modify: `SKILL-common.md` (tool table, new section, script table)
- Modify: `SKILL-android.md` (cross-reference line)
- Modify: `SKILL-ios.md` (cross-reference line)
- Modify: `README.md` (one capability line)

**Interfaces:** none (docs/config only).

- [ ] **Step 1: Add ollama to `scripts/check_tools.py`**

Insert into the `TOOLS` dict (e.g. after the `r2ai` entry):

```python
    "ollama": {
        "check_cmd": ["ollama", "--version"],
        "install": {
            "macos": "brew install ollama  # then: ollama pull qwen3-coder:30b",
            "linux": "curl -fsSL https://ollama.com/install.sh | sh  # then: ollama pull qwen3-coder:30b",
        },
        "required_for": ["AI-assisted renaming (ai_rename.py)"],
        "optional": True,
    },
```

- [ ] **Step 2: Verify the tool check runs**

Run: `cd /Users/persephone/Leto && python scripts/check_tools.py | grep -i ollama`
Expected: a line `  ollama          [OK] (optional)` (ollama is installed on this machine).

- [ ] **Step 3: Update `SKILL-common.md`** — add to the Shared Tool Ecosystem table (after the `hbctool`/`frida` rows):

```markdown
| **ollama** | Local LLM runtime for AI renaming | `brew install ollama` | Pull a model: `ollama pull qwen3-coder:30b` |
```

Add a new section after "Enhanced Secret Scanning":

```markdown
## AI-Assisted Renaming

Decompiled Hermes identifiers are meaningless (`r0`, `r1`, anonymous functions). `ai_rename.py`
uses a **local** model (ollama + `qwen3-coder:30b`) to suggest meaningful, whole-program-consistent
names — the JSNice/Nice2Predict goal without a training corpus, and without spending paid context.

```bash
# Rename a whole bundle's high-signal functions (auto-decompiles if given a bundle)
python scripts/ai_rename.py index.android.bundle -o rename_out

# Target one function and its callees
python scripts/ai_rename.py decompiled.js --function fetchData --depth 2 -o rename_out

# Whole bundle (resumable via cache), or a function-index range
python scripts/ai_rename.py decompiled.js --all
python scripts/ai_rename.py decompiled.js --range 100-140

# Review the map before rewriting anything
python scripts/ai_rename.py decompiled.js --dry-run -o rename_out
```

Outputs `rename_out/rename-map.json` (always) and `rename_out/renamed.js` (unless `--dry-run`).
Requires a running ollama with the model pulled: `ollama pull qwen3-coder:30b`.
The rename-map format is shared with the Hermes2Predict trained-model project so backends are interchangeable.
```

Add to the Script Reference "Analysis Scripts" table:

```markdown
| `ai_rename.py` | AI-assisted identifier renaming (local LLM) | `--function`, `--range`, `--all`, `--depth`, `--limit`, `--model`, `--ollama-url`, `--dry-run`, `-o DIR` |
```

- [ ] **Step 4: Update `SKILL-android.md` and `SKILL-ios.md`** — in each, add a bullet under the Hermes/decompilation analysis references:

```markdown
- [AI-assisted renaming](SKILL-common.md#ai-assisted-renaming) — local-LLM identifier renaming for decompiled output
```

- [ ] **Step 5: Update `README.md`** — add one line to the features/capabilities list:

```markdown
- **AI-assisted renaming** — local LLM (ollama + qwen3-coder) renames decompiled Hermes identifiers, whole-program-consistent, no paid context
```

- [ ] **Step 6: Commit**

```bash
cd /Users/persephone/Leto
git add scripts/check_tools.py SKILL-common.md SKILL-android.md SKILL-ios.md README.md
git commit -m "docs: document AI-assisted renaming + optional ollama tool check"
```

---

## Self-Review

**Spec coverage:**
- Input (.js or auto-decompile bundle) → Task 5 (`load_decompiled`).
- Identifiers `r\d+` + function names → Tasks 1–2.
- Scope-aware substitution, no AST/Node → Task 2.
- Targeting (default strings-only / `--function`+depth / `--range` / `--all` / `--limit`) → Task 5.
- 3-pass pipeline (collect/suggest/reconcile+apply) → Tasks 1,4,3,7.
- Rename-map shared schema → Task 3 + Global Constraints.
- ollama HTTP `format:json`, config flags, temperature → Tasks 4,7.
- Caching, resumable → Task 6, exercised in Task 7 test.
- Robustness (per-function try, retry-once, clear ollama failure) → Tasks 4,7.
- `--dry-run` map-only → Task 7 `main`.
- Skill docs + optional ollama check → Task 8.
- Tests (collect, apply, reconcile, map roundtrip, pipeline mocked) → Tasks 1–7.

**Placeholder scan:** No TBD/TODO; every code step has runnable code; Task 7 Step 5 is a real manual verification command, not a placeholder.

**Type consistency:** `Rename(scope, original, suggested, confidence)`, `Function(index, name, span, body, registers, strings, callees)`, `scope_id() -> "fn#<index>"`, `query(prompt, model, url, temperature, timeout=180)` signature is consistent across `query_ollama`, `suggest_names`, `run_rename`, and all test doubles. `select_functions` kwargs (`function, depth, id_range, all_, limit`) match `run_rename`'s `selection_kwargs` and `main`'s wiring.

**Deviation from spec (flagged):** spec examples used `f123` function ids; source inspection shows hermes-dec emits `r\d+` locals and real function names, so scope ids are `fn#<index>` / `global`. Schema shape is unchanged.
