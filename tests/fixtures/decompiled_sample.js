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
