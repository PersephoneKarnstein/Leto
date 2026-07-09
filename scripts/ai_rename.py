#!/usr/bin/env python3
"""AI-assisted renaming of decompiled Hermes bytecode identifiers.

Consumes decompiled Hermes JS (hbc-decompiler output, or a raw bundle which is
auto-decompiled) and uses a local ollama model to produce meaningful, whole-
program-consistent names. See SKILL-common.md "AI-Assisted Renaming".
"""
import json
import re
import urllib.request
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


@dataclass
class Rename:
    scope: str
    original: str
    suggested: str
    confidence: float


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


def scope_id(func) -> str:
    return "fn#%d" % func.index


def _apply_map(text: str, mapping: dict) -> str:
    """Apply a mapping of token renames in a single pass to prevent intra-scope collapse.

    Matches all keys simultaneously, so already-substituted text is never re-scanned.
    Sorts keys by length (longest first) to avoid r1 matching within r10.
    """
    if not mapping:
        return text
    keys = sorted(mapping, key=len, reverse=True)
    pat = re.compile(r"(?<![\w$])(" + "|".join(re.escape(k) for k in keys) + r")(?![\w$])")
    return pat.sub(lambda m: mapping[m.group(1)], text)


def apply_renames(js_text: str, funcs: list, renames: list) -> str:
    """Apply Rename objects to js_text.

    Assumes function spans in funcs are non-overlapping and non-nested (true for
    Hermes-decompiled output, which hoists closures to disjoint top-level functions).
    """
    by_scope = {}
    global_renames = []
    for r in renames:
        if r.scope == "global":
            global_renames.append(r)
        else:
            by_scope.setdefault(r.scope, []).append(r)
    # Apply per-function renames inside spans, working right-to-left so earlier
    # spans' offsets stay valid. Use single-pass substitution per scope to prevent
    # one rename's suggested name from being matched by another's original.
    pieces = js_text
    for func in sorted(funcs, key=lambda f: f.span[0], reverse=True):
        local = by_scope.get(scope_id(func))
        if not local:
            continue
        start, end = func.span
        block = pieces[start:end]
        mapping = {r.original: r.suggested for r in local}
        block = _apply_map(block, mapping)
        pieces = pieces[:start] + block + pieces[end:]
    # Global (function-name) renames apply across the whole file, also in one pass.
    global_mapping = {r.original: r.suggested for r in global_renames}
    pieces = _apply_map(pieces, global_mapping)
    return pieces


def reconcile(renames: list) -> list:
    """Reconcile name collisions within each scope.

    Deterministically disambiguates duplicate suggested names within the same scope
    by appending _2, _3, etc to lower-confidence duplicates. Processes renames sorted
    by (scope, -confidence, original) to ensure deterministic ordering.
    """
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
    """Convert renames to the rename-map JSON schema dict.

    Schema: {"source": "<file>", "model": "<model>",
             "renames": [{"scope": "...", "original": "...", "suggested": "...", "confidence": 0.0}]}
    """
    return {
        "source": source,
        "model": model,
        "renames": [
            {"scope": r.scope, "original": r.original,
             "suggested": r.suggested, "confidence": r.confidence}
            for r in renames
        ],
    }


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
