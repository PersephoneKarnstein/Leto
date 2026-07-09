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
