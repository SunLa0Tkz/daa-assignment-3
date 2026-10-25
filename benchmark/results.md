Environment: Python 3.13.17 (CPython), Linux 6.18.44-fc-v153, x86_64, 2 logical CPUs

Seed 12345, 1 warm-up + 5 timed runs, time.perf_counter around the algorithm call only. Both forests verified (acyclic, n-c edges, optimum cost) before timing.

| n | m | method | runs (ms) | median (ms) | MSF cost |
|---|---|---|---|---|---|
| 1000 | 5000 | Kruskal | 5.1, 6.6, 4.4, 4.8, 4.8 | **4.8** | -750972988838 |
| 1000 | 5000 | Prim | 6.6, 6.2, 6.6, 6.5, 6.4 | **6.5** | -750972988838 |
| 10000 | 50000 | Kruskal | 66.5, 72.1, 65.3, 63.4, 82.2 | **66.5** | -7617223389661 |
| 10000 | 50000 | Prim | 142.9, 103.7, 115.4, 103.2, 116.3 | **115.4** | -7617223389661 |
| 100000 | 250000 | Kruskal | 723.8, 832.0, 946.2, 739.8, 846.2 | **832.0** | -53272763429611 |
| 100000 | 250000 | Prim | 1174.0, 1310.3, 1203.6, 1214.5, 1238.7 | **1214.5** | -53272763429611 |
