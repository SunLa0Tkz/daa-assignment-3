# Assignment 3 Analysis

I used Python. My code is in `src/Python/algorithms.py`. I did not change the
adapter `src/Python/main.py` from the template.

## How to run

No build is needed for Python. All commands are run from the repo root:

```
python tools/run.py --setup
python tools/run.py --check
python tools/run.py --input tests/my_cases.jsonl
python tests/run_tests.py
python tests/route_demo.py
python benchmark/bench.py
```

`run_tests.py` takes about 10 seconds because it also runs the big inputs. With
`--quick` it skips them.

## Things that apply to all methods

**State reset.** Every function builds its own lists (adjacency, visited,
DSU and so on) when it is called and returns a dict. I don't keep anything in
global variables, so one request cannot affect the next one. To check this, my
test script sends all hand cases two times in the same process and compares
the answers.

**Deep DFS.** Python's recursion limit is 1000 by default, and a chain of
100000 vertices would crash a recursive DFS. So I wrote every DFS with my own
stack. I also keep an array `nxt[u]` with the position of the next neighbour
of `u`. When the DFS comes back to `u` it continues from there, so neighbours
are not scanned again, and the DFS stays O(n + m).

**Big numbers.** Python ints have no overflow, so costs and distances bigger
than 32 bits are fine. For unreachable vertices I use `None`, and it becomes
`null` in JSON.

## DSU

I keep `parent` and `size` arrays, plus two counters: `components` (starts
at n) and `largest` (starts at 1, or 0 if n = 0).

`find` goes up to the root and then goes up again, setting every node on the
path to point straight to the root (path compression). `union` finds both
roots. If they are the same, nothing happens. Otherwise the smaller tree is
attached to the bigger one (union by size), `components` goes down by one, and
`largest` is updated if the new set is bigger. After every operation I add
`[components, largest]` to `states`.

Invariant: each tree in `parent` is one set, `size[root]` is the size of that
set, and the counters match the current sets.

Why it is correct: path compression only moves pointers inside the same tree,
so sets do not change. A union joins exactly two sets, so components decreases
by 1. Sets only grow when merged, so a running maximum is enough for
`largest`.

Edge cases: n = 0 gives `states = []`. A self-union or repeating the same
union does nothing.

Complexity: O(n + q α(n)) time and O(n + q) memory, including the output.

## Kruskal

1. Sort edge indices by weight. I sort indices, not the edges themselves, so
   the original IDs stay correct.
2. Go through the edges and skip self-loops.
3. If `find(u) != find(v)`, take the edge and union the two vertices.
4. Stop after n - 1 edges.
5. The number of components is n minus the number of chosen edges.

Invariant: the chosen edges never form a cycle and they are always part of
some minimum spanning forest.

Why it is correct: this follows from the cut property. When an edge joins two
different trees, it is the cheapest edge leaving one of those trees, because
all cheaper edges were already looked at. A forest with c components has n - c
edges, which is why the component formula works. Isolated vertices are
counted automatically. With parallel edges the cheapest copy is taken first,
and the others are rejected because they would make a cycle.

Edge cases: empty graph, isolates, a self-loop that is the cheapest edge,
parallel edges, equal weights, negative weights, total cost of 3·10^9.

Complexity: O(n + m log m) time, O(n + m) memory.

## Prim

I build undirected adjacency lists with `(weight, id, other vertex)` and skip
self-loops. Then I loop over all vertices. Every time I find a vertex that is
not visited yet, I count a new component and start Prim from it:
- mark it visited and put its edges into a heap;
- pop the cheapest edge;
- if the other end is already visited, throw the edge away (lazy deletion);
- otherwise take the edge, mark the vertex, and push its edges.

When the heap is empty, the component is done, and the outer loop finds the
next unvisited vertex. An isolated vertex is just a restart with no edges.

Invariant: the visited vertices of the current component are connected by
chosen edges that belong to some MSF, and the heap has all edges going out of
this set (maybe with some old ones).

Why it is correct: the edge popped from the heap is the cheapest edge crossing
the cut between visited and unvisited vertices, so the cut property applies
again. The restarts mean every vertex gets processed, and the number of
restarts equals the number of components. So Prim always gets the same cost
and component count as Kruskal, even though the chosen IDs can be different.

Edge cases: the same as Kruskal, plus a forest with several components and an
input with 100000 isolated vertices.

Complexity: O(n + m log m) time with a lazy heap, O(n + m) memory.

## SCC (Kosaraju)

1. Build the graph and its transpose.
2. First DFS on the original graph. When a vertex is finished, add it to
   `order`.
3. Go through `order` backwards. For every vertex without a label, run a DFS
   on the transposed graph and give everything it reaches the same new label.
4. For the condensation, go through the edges. If the two endpoints have
   different labels, add the pair to a set, so duplicates are removed.

Why it is correct: if there is an edge from SCC A to SCC B, then A has a later
finish time than B. So the second pass always starts in an SCC that has no
incoming edges from unlabeled SCCs in the original graph. In the transposed
graph that DFS can't leave its SCC, because the edges going out lead only to
SCCs that already have labels. So each DFS in the second pass labels exactly
one SCC. Self-loops and duplicate edges don't change who can reach whom.

Edge cases: empty graph, isolated vertices (each is its own SCC), self-loops,
duplicate cross edges (only one pair in the output), a ring of 100000 vertices
(one SCC), a chain of 100000 (100000 SCCs).

Complexity: O(n + m) expected time because of the hash set, O(n + m) memory.

## Topological order

I use three colors: 0 = not visited, 1 = active (on the current path),
2 = finished. The DFS starts from every unvisited vertex, so all components
are checked.
- An edge to an active vertex means there is a cycle, so I return
  `acyclic = false` and an empty order.
- An edge to a finished vertex is fine.
- When a vertex has no neighbours left, it becomes finished and is added to a
  list.

At the end the list is reversed.

Invariant: the active vertices are exactly the vertices on my stack.

Why it is correct: if u -> v and v is active, then v is an ancestor of u on
the current path, so there is a cycle. A self-loop is the case u = v. In the
other direction, if there is a cycle, the first vertex of it that we visit
stays active while the rest of the cycle is explored, so the edge back to it
will be found. If there is no cycle, then for every edge u -> v, v finishes
before u, so after reversing, u comes first.

Edge cases: n = 0, isolates, duplicate edges, a self-loop, a cycle in a
component other than the first, a chain of 100000, a ring of 100000.

Complexity: O(n + m) time and memory.

## DAG shortest paths

1. Run the same three-color DFS on the whole graph, not only from the source.
   If there is any cycle, even one the source can't reach, return false and
   two empty arrays.
2. `dist` starts as all `None`, `parent_edge` as all -1, and
   `dist[source] = 0`.
3. Go through the vertices in topological order. Skip a vertex if its
   distance is `None`, so I never relax from an unreachable vertex.
4. For every edge `u -> v` with weight `w`: if `dist[v]` is `None` or
   `dist[u] + w` is smaller, update `dist[v]` and set `parent_edge[v]` to the
   edge ID.

Invariant: when a vertex is processed, its distance is already final, because
all vertices that have edges into it come earlier in the order.

Why it is correct: any shortest path goes forward in topological order, so its
edges get relaxed in the right order (induction on the order). Negative
weights are not a problem because there are no cycles. The parent edge always
ends at the vertex and satisfies `dist[u] + w = dist[v]`, so following
parents leads back to the source. I use a strict `<`, so with ties the first
edge found stays. Any other tight edge would also be accepted.

Edge cases: n = 1, a source that is not vertex 0 (vertices before it are
unreachable), an unreachable cycle, parallel edges with the same weight, tied
routes, negative weights, distances of -3·10^9 and about 10^14.

Complexity: O(n + m) time and memory.

### Route helper

`reconstruct_route(source, target, parent_edge, edges)` returns the list of
vertices from source to target. `route_edge_ids(...)` returns the edge IDs
on the same route.

- For target = source the route is `[source]`.
- If the target can't be reached, I return `None`. This is only for the
  helper; the JSON still has `null` in `distance`.

Both helpers walk back from the target using `parent_edge` and then reverse
the result, so they take O(L) time, where L is the length of the route.

This is the output of `python tests/route_demo.py`. Graph 1 is the example
from the assignment. The script checks that every edge goes from `route[k]` to
`route[k+1]`, and that the sum of weights equals the distance.

```
graph 1: {'acyclic': True, 'distance': [0, 3, -4, 0, None], 'parent_edge': [-1, 0, 2, 3, -1]}
reachable target 3     route=[0, 1, 2, 3] edge_ids=[0, 2, 3] weight=0 distance=0  check=OK
target = source 0      route=[0] edge_ids=[] weight=0 distance=0  check=OK
unreachable target 4   route=None edge_ids=None  check=OK
graph 2: {'acyclic': True, 'distance': [0, 5, 6], 'parent_edge': [-1, 0, 3]}
parallel target 1      route=[0, 1] edge_ids=[0] weight=5 distance=5  check=OK
tied target 2          route=[0, 2] edge_ids=[3] weight=6 distance=6  check=OK
alt witness, target 2  route=[0, 1, 2] edge_ids=[1, 2] weight=6 distance=6  check=OK
ALL ROUTE CHECKS OK
```

In graph 1, the route to 3 uses edge 0 (0->1, w=3), edge 2 (1->2, w=-7) and
edge 3 (2->3, w=4). The total is 3 - 7 + 4 = 0, which is the same as
`distance[3]`.

In graph 2, edges 0 and 1 are parallel (both 0->1 with weight 5). There are
two shortest ways to reach 2 with cost 6: edge 3 directly, or edges 1 and 2.
My code returned `[-1, 0, 3]`, but `[-1, 1, 2]` is also correct, and the last
line shows that it gives a valid route too.

## Complexity table

| method | time | memory |
|---|---|---|
| dsu | O(n + q α(n)) | O(n + q) |
| kruskal | O(n + m log m) | O(n + m) |
| prim | O(n + m log m) | O(n + m) |
| scc | O(n + m) expected | O(n + m) |
| topo | O(n + m) | O(n + m) |
| dag | O(n + m), route O(L) | O(n + m) |

## My tests

Everything is in `tests/`:

- `cases.json`: 33 small cases written by hand. Each has the input, the
  expected answer and a short explanation (`why`) of why that answer is
  right. The examples from the assignment are included.
- `my_cases.jsonl`: the same inputs, one per line, for
  `tools/run.py --input`.
- `actual_outputs.jsonl`: what my program printed for those cases.
- `validators.py`: checkers for each task. I wrote them with different
  algorithms (Kahn's algorithm, Tarjan, brute force for MSF, simple
  relabeling for DSU), so a mistake in my main code would not be repeated in
  the checker.
- `run_tests.py`: runs everything through `src/Python/main.py`.

What `run_tests.py` does:

1. **Hand cases.** They cover empty graphs, isolates, self-unions and
   repeated unions, loops, parallel and tied edges, negative weights, sums
   over 32 bits, unreachable vertices, and a cycle the source can't reach.
   They are all sent two times in one process to check the state reset.
   - Where the answer is unique (DSU states, cyclic results, MSF cost and
     component count), I compare it exactly.
   - Where many answers are possible, I check it with the validator.
2. **Other valid answers.** I check that the validators accept a different
   correct answer: another MSF, another topological order, other SCC labels,
   another parent edge. I also check that they reject wrong ones: a forest
   with a cycle, a non-minimal tree, an order that breaks an edge, wrong SCC
   groups, a parent edge that doesn't end at the vertex, a distance that
   isn't the shortest.
3. **Random tests.** 150 random small graphs for each task (seed 2026). For
   MSF I compare with brute force over all subsets of edges.
4. **Big inputs.** n = 100000, m or q = 250000, weights up to ±10^9, chains
   and a ring of 100000 vertices, 100000 isolated vertices for Prim, and a
   DAG chain where the distance reaches about 10^14.

All tests passed, and `python tools/run.py --check` passed all 36 public
cases and the state reset check. The slowest big case was Prim with n = 100000 and
m = 250000. It took around 1.5 s including Python startup, which is fine for
the 20 s limit.

## Benchmark: Kruskal vs Prim

Setup:

- Script: `benchmark/bench.py`, seed 12345.
- Graphs: a random spanning tree plus random extra edges until there are m
  edges, so loops and parallel edges can appear. Weights are random in
  [-10^9, 10^9]. Both algorithms get the same edge list for each size.
- Correctness first: each result is checked with the MSF validator (no
  cycle, n - c edges, minimum cost), and the two costs must be equal. This
  first run also works as the warm-up.
- Runs: after the warm-up, 5 timed runs per method per size, and I take the
  median.
- Timer: `time.perf_counter()`, only around the call `kruskal(n, edges)` or
  `prim(n, edges)`.
  - Included: the algorithm itself, and the graph construction inside the
    function (the sort in Kruskal, the adjacency lists in Prim).
  - Not included: generating the graph, JSON reading and writing, starting
    Python.
  - The boundary is the same for both methods. There is no compilation in
    Python.
- Machine: Python 3.13.17 (CPython), Linux x86_64, Intel Xeon @ 2.10GHz,
  2 CPUs.

| n | m | method | runs (ms) | median (ms) |
|---|---|---|---|---|
| 1000 | 5000 | Kruskal | 5.1, 6.6, 4.4, 4.8, 4.8 | 4.8 |
| 1000 | 5000 | Prim | 6.6, 6.2, 6.6, 6.5, 6.4 | 6.5 |
| 10000 | 50000 | Kruskal | 66.5, 72.1, 65.3, 63.4, 82.2 | 66.5 |
| 10000 | 50000 | Prim | 142.9, 103.7, 115.4, 103.2, 116.3 | 115.4 |
| 100000 | 250000 | Kruskal | 723.8, 832.0, 946.2, 739.8, 846.2 | 832.0 |
| 100000 | 250000 | Prim | 1174.0, 1310.3, 1203.6, 1214.5, 1238.7 | 1214.5 |

The MSF costs were the same for both methods at every size.

**Asymptotic argument.** Both algorithms are O(n + m log m) here, so in
theory they should grow at about the same rate.

**What I observed.**
- Kruskal was faster at all three sizes, about 1.35 to 1.75 times. I think the
  reason is Python itself. Kruskal does one big sort, and `sorted` is written
  in C, so it is fast. Prim calls `heappush` and `heappop` up to 2m times from
  Python code, makes a lot of tuples, and keeps old entries in the heap
  because of lazy deletion.
- The time grew more than m log m predicts. From the smallest to the largest
  size, m log m grows about 73 times, but the time grew about 170 times for
  Kruskal and 190 times for Prim. My guess is caching: at n = 1000 everything
  fits in the CPU cache, and at n = 100000 it doesn't. I did not profile this,
  so it is only a guess.

**Limitations.**
- I only tested sparse graphs (m is 2.5 to 5 times n). On dense graphs, or
  with a different Prim (indexed heap), the result could be different.
- The machine was shared, and single runs jumped by up to about 30%, which is
  why I used medians.

## Sources and AI

- Cormen et al., *Introduction to Algorithms* (3rd ed.), chapters 21, 22, 23
  and 24.2.
- Lecture slides from this course.
- I used Claude (an AI assistant) to help write the code, tests, benchmark
  script and this file. I checked the code myself, ran all the tests and the
  benchmark, and the numbers above are from those runs.
