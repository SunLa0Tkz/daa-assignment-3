import heapq


class DSU:
    def __init__(self, n):
        self.parent = list(range(n))
        self.size = [1] * n
        self.components = n
        self.largest = 1 if n > 0 else 0

    def find(self, x):
        parent = self.parent
        root = x
        while parent[root] != root:
            root = parent[root]
        # path compression
        while parent[x] != root:
            nxt = parent[x]
            parent[x] = root
            x = nxt
        return root

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False
        # union by size
        if self.size[ra] < self.size[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        self.size[ra] += self.size[rb]
        self.components -= 1
        if self.size[ra] > self.largest:
            self.largest = self.size[ra]
        return True


def dsu(request):
    n = request["n"]
    operations = request["operations"]
    d = DSU(n)
    states = []
    for u, v in operations:
        d.union(u, v)
        states.append([d.components, d.largest])
    return {"states": states}


def kruskal(request):
    n = request["n"]
    edges = request["edges"]
    order = sorted(range(len(edges)), key=lambda i: (edges[i][2], i))
    d = DSU(n)
    cost = 0
    chosen = []
    for i in order:
        u, v, w = edges[i]
        if u == v:
            continue
        if d.find(u) != d.find(v):
            d.union(u, v)
            cost += w
            chosen.append(i)
            if len(chosen) == n - 1:
                break
    chosen.sort()
    return {"cost": cost, "edge_ids": chosen, "components": n - len(chosen)}


def prim(request):
    n = request["n"]
    edges = request["edges"]
    adj = [[] for _ in range(n)]
    for i, (u, v, w) in enumerate(edges):
        if u == v:
            continue
        adj[u].append((w, i, v))
        adj[v].append((w, i, u))

    visited = [False] * n
    cost = 0
    chosen = []
    components = 0
    # restart in every component
    for start in range(n):
        if visited[start]:
            continue
        components += 1
        visited[start] = True
        heap = list(adj[start])
        heapq.heapify(heap)
        while heap:
            w, i, v = heapq.heappop(heap)
            if visited[v]:
                continue
            visited[v] = True
            cost += w
            chosen.append(i)
            for item in adj[v]:
                if not visited[item[2]]:
                    heapq.heappush(heap, item)
    chosen.sort()
    return {"cost": cost, "edge_ids": chosen, "components": components}


def scc(request):
    n = request["n"]
    edges = request["edges"]
    adj = [[] for _ in range(n)]
    radj = [[] for _ in range(n)]
    for u, v in edges:
        adj[u].append(v)
        radj[v].append(u)

    # pass 1: finish order on G (iterative DFS)
    visited = [False] * n
    order = []
    nxt = [0] * n
    for s in range(n):
        if visited[s]:
            continue
        visited[s] = True
        stack = [s]
        while stack:
            u = stack[-1]
            nbrs = adj[u]
            if nxt[u] < len(nbrs):
                v = nbrs[nxt[u]]
                nxt[u] += 1
                if not visited[v]:
                    visited[v] = True
                    stack.append(v)
            else:
                stack.pop()
                order.append(u)

    # pass 2: DFS on the transpose
    component = [-1] * n
    label = 0
    for s in reversed(order):
        if component[s] != -1:
            continue
        component[s] = label
        stack = [s]
        while stack:
            u = stack.pop()
            for v in radj[u]:
                if component[v] == -1:
                    component[v] = label
                    stack.append(v)
        label += 1

    pairs = set()
    for u, v in edges:
        cu, cv = component[u], component[v]
        if cu != cv:
            pairs.add((cu, cv))
    condensation = [list(p) for p in pairs]
    return {"component": component, "condensation": condensation}


WHITE, GRAY, BLACK = 0, 1, 2


def _topo_order(n, adj):
    # returns None if a cycle exists
    color = [WHITE] * n
    nxt = [0] * n
    post = []
    for s in range(n):
        if color[s] != WHITE:
            continue
        color[s] = GRAY
        stack = [s]
        while stack:
            u = stack[-1]
            nbrs = adj[u]
            if nxt[u] < len(nbrs):
                v = nbrs[nxt[u]][0]
                nxt[u] += 1
                if color[v] == GRAY:
                    return None
                if color[v] == WHITE:
                    color[v] = GRAY
                    stack.append(v)
            else:
                stack.pop()
                color[u] = BLACK
                post.append(u)
    post.reverse()
    return post


def topo(request):
    n = request["n"]
    edges = request["edges"]
    adj = [[] for _ in range(n)]
    for u, v in edges:
        adj[u].append((v,))
    order = _topo_order(n, adj)
    if order is None:
        return {"acyclic": False, "order": []}
    return {"acyclic": True, "order": order}


def dag(request):
    n = request["n"]
    source = request["source"]
    edges = request["edges"]
    adj = [[] for _ in range(n)]
    for i, (u, v, w) in enumerate(edges):
        adj[u].append((v, w, i))
    # check the whole graph for cycles
    order = _topo_order(n, adj)
    if order is None:
        return {"acyclic": False, "distance": [], "parent_edge": []}

    dist = [None] * n
    parent = [-1] * n
    dist[source] = 0
    for u in order:
        du = dist[u]
        if du is None:
            continue
        for v, w, i in adj[u]:
            nd = du + w
            if dist[v] is None or nd < dist[v]:
                dist[v] = nd
                parent[v] = i
    return {"acyclic": True, "distance": dist, "parent_edge": parent}


def route_edge_ids(source, target, parent_edge, edges):
    # None means no route
    if target == source:
        return []
    if not parent_edge or parent_edge[target] == -1:
        return None
    ids = []
    cur = target
    while cur != source:
        e = parent_edge[cur]
        if e == -1 or len(ids) >= len(parent_edge):
            return None
        ids.append(e)
        cur = edges[e][0]
    ids.reverse()
    return ids


def reconstruct_route(source, target, parent_edge, edges):
    # vertex sequence source..target, None if unreachable
    ids = route_edge_ids(source, target, parent_edge, edges)
    if ids is None:
        return None
    return [source] + [edges[e][1] for e in ids]
