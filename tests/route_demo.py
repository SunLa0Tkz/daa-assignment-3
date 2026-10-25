# Usage: python tests/route_demo.py

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "src", "Python"))

from algorithms import dag, reconstruct_route, route_edge_ids  # noqa: E402

failures = 0


def show(label, source, target, parent, edges, dist):
    global failures
    route = reconstruct_route(source, target, parent, edges)
    ids = route_edge_ids(source, target, parent, edges)
    if route is None:
        ok = dist[target] is None and ids is None
        print(f"{label:<22} route=None edge_ids=None  check={'OK' if ok else 'FAIL'}")
    else:
        direction = all(edges[e][0] == route[k] and edges[e][1] == route[k + 1]
                        for k, e in enumerate(ids))
        total = sum(edges[e][2] for e in ids)
        ok = direction and route[0] == source and route[-1] == target \
            and total == dist[target]
        print(f"{label:<22} route={route} edge_ids={ids} weight={total} "
              f"distance={dist[target]}  check={'OK' if ok else 'FAIL'}")
    failures += not ok


edges1 = [[0, 1, 3], [0, 2, 8], [1, 2, -7], [2, 3, 4]]
r1 = dag({"n": 5, "source": 0, "edges": edges1})
print("graph 1:", r1)
show("reachable target 3", 0, 3, r1["parent_edge"], edges1, r1["distance"])
show("target = source 0", 0, 0, r1["parent_edge"], edges1, r1["distance"])
show("unreachable target 4", 0, 4, r1["parent_edge"], edges1, r1["distance"])

edges2 = [[0, 1, 5], [0, 1, 5], [1, 2, 1], [0, 2, 6]]
r2 = dag({"n": 3, "source": 0, "edges": edges2})
print("graph 2:", r2)
show("parallel target 1", 0, 1, r2["parent_edge"], edges2, r2["distance"])
show("tied target 2", 0, 2, r2["parent_edge"], edges2, r2["distance"])
show("alt witness, target 2", 0, 2, [-1, 1, 2], edges2, r2["distance"])

print("ALL ROUTE CHECKS OK" if failures == 0 else f"{failures} FAILED")
sys.exit(1 if failures else 0)
