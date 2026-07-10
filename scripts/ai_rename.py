#!/usr/bin/env python3
"""AI-assisted renaming of decompiled Hermes bytecode identifiers.

Consumes decompiled Hermes JS (hbc-decompiler output, or a raw bundle which is
auto-decompiled) and uses a local ollama model to produce meaningful, whole-
program-consistent names. See SKILL-common.md "AI-Assisted Renaming".
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
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


def _is_bracket_property_key(body: str, start: int, end: int) -> bool:
    """True if the quoted match at body[start:end] is bracket-notation member
    access (e.g. r0['token']) rather than a real string constant. These are JS
    property-name syntax, not "surviving string constants", and would otherwise
    give every function false positive signal for default targeting."""
    before = body[:start].rstrip()
    after = body[end:].lstrip()
    return before.endswith("[") and after.startswith("]")


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
        strings = [
            sm.group(2) for sm in STRING_RE.finditer(body)
            if not _is_bracket_property_key(body, sm.start(), sm.end())
        ]
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


def cache_key(func, model: str) -> str:
    """Generate a deterministic cache key for a function and model.

    Returns SHA256 hex digest (64 chars) of func.body + model + PROMPT_VERSION.
    """
    h = hashlib.sha256()
    h.update(func.body.encode())
    h.update(model.encode())
    h.update(PROMPT_VERSION.encode())
    return h.hexdigest()


def cache_load(cache_dir: str, key: str):
    """Load cached renames from a JSON file.

    Returns list of Rename objects if file exists and is valid, None otherwise.
    Treats corrupt/unreadable/schema-drifted entries as cache MISS (returns None).
    """
    path = os.path.join(cache_dir, key + ".json")
    if not os.path.exists(path):
        return None
    try:
        with open(path) as f:
            data = json.load(f)
        return [Rename(**r) for r in data]
    except (json.JSONDecodeError, TypeError, OSError, ValueError) as e:
        # Corrupt JSON, schema drift, file unreadable, or deserialization error
        sys.stderr.write(f"cache_load: corrupted cache entry {key}.json: {e}\n")
        return None


def cache_store(cache_dir: str, key: str, renames: list) -> None:
    """Store renames to a JSON cache file atomically.

    Creates cache_dir if needed. Writes to a temp file first, then atomically
    replaces the final path to avoid leaving half-written cache entries.
    """
    os.makedirs(cache_dir, exist_ok=True)
    path = os.path.join(cache_dir, key + ".json")

    # Write to a temp file in the same directory for atomic replace
    fd, tmp_path = tempfile.mkstemp(dir=cache_dir, prefix=key, suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump([r.__dict__ for r in renames], f)
        # Atomically replace the final path
        os.replace(tmp_path, path)
    except Exception:
        # Clean up temp file on error
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def _string_literal_spans(text: str) -> list:
    """Return (start, end) spans (inclusive of quotes) of string literals in text."""
    return [m.span() for m in STRING_RE.finditer(text)]


def _inside_any_span(pos: int, spans: list) -> bool:
    return any(start <= pos < end for start, end in spans)


def _apply_map(text: str, mapping: dict) -> str:
    """Apply a mapping of token renames in a single pass to prevent intra-scope collapse.

    Matches all keys simultaneously, so already-substituted text is never re-scanned.
    Sorts keys by length (longest first) to avoid r1 matching within r10.

    Substitution is purely textual, so without protection a rename could corrupt
    a surviving string constant that happens to contain the same token (e.g. a
    log message mentioning a register/function name). Candidate matches whose
    position falls inside a detected string-literal span (via STRING_RE) are
    left untouched.
    """
    if not mapping:
        return text
    keys = sorted(mapping, key=len, reverse=True)
    pat = re.compile(r"(?<![\w$])(" + "|".join(re.escape(k) for k in keys) + r")(?![\w$])")
    spans = _string_literal_spans(text)

    def repl(m):
        if _inside_any_span(m.start(), spans):
            return m.group(0)
        return mapping[m.group(1)]

    return pat.sub(repl, text)


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

    Note: this only disambiguates names it assigns from this batch of suggestions --
    it does not check suggested names against pre-existing identifiers already in the
    source that were not part of this run's renames, so those may still collide.
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


class DecompileError(RuntimeError):
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
    url = url.rstrip("/")  # Normalize URL to prevent double slashes
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
            # Validate that data is a dict; if not, treat as failed parse
            if not isinstance(data, dict):
                raise TypeError("Expected dict, got %s" % type(data).__name__)
            break
        except (json.JSONDecodeError, TypeError):
            if attempt == 1:
                # Give-up must be distinguishable from "the model legitimately
                # suggested nothing" (which returns []). Raising here (instead
                # of returning []) means run_rename's OllamaError handling
                # skips-and-logs the function WITHOUT caching the failure, so
                # a resumable re-run re-queries instead of replaying a
                # permanently poisoned empty cache entry.
                raise OllamaError(
                    "model returned unparseable JSON after retry for %s"
                    % (func.name or scope_id(func))
                )
    renames = []
    # Guard fn: ensure it is a dict before calling .get()
    fn = data.get("function") or {}
    if not isinstance(fn, dict):
        fn = {}
    if func.name and fn.get("name") and fn["name"] != func.name:
        renames.append(Rename("global", func.name, fn["name"],
                              float(fn.get("confidence", 0.0))))
    # Guard registers: ensure it is a dict before calling .items()
    regs = data.get("registers") or {}
    if not isinstance(regs, dict):
        regs = {}
    for reg, info in regs.items():
        # Guard info: skip entries where info is not a dict
        if not isinstance(info, dict):
            continue
        if reg in func.registers and info.get("name") and info["name"] != reg:
            renames.append(Rename(scope_id(func), reg, info["name"],
                                  float(info.get("confidence", 0.0))))
    return renames


def is_hermes_bundle(path: str) -> bool:
    # Rely only on the 4-byte Hermes bytecode magic. A looser substring check
    # (e.g. scanning for b"Hermes" in the header) false-positives on a
    # decompiled .js file that merely mentions "Hermes" in a comment/string,
    # misrouting it into the bundle decompile path instead of being read as text.
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
            raise DecompileError("hbc-decompiler failed: " + (proc.stderr or "")[:200])
        return proc.stdout
    with open(path, "r", errors="ignore") as f:
        return f.read()


def _by_name(funcs):
    return {f.name: f for f in funcs if f.name}


def select_functions(funcs, function=None, depth=1, id_range=None,
                     all_=False, limit=None):
    if function is not None:
        index = _by_name(funcs)
        # BFS out to `depth` hops. Mark nodes seen when *discovered* (enqueued),
        # not when processed -- marking on processing is off-by-one: it would
        # stop one hop short because the last frontier's callees get queued but
        # the loop ends before they're ever visited.
        seen = {function}
        frontier = [function]
        # depth is clamped to >= 1: there is no "zero-hop" mode, a call to
        # select_functions(function=...) always expands at least one hop.
        for _ in range(max(depth, 1)):
            nxt = []
            for nm in frontier:
                fn = index.get(nm)
                if not fn:
                    continue
                for c in fn.callees:
                    if c not in seen:
                        seen.add(c)
                        nxt.append(c)
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


def run_rename(js_text, source, model, url, temperature, selection_kwargs,
               cache_dir=None, query=query_ollama, progress=None):
    funcs = collect_functions(js_text)
    selected = select_functions(funcs, **selection_kwargs)
    if not selected:
        sys.stderr.write(
            "warning: selection matched 0 functions; writing an empty rename map\n"
        )
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
            if cache_dir:
                cache_store(cache_dir, key, rs)
        except OllamaError as e:
            sys.stderr.write("skip %s: %s\n" % (func.name or scope_id(func), e))
            rs = []
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

    try:
        js_text = load_decompiled(args.input)
    except DecompileError as e:
        sys.stderr.write("error: failed to decompile %s: %s\n" % (args.input, e))
        sys.exit(1)
    except OSError as e:
        sys.stderr.write("error: cannot read %s: %s\n" % (args.input, e))
        sys.exit(1)

    id_range = None
    if args.id_range:
        parts = args.id_range.split("-")
        if len(parts) != 2 or not all(p.strip().lstrip("-").isdigit() for p in parts):
            sys.stderr.write(
                "error: --range must be in the form <int>-<int>, e.g. 100-140 "
                "(got %r)\n" % args.id_range)
            sys.exit(2)
        lo, hi = parts
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
