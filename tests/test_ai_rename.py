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
