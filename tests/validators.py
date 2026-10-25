# Independent validators for all tasks.

from __future__ import annotations

from collections import deque
from itertools import combinations


class _UF:
    def __init__(self, n):
        self.p = list(range(n))

    def find(self, x):
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a, b):
        a, b = self.find(a), self.find(b)
        if a == b:
            return False
        self.p[a] = b
        return True


def _kahn(n, pairs):
    indeg = [0] * n
    adj = [[] for _ in range(n)]
    for u, v in pairs:
        adj[u].append(v)
        indeg[v] += 1
    q = deque(i for i in range(n) if indeg[i] == 0)
    order = []
    while q:
        u = q.popleft()
        order.append(u)
        for v in adj[u]:
            indeg[v] -= 1
            if indeg[v] == 0:
                q.append(v)
    return order, len(order) == n


def _tarjan_partition(n, edges):
    adj = [[] for _ in range(n)]
    for u, v in edges:
        adj[u].append(v)
    index = [-1] * n
    low = [0] * n
    on = [False] * n
    st = []
    comps = []
    counter = 0
    for s in range(n):
        if index[s] != -1:
            continue
        work = [(s, 0)]
        index[s] = low[s] = counter
        counter += 1
        st.append(s)
        on[s] = True
        while work:
            u, i = work[-1]
            if i < len(adj[u]):
                work[-1] = (u, i + 1)
                v = adj[u][i]
                if index[v] == -1:
                    index[v] = low[v] = counter
                    counter += 1
                    st.append(v)
                    on[v] = True
                    work.append((v, 0))
                elif on[v]:
                    low[u] = min(low[u], index[v])
            else:
                work.pop()
                if work:
                    p = work[-1][0]
                    low[p] = min(low[p], low[u])
                if low[u] == index[u]:
                    comp = []
                    while True:
                        x = st.pop()
                        on[x] = False
                        comp.append(x)
                        if x == u:
                            break
                    comps.append(frozenset(comp))
    return frozenset(comps)


def _labels_to_partition(labels):
    groups = {}
    for v, c in enumerate(labels):
        groups.setdefault(c, set()).add(v)
    return frozenset(frozenset(g) for g in groups.values())


def reference_msf_cost(n, edges):
    order = sorted(range(len(edges)), key=lambda i: edges[i][2])
    uf = _UF(n)
    cost = 0
    k = 0
    for i in order:
        u, v, w = edges[i]
        if u != v and uf.union(u, v):
            cost += w
            k += 1
    return cost, n - k


def brute_msf_cost(n, edges):
    _, comps = reference_msf_cost(n, edges)
    need = n - comps
    best = None
    for subset in combinations(range(len(edges)), need):
        uf = _UF(n)
        ok = True
        for i in subset:
            u, v, _ = edges[i]
            if not uf.union(u, v):
                ok = False
                break
        if ok:
            c = sum(edges[i][2] for i in subset)
            best = c if best is None or c < best else best
    return (best if best is not None else 0), comps


def check_dsu(req, res, expected=None):
    n, ops = req["n"], req["operations"]
    if n * len(ops) > 2_000_000:
        uf = _UF(n)
        size = [1] * n
        comps, largest = n, (1 if n else 0)
        exp = []
        for u, v in ops:
            a, b = uf.find(u), uf.find(v)
            if a != b:
                uf.p[a] = b
                size[b] += size[a]
                comps -= 1
                largest = max(largest, size[b])
            exp.append([comps, largest])
        if res.get("states") != exp:
            return False, "states mismatch (large reference)"
        return True, "ok"
    label = list(range(n))
    size = {i: 1 for i in range(n)}
    exp = []
    for u, v in ops:
        a, b = label[u], label[v]
        if a != b:
            for x in range(n):
                if label[x] == b:
                    label[x] = a
            size[a] += size.pop(b)
        exp.append([len(size), max(size.values()) if size else 0])
    if res.get("states") != exp:
        return False, f"states mismatch: expected {exp}, got {res.get('states')}"
    return True, "ok"


def check_msf(req, res, expected=None):
    n, edges = req["n"], req["edges"]
    ids = res.get("edge_ids")
    if not isinstance(ids, list) or len(set(ids)) != len(ids):
        return False, "edge_ids missing or duplicated"
    uf = _UF(n)
    total = 0
    for i in ids:
        if not (0 <= i < len(edges)):
            return False, f"edge id {i} out of range"
        u, v, w = edges[i]
        if not uf.union(u, v):
            return False, f"edge {i} closes a cycle (or is a loop)"
        total += w
    if total != res.get("cost"):
        return False, f"cost {res.get('cost')} != sum of chosen edges {total}"
    if len(edges) <= 14 and n <= 10:
        best, comps = brute_msf_cost(n, edges)
    else:
        best, comps = reference_msf_cost(n, edges)
    if res.get("components") != comps:
        return False, f"components {res.get('components')} != {comps}"
    if len(ids) != n - comps:
        return False, "not spanning: forest has the wrong number of edges"
    if total != best:
        return False, f"cost {total} is not minimum ({best})"
    return True, "ok"


def check_scc(req, res, expected=None):
    n, edges = req["n"], req["edges"]
    comp = res.get("component")
    if not isinstance(comp, list) or len(comp) != n:
        return False, "component has wrong length"
    if _labels_to_partition(comp) != _tarjan_partition(n, edges):
        return False, "partition differs from mutual reachability"
    exp_pairs = {(comp[u], comp[v]) for u, v in edges if comp[u] != comp[v]}
    got = res.get("condensation", [])
    got_set = {tuple(p) for p in got}
    if len(got_set) != len(got):
        return False, "condensation contains duplicate pairs"
    if got_set != exp_pairs:
        return False, f"condensation {sorted(got_set)} != {sorted(exp_pairs)}"
    return True, "ok"


def check_topo(req, res, expected=None):
    n, edges = req["n"], req["edges"]
    _, acyclic = _kahn(n, edges)
    if res.get("acyclic") != acyclic:
        return False, f"acyclic should be {acyclic}"
    order = res.get("order")
    if not acyclic:
        return (order == [], "order must be empty for a cyclic graph")
    if sorted(order) != list(range(n)):
        return False, "order is not a permutation of 0..n-1"
    pos = [0] * n
    for i, v in enumerate(order):
        pos[v] = i
    for u, v in edges:
        if pos[u] >= pos[v]:
            return False, f"edge {u}->{v} violates the order"
    return True, "ok"


def check_dag(req, res, expected=None):
    n, edges, s = req["n"], req["edges"], req["source"]
    order, acyclic = _kahn(n, [(u, v) for u, v, _ in edges])
    if res.get("acyclic") != acyclic:
        return False, f"acyclic should be {acyclic}"
    dist, par = res.get("distance"), res.get("parent_edge")
    if not acyclic:
        ok = dist == [] and par == []
        return ok, "ok" if ok else "cyclic graph must return two empty arrays"
    ref = [None] * n
    ref[s] = 0
    out = [[] for _ in range(n)]
    for i, (u, v, w) in enumerate(edges):
        out[u].append((v, w))
    for u in order:
        if ref[u] is None:
            continue
        for v, w in out[u]:
            if ref[v] is None or ref[u] + w < ref[v]:
                ref[v] = ref[u] + w
    if dist != ref:
        return False, "distance array is not the shortest distances"
    if len(par) != n:
        return False, "parent_edge has wrong length"
    for v in range(n):
        if v == s or dist[v] is None:
            if par[v] != -1:
                return False, f"parent_edge[{v}] must be -1"
            continue
        e = par[v]
        if not (0 <= e < len(edges)):
            return False, f"parent_edge[{v}]={e} out of range"
        u, t, w = edges[e]
        if t != v:
            return False, f"edge {e} does not end at {v}"
        if dist[u] is None or dist[u] + w != dist[v]:
            return False, f"edge {e} is not tight for {v}"
    return True, "ok"


VALIDATORS = {
    "dsu": check_dsu,
    "kruskal": check_msf,
    "prim": check_msf,
    "scc": check_scc,
    "topo": check_topo,
    "dag": check_dag,
}


def validate(req, res):
    if req["task"] == "ping":
        return (res.get("status") == "ready", "ping")
    return VALIDATORS[req["task"]](req, res)
