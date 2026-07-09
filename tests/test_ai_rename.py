import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
import ai_rename as air
import json as _json

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
    # Verify same register in different function survives untouched
    assert "r1" in out  # r1 is only renamed in fn#2, must exist in other functions


def test_apply_renames_no_intra_scope_collapse():
    """Regression test: ensure renames within a scope don't collapse into each other.

    If one rename's suggested name equals another's original name (near-swap),
    the second substitution must NOT affect text already produced by the first.
    This is a classic single-pass vs sequential substitution bug.
    """
    # Create a minimal function with two registers
    js = """function test() {
  var r1 = 0;
  var r2 = 1;
  return r1 + r2;
}"""
    funcs = [air.Function(0, "test", (0, len(js)), js, {"r1", "r2"}, [], [])]

    # Define renames where r1 -> r2, then r2 -> finalName
    # If applied sequentially, this would collapse: r1 becomes r2, then that r2 becomes finalName
    # With single-pass, r1 -> r2 and r2 -> finalName happen simultaneously, keeping them distinct
    renames = [
        air.Rename("fn#0", "r1", "r2", 0.8),        # first: r1 -> r2
        air.Rename("fn#0", "r2", "finalName", 0.9), # second: r2 -> finalName
    ]

    out = air.apply_renames(js, funcs, renames)

    # Both renames should be applied distinctly
    # The original r1 should become r2
    assert "var r2 = 0" in out, "Original r1 should be renamed to r2"
    # The original r2 should become finalName (not collapsed into r2)
    assert "var finalName = 1" in out, "Original r2 should be renamed to finalName"
    # Make sure we have both distinct names
    assert "return r2 + finalName" in out, "Both registers should appear with correct final names"


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


def test_suggest_names_survives_malformed_schema():
    """Regression test: suggest_names must not crash on schema-mismatched but valid JSON.

    Tests multiple malformed responses:
    1. Top-level is a string (not dict)
    2. function field is a string (not dict)
    3. registers field is a list (not dict)
    4. registers has non-dict values

    In each case, suggest_names should return a list (possibly empty) without raising.
    """
    funcs = air.collect_functions(FIX.read_text())
    fetch = funcs[1]  # fetchData, scope fn#1
    test_cases = [
        # Case 1: Top-level is a bare string
        (_json.dumps("not a dict"), "bare-string"),
        # Case 2: Top-level is a number
        (_json.dumps(123), "bare-number"),
        # Case 3: function field is a string (not dict)
        (_json.dumps({"function": "some_name", "registers": {}}), "function-is-string"),
        # Case 4: registers is a list (not dict)
        (_json.dumps({"function": {"name": "renamed", "confidence": 0.9}, "registers": []}),
         "registers-is-list"),
        # Case 5: registers has non-dict values
        (_json.dumps({"function": {"name": "renamed", "confidence": 0.9},
                      "registers": {"r0": "not_a_dict", "r1": {"name": "val", "confidence": 0.8}}}),
         "registers-mixed-values"),
        # Case 6: Valid response (control case, should work)
        (_json.dumps({"function": {"name": "validName", "confidence": 0.9},
                      "registers": {"r0": {"name": "token", "confidence": 0.8}}}),
         "valid-response"),
    ]

    for response_json, case_name in test_cases:
        call_count = [0]
        def fake_query(prompt, model, url, temperature, timeout=180):
            call_count[0] += 1
            # First attempt returns malformed, second returns empty dict (fallback on retry)
            if call_count[0] == 1:
                return response_json
            return _json.dumps({})

        # Should not raise, regardless of schema mismatch
        result = air.suggest_names(fetch, "m", "u", 0.15, query=fake_query)
        assert isinstance(result, list), f"Case {case_name}: should return list, got {type(result)}"

        # For the valid response case, we should get the expected rename
        if case_name == "valid-response":
            got = {(r.scope, r.original): (r.suggested, r.confidence) for r in result}
            assert ("global", "fetchData") in got, f"Case {case_name}: should have function rename"
            assert got[("global", "fetchData")][0] == "validName"
        # For case with valid function but malformed registers, we should still get function rename
        elif case_name == "registers-is-list":
            got = {(r.scope, r.original): (r.suggested, r.confidence) for r in result}
            assert ("global", "fetchData") in got, f"Case {case_name}: should have function rename even with bad registers"
            assert got[("global", "fetchData")][0] == "renamed"
