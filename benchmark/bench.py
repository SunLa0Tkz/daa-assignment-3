# Usage: python benchmark/bench.py

import os
import platform
import random
import statistics
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src", "Python"))
sys.path.insert(0, os.path.join(ROOT, "tests"))

from algorithms import kruskal, prim  # noqa: E402
from validators import check_msf  # noqa: E402

SEED = 12345
RUNS = 5
SIZES = [(1_000, 5_000), (10_000, 50_000), (100_000, 250_000)]


def make_graph(rng, n, m):
    edges = []
    for v in range(1, n):
        edges.append([rng.randrange(v), v, rng.randint(-10**9, 10**9)])
    while len(edges) < m:
        edges.append([rng.randrange(n), rng.randrange(n),
                      rng.randint(-10**9, 10**9)])
    rng.shuffle(edges)
    return edges


def time_it(fn, n, edges):
    t0 = time.perf_counter()
    res = fn({"n": n, "edges": edges})
    return time.perf_counter() - t0, res


def main():
    rng = random.Random(SEED)
    rows = []
    for n, m in SIZES:
        edges = make_graph(rng, n, m)
        result = {}
        for name, fn in (("Kruskal", kruskal), ("Prim", prim)):
            # verify first, also serves as warm-up
            ok, msg = check_msf({"n": n, "edges": edges}, fn({"n": n, "edges": edges}))
            assert ok, f"{name}: {msg}"
            times = []
            for _ in range(RUNS):
                t, res = time_it(fn, n, edges)
                times.append(t * 1000)
            result[name] = (times, res["cost"])
        assert result["Kruskal"][1] == result["Prim"][1], "costs differ!"
        for name in ("Kruskal", "Prim"):
            times, cost = result[name]
            rows.append((n, m, name, times, statistics.median(times), cost))
            print(f"n={n:>7} m={m:>7} {name:<8} runs(ms)="
                  + ", ".join(f"{t:.1f}" for t in times)
                  + f"  median={statistics.median(times):.1f}  cost={cost}")

    env = (f"Python {platform.python_version()} ({platform.python_implementation()}), "
           f"{platform.system()} {platform.release()}, {platform.machine()}, "
           f"{os.cpu_count()} logical CPUs")
    with open(os.path.join(ROOT, "benchmark", "results.md"), "w",
              encoding="utf-8") as f:
        f.write(f"Environment: {env}\n\nSeed {SEED}, 1 warm-up + {RUNS} timed runs, "
                "time.perf_counter around the algorithm call only. Both forests verified "
                "(acyclic, n-c edges, optimum cost) before timing.\n\n")
        f.write("| n | m | method | runs (ms) | median (ms) | MSF cost |\n")
        f.write("|---|---|---|---|---|---|\n")
        for n, m, name, times, med, cost in rows:
            f.write(f"| {n} | {m} | {name} | "
                    + ", ".join(f"{t:.1f}" for t in times)
                    + f" | **{med:.1f}** | {cost} |\n")
    print("\n" + env)


if __name__ == "__main__":
    main()
