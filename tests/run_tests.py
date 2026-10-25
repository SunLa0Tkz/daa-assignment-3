# Usage: python tests/run_tests.py [--quick]

from __future__ import annotations

import json
import os
import random
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MAIN = os.path.join(ROOT, "src", "Python", "main.py")
sys.path.insert(0, HERE)

from validators import validate, check_msf, check_topo, check_dag  # noqa: E402

failures = 0


def report(ok: bool, name: str, msg: str = "") -> None:
    global failures
    if not ok:
        failures += 1
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + ("" if ok else f" -> {msg}"))


def run_batch(requests: list) -> list:
    data = "".join(json.dumps(r) + "\n" for r in requests)
    proc = subprocess.run([sys.executable, MAIN], input=data,
                          capture_output=True, text=True, check=True)
    lines = proc.stdout.splitlines()
    assert len(lines) == len(requests), "one output line per request expected"
    return [json.loads(x) for x in lines]


def section_a():
    print("A. Hand-written cases (sent twice in one process)")
    with open(os.path.join(HERE, "cases.json"), encoding="utf-8") as f:
        cases = json.load(f)
    reqs = [c["input"] for c in cases]
    outs = run_batch(reqs + reqs)
    first, second = outs[:len(cases)], outs[len(cases):]
    with open(os.path.join(HERE, "actual_outputs.jsonl"), "w",
              encoding="utf-8") as f:
        for c, out in zip(cases, first):
            f.write(json.dumps({"name": c["name"], "actual": out}) + "\n")
    for c, out, again in zip(cases, first, second):
        req, exp = c["input"], c["expected"]
        ok_exp, m1 = validate(req, exp)
        ok_out, m2 = validate(req, out)
        same = out == again
        exact = True
        if req["task"] in ("ping", "dsu") or out.get("acyclic") is False:
            exact = out == exp
        if req["task"] in ("kruskal", "prim"):
            exact = (out["cost"], out["components"]) == (exp["cost"],
                                                         exp["components"])
        report(ok_exp and ok_out and same and exact, c["name"],
               f"expected-valid={m1}; actual-valid={m2}; repeat={same}; "
               f"exact={exact}; got={out}")


def section_b():
    print("B. Alternative valid answers / invalid witnesses")
    tri = {"task": "kruskal", "n": 3, "edges": [[0, 1, 1], [1, 2, 1], [0, 2, 1]]}
    report(check_msf(tri, {"cost": 2, "edge_ids": [0, 2], "components": 1})[0],
           "MSF alternative [0,2] accepted")
    report(not check_msf(tri, {"cost": 3, "edge_ids": [0, 1, 2], "components": 1})[0],
           "MSF with a cycle rejected")
    heavy = {"task": "prim", "n": 3, "edges": [[0, 1, 1], [1, 2, 1], [0, 2, 9]]}
    report(not check_msf(heavy, {"cost": 10, "edge_ids": [0, 2], "components": 1})[0],
           "non-minimum spanning tree rejected")

    dia = {"task": "topo", "n": 4, "edges": [[0, 1], [0, 2], [1, 3], [2, 3]]}
    report(check_topo(dia, {"acyclic": True, "order": [0, 1, 2, 3]})[0],
           "topo alternative [0,1,2,3] accepted")
    report(not check_topo(dia, {"acyclic": True, "order": [1, 0, 2, 3]})[0],
           "topo order violating 0->1 rejected")

    from validators import check_scc
    s = {"task": "scc", "n": 5, "edges": [[0, 1], [1, 2], [2, 0], [2, 3], [3, 4]]}
    report(check_scc(s, {"component": [7, 7, 7, 3, 1],
                         "condensation": [[7, 3], [3, 1]]})[0],
           "SCC with different labels accepted")
    report(not check_scc(s, {"component": [0, 0, 1, 2, 3],
                             "condensation": [[0, 1], [1, 2], [2, 3]]})[0],
           "SCC wrong partition rejected")

    d = {"task": "dag", "n": 3, "source": 0,
         "edges": [[0, 1, 5], [0, 1, 5], [1, 2, 1], [0, 2, 6]]}
    report(check_dag(d, {"acyclic": True, "distance": [0, 5, 6],
                         "parent_edge": [-1, 1, 2]})[0],
           "DAG alternative witness [-1,1,2] accepted")
    report(not check_dag(d, {"acyclic": True, "distance": [0, 5, 6],
                             "parent_edge": [-1, 0, 1]})[0],
           "DAG invalid witness (edge 1 does not end at 2) rejected")
    report(not check_dag(d, {"acyclic": True, "distance": [0, 5, 7],
                             "parent_edge": [-1, 0, 2]})[0],
           "DAG non-shortest distance rejected")


def rand_graph(rng, n, m, weighted, wmin=-10, wmax=10):
    e = []
    for _ in range(m):
        u, v = rng.randrange(n), rng.randrange(n)
        e.append([u, v, rng.randint(wmin, wmax)] if weighted else [u, v])
    return e


def rand_dag(rng, n, m):
    perm = list(range(n))
    rng.shuffle(perm)
    e = []
    for _ in range(m):
        a, b = sorted(rng.sample(range(n), 2)) if n > 1 else (0, 0)
        if a == b:
            continue
        e.append([perm[a], perm[b], rng.randint(-10, 10)])
    return e


def section_c():
    print("C. Random small graphs vs independent references (seed 2026)")
    rng = random.Random(2026)
    reqs = []
    for _ in range(150):
        n = rng.randint(1, 9)
        m = rng.randint(0, 12)
        reqs.append({"task": "dsu", "n": n,
                     "operations": [e[:2] for e in rand_graph(rng, n, m, False)]})
        w = rand_graph(rng, n, m, True)
        reqs.append({"task": "kruskal", "n": n, "edges": w})
        reqs.append({"task": "prim", "n": n, "edges": w})
        g = rand_graph(rng, n, m, False)
        reqs.append({"task": "scc", "n": n, "edges": g})
        reqs.append({"task": "topo", "n": n, "edges": g})
        dagw = rand_dag(rng, n, m) if rng.random() < 0.7 else rand_graph(rng, n, m, True)
        reqs.append({"task": "dag", "n": n, "source": rng.randrange(n), "edges": dagw})
    outs = run_batch(reqs)
    by_task = {}
    for r, o in zip(reqs, outs):
        ok, msg = validate(r, o)
        t = by_task.setdefault(r["task"], [0, 0, ""])
        t[0] += 1
        if ok:
            t[1] += 1
        elif not t[2]:
            t[2] = f"{msg} | {r} | {o}"
    for task, (total, good, msg) in by_task.items():
        report(total == good, f"{task}: {good}/{total} random cases", msg)


def section_d():
    print("D. Full limits and deep graphs")
    N, M = 100_000, 250_000
    rng = random.Random(7)
    big_w = [[rng.randrange(N), rng.randrange(N),
              rng.randint(-10**9, 10**9)] for _ in range(M)]
    chain = [[i, i + 1] for i in range(N - 1)]
    chain_w = [[i, i + 1, 10**9] for i in range(N - 1)]
    ring = chain + [[N - 1, 0]]
    tests = [
        ("dsu 250k unions on n=100k", {"task": "dsu", "n": N, "operations":
            [[rng.randrange(N), rng.randrange(N)] for _ in range(M)]}),
        ("dsu worst chain of unions", {"task": "dsu", "n": N, "operations":
            [[i, i + 1] for i in range(N - 1)]}),
        ("kruskal n=100k m=250k |w|<=1e9", {"task": "kruskal", "n": N, "edges": big_w}),
        ("prim n=100k m=250k |w|<=1e9", {"task": "prim", "n": N, "edges": big_w}),
        ("prim 100k isolates (100k restarts)", {"task": "prim", "n": N, "edges": []}),
        ("scc deep chain n=100k", {"task": "scc", "n": N, "edges": chain}),
        ("scc ring n=100k (one SCC)", {"task": "scc", "n": N, "edges": ring}),
        ("topo deep chain n=100k", {"task": "topo", "n": N, "edges": chain}),
        ("topo ring n=100k (cycle at depth 1e5)", {"task": "topo", "n": N, "edges": ring}),
        ("dag deep chain, distance ~1e14 (64-bit)", {"task": "dag", "n": N,
            "source": 0, "edges": chain_w}),
        ("dag random DAG m=250k", {"task": "dag", "n": N, "source": 0,
            "edges": rand_dag(rng, N, M)}),
    ]
    for name, req in tests:
        t0 = time.perf_counter()
        out = run_batch([req])[0]
        dt = time.perf_counter() - t0
        ok, msg = validate(req, out)
        if name.startswith("scc ring"):
            ok = ok and len(set(out["component"])) == 1
        if name.startswith("dag deep"):
            ok = ok and out["distance"][-1] == (N - 1) * 10**9
        report(ok, f"{name}  ({dt:.2f}s incl. process start + JSON)", msg)


if __name__ == "__main__":
    section_a()
    section_b()
    section_c()
    if "--quick" not in sys.argv:
        section_d()
    print(f"\n{'ALL TESTS PASSED' if failures == 0 else f'{failures} FAILURE(S)'}")
    sys.exit(1 if failures else 0)
