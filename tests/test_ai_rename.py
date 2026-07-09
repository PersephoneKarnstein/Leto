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
