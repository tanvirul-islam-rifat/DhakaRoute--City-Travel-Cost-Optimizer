# DhakaRoute — City Travel Cost Optimizer

A real-world routing tool that models city areas as a **weighted graph** and solves three distinct travel problems using variations of Dijkstra's algorithm: finding the fastest route, finding the *safest* route (not the same thing!), and finding the fairest meeting point for a group scattered across the city.

---

## The Real-World Problems

1. **Fastest route** — classic shortest-path: minimize total travel time between two areas.
2. **Safest route** — a genuinely different problem: minimize the *single riskiest road segment* on the route, not the total risk. A long route where every road is moderately safe should beat a short route that passes through one dangerous segment. This is a **minimax path problem**, solved with a modified Dijkstra.
3. **Best meeting point** — given several people scattered across the city, find the one area that minimizes the *maximum* travel time for any individual — the fairest possible meeting spot, not just the one closest to the average.

All three are solved using the same underlying weighted-graph model, demonstrating how one data structure supports multiple algorithmic objectives.

---

## Features

- **Build a City Graph** — Add areas and roads with both a travel cost (minutes) and a risk level (0–10)
- **Fastest/Cheapest Route** — Standard Dijkstra's algorithm with a min-heap priority queue
- **Safest Route** — Modified Dijkstra solving a minimax optimization instead of a sum minimization
- **Best Meeting Point** — Runs Dijkstra once per person, then finds the area minimizing the worst-case travel time across the group
- **Sample City Loader** — Pre-loads a realistic 10-area, 15-road Dhaka-style city map to try immediately

---

## How to Run

```bash
# Clone the repository
git clone https://github.com/tanvirul-islam-rifat/DhakaRoute--City-Travel-Cost-Optimizer.git
cd dhakaroute-travel-optimizer

# Run the application (Python 3 required, no external libraries needed)
python3 dhakaroute.py
```

On first run, choose option **8** to load the sample city map, then try options 5–7.

---

## Sample Output

**Fastest vs Safest can genuinely disagree:**

```
-- Find Fastest/Cheapest Route --
From: A
To: D
Fastest route: A -> B -> D
Total travel cost: 10.0 minutes

-- Find Safest Route (Minimax Risk) --
From: A
To: D
Safest route: A -> C -> D
Maximum risk level on this route: 1.0
(This minimizes the WORST road segment, not total risk —
 a longer but uniformly safe route beats a short risky one.)
```

Here, A→B→D is fastest (10 min) but passes through a high-risk segment (risk 9). A→C→D takes longer (40 min) but never exceeds risk level 1 on any segment — the algorithm correctly identifies these as different optimization goals.

**Meeting point for a scattered group:**

```
-- Find Best Meeting Point --
Best meeting point: Uttara
Maximum travel time for any person: 30 minutes
Combined travel time for everyone: 57 minutes
   Mirpur -> Uttara: 30 minutes
   Uttara -> Uttara: 0 minutes
   Gulshan -> Uttara: 27 minutes
```

---

## Project Structure

```
dhakaroute-travel-optimizer/
├── dhakaroute.py     # Graph model + 3 algorithms + CLI
├── data/
│   ├── areas.txt     # Persisted area list (auto-generated)
│   └── roads.txt     # Persisted weighted edges (auto-generated)
└── README.md
```

---

## Technical Architecture

- **Language:** Python 3.x
- **Paradigm:** Graph-based algorithm design with object-oriented data modeling
- **Core Data Structure:** Weighted undirected graph via adjacency list (`dict[str, list[tuple]]`), each edge storing both cost and risk
- **Priority Queue:** Python's `heapq` module for all three Dijkstra variants
- **Data Storage:** Flat-file text database (`.txt`) for areas and weighted roads
- **Interface:** Command Line Interface (CLI)

## Core Engineering Practices Demonstrated

- **Dijkstra's Algorithm from Scratch:** Implemented directly with a min-heap and a `visited` set — not a library call — including proper handling of stale heap entries via the visited check
- **Algorithm Variant via Relaxation Rule Change:** The safest-route function reuses the exact same heap-based traversal skeleton as standard Dijkstra, but replaces the relaxation step `dist[v] = dist[u] + weight` with a minimax relaxation `max_risk[v] = max(max_risk[u], risk)` — demonstrating how changing one line of mathematical logic transforms a sum-shortest-path algorithm into a bottleneck-minimization algorithm
- **Multi-Source Graph Search:** The meeting-point feature runs independent Dijkstra searches from every person's location, then performs a candidate-evaluation pass over all areas to solve a *minimize-the-maximum* fairness objective — a practical extension beyond textbook single-source shortest path
- **Path Reconstruction via Predecessor Tracking:** All three algorithms maintain a `prev` map during traversal and reconstruct the full path by walking backward from the destination, rather than only returning a distance/cost value
- **Edge Case Handling:** Unreachable destinations, disconnected graphs, and empty meeting-point candidate sets are all explicitly detected and reported rather than causing silent failures or incorrect results

## Author

**Md. Tanvirul Islam Rifat**

* **GitHub:** [@tanvirul-islam-rifat](https://github.com/tanvirul-islam-rifat)
* **LinkedIn:** [Tanvirul Islam Rifat](https://www.linkedin.com/in/tanvirul-islam-rifat)
