"""
DhakaRoute — City Travel Cost Optimizer
A real-world routing tool that models Dhaka's areas as a weighted graph
and finds the cheapest/fastest route between two points using Dijkstra's
algorithm, plus a "safest route" mode that minimizes maximum risk exposure
instead of total distance (a minimax path problem).

"""

import os
import heapq

AREAS_FILE = "data/areas.txt"
ROADS_FILE = "data/roads.txt"

INF = float("inf")


# ═══════════════════════════════════════════════════════
# CITY GRAPH
# ═══════════════════════════════════════════════════════

class CityGraph:
    """
    Models a city as a weighted, undirected graph.
    Each edge (road) has a travel cost (time in minutes, or fare in taka)
    and a risk level (0 = very safe, 10 = high risk) used for safest-route mode.
    """

    def __init__(self):
        self.areas = set()
        self.adj = {}   # area -> list of (neighbor, cost, risk)
        self._load()

    # ── Persistence ──

    def _load(self):
        os.makedirs("data", exist_ok=True)
        if os.path.exists(AREAS_FILE):
            with open(AREAS_FILE, "r") as f:
                for line in f:
                    area = line.strip()
                    if area:
                        self.areas.add(area)
                        self.adj.setdefault(area, [])

        if os.path.exists(ROADS_FILE):
            with open(ROADS_FILE, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    a, b, cost, risk = line.split(",")
                    self._add_edge_internal(a, b, float(cost), float(risk))

    def _save_areas(self):
        with open(AREAS_FILE, "w") as f:
            for area in sorted(self.areas):
                f.write(area + "\n")

    def _save_roads(self):
        seen = set()
        with open(ROADS_FILE, "w") as f:
            for a in self.adj:
                for (b, cost, risk) in self.adj[a]:
                    edge_key = tuple(sorted([a, b]))
                    if edge_key not in seen:
                        seen.add(edge_key)
                        f.write(f"{a},{b},{cost},{risk}\n")

    def _add_edge_internal(self, a, b, cost, risk):
        self.adj.setdefault(a, [])
        self.adj.setdefault(b, [])
        self.adj[a].append((b, cost, risk))
        self.adj[b].append((a, cost, risk))

    # ── Graph Management ──

    def add_area(self, name):
        if name in self.areas:
            return False, f"Area '{name}' already exists."
        self.areas.add(name)
        self.adj.setdefault(name, [])
        self._save_areas()
        return True, f"Added area: {name}"

    def add_road(self, a, b, cost, risk=1.0):
        if a not in self.areas or b not in self.areas:
            return False, "Both areas must exist first."
        self._add_edge_internal(a, b, cost, risk)
        self._save_roads()
        return True, f"Road added: {a} <-> {b} (cost: {cost}, risk: {risk})"

    def list_areas(self):
        return sorted(self.areas)

    def list_roads(self):
        seen = set()
        roads = []
        for a in self.adj:
            for (b, cost, risk) in self.adj[a]:
                key = tuple(sorted([a, b]))
                if key not in seen:
                    seen.add(key)
                    roads.append((a, b, cost, risk))
        return roads


# ═══════════════════════════════════════════════════════
# DIJKSTRA — CHEAPEST / FASTEST ROUTE
# ═══════════════════════════════════════════════════════

def dijkstra_shortest_path(graph, source, destination):
    """
    Standard Dijkstra's algorithm using a min-heap priority queue.
    Finds the minimum total-cost path from source to destination.
    Returns (distance, path, nodes_explored) or (INF, [], n) if unreachable.
    """
    if source not in graph.areas or destination not in graph.areas:
        return INF, [], 0

    dist = {area: INF for area in graph.areas}
    prev = {area: None for area in graph.areas}
    dist[source] = 0
    visited = set()
    pq = [(0, source)]
    nodes_explored = 0

    while pq:
        d, u = heapq.heappop(pq)
        if u in visited:
            continue
        visited.add(u)
        nodes_explored += 1

        if u == destination:
            break

        for (v, cost, risk) in graph.adj.get(u, []):
            if v in visited:
                continue
            new_dist = d + cost
            if new_dist < dist[v]:
                dist[v] = new_dist
                prev[v] = u
                heapq.heappush(pq, (new_dist, v))

    if dist[destination] == INF:
        return INF, [], nodes_explored

    # Reconstruct path
    path = []
    node = destination
    while node is not None:
        path.append(node)
        node = prev[node]
    path.reverse()

    return dist[destination], path, nodes_explored


# ═══════════════════════════════════════════════════════
# MINIMAX DIJKSTRA — SAFEST ROUTE
# ═══════════════════════════════════════════════════════

def safest_path(graph, source, destination):
    """
    Modified Dijkstra solving a MINIMAX path problem:
    instead of minimizing total cost, minimize the MAXIMUM risk value
    encountered along the path. This answers "what is the safest route?"
    where safety is determined by the single riskiest road segment,
    not the sum of all risks (a long but uniformly-safe route should beat
    a short route with one dangerous segment).
    """
    if source not in graph.areas or destination not in graph.areas:
        return INF, [], 0

    # max_risk_on_path[node] = minimum possible "worst edge" to reach node
    max_risk = {area: INF for area in graph.areas}
    prev = {area: None for area in graph.areas}
    max_risk[source] = 0
    visited = set()
    pq = [(0, source)]
    nodes_explored = 0

    while pq:
        current_max, u = heapq.heappop(pq)
        if u in visited:
            continue
        visited.add(u)
        nodes_explored += 1

        if u == destination:
            break

        for (v, cost, risk) in graph.adj.get(u, []):
            if v in visited:
                continue
            # The bottleneck risk if we go through u to reach v
            candidate = max(current_max, risk)
            if candidate < max_risk[v]:
                max_risk[v] = candidate
                prev[v] = u
                heapq.heappush(pq, (candidate, v))

    if max_risk[destination] == INF:
        return INF, [], nodes_explored

    path = []
    node = destination
    while node is not None:
        path.append(node)
        node = prev[node]
    path.reverse()

    return max_risk[destination], path, nodes_explored


# ═══════════════════════════════════════════════════════
# MULTI-SOURCE: BEST MEETING POINT
# ═══════════════════════════════════════════════════════

def find_meeting_point(graph, people_locations):
    """
    Real-world problem: a group of people are scattered across the city.
    Find the single area that minimizes the MAXIMUM travel cost for anyone
    in the group (fairest meeting point — nobody travels excessively far).

    Runs Dijkstra once from each person's location, then for every candidate
    area, takes the max distance across all people, and picks the area
    that minimizes that max.
    """
    all_distances = {}  # person_location -> {area: dist}

    for person_loc in people_locations:
        dist = {area: INF for area in graph.areas}
        dist[person_loc] = 0
        visited = set()
        pq = [(0, person_loc)]

        while pq:
            d, u = heapq.heappop(pq)
            if u in visited:
                continue
            visited.add(u)
            for (v, cost, risk) in graph.adj.get(u, []):
                new_dist = d + cost
                if new_dist < dist[v]:
                    dist[v] = new_dist
                    heapq.heappush(pq, (new_dist, v))

        all_distances[person_loc] = dist

    best_area = None
    best_max_dist = INF
    results = {}

    for area in graph.areas:
        distances_for_area = [all_distances[p].get(area, INF) for p in people_locations]
        if INF in distances_for_area:
            continue
        max_dist = max(distances_for_area)
        total_dist = sum(distances_for_area)
        results[area] = (max_dist, total_dist, distances_for_area)
        if max_dist < best_max_dist:
            best_max_dist = max_dist
            best_area = area

    return best_area, results


# ═══════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════

def seed_sample_city(graph):
    """Pre-load a sample Dhaka-style area graph with realistic travel costs (minutes)."""
    sample_areas = [
        "Mirpur", "Dhanmondi", "Gulshan", "Banani", "Uttara",
        "Motijheel", "Mohakhali", "Badda", "Farmgate", "Bashundhara"
    ]
    # (area_a, area_b, cost_minutes, risk_level 0-10)
    sample_roads = [
        ("Mirpur", "Farmgate", 18, 3),
        ("Mirpur", "Dhanmondi", 22, 2),
        ("Farmgate", "Dhanmondi", 10, 2),
        ("Farmgate", "Mohakhali", 15, 4),
        ("Dhanmondi", "Motijheel", 25, 3),
        ("Mohakhali", "Gulshan", 12, 2),
        ("Mohakhali", "Banani", 8, 2),
        ("Gulshan", "Banani", 7, 1),
        ("Gulshan", "Badda", 14, 5),
        ("Banani", "Uttara", 20, 3),
        ("Badda", "Bashundhara", 10, 4),
        ("Bashundhara", "Uttara", 25, 6),
        ("Motijheel", "Mohakhali", 20, 7),
        ("Gulshan", "Bashundhara", 16, 3),
        ("Uttara", "Mirpur", 30, 5),
    ]
    for area in sample_areas:
        if area not in graph.areas:
            graph.add_area(area)
    for a, b, cost, risk in sample_roads:
        graph.add_road(a, b, cost, risk)


def print_menu():
    print("\n" + "=" * 52)
    print("       DhakaRoute — City Travel Optimizer")
    print("=" * 52)
    print("  1. Add an Area")
    print("  2. Add a Road (Area A <-> Area B)")
    print("  3. List All Areas")
    print("  4. List All Roads")
    print("  5. Find Fastest/Cheapest Route (Dijkstra)")
    print("  6. Find Safest Route (Minimax Risk)")
    print("  7. Find Best Meeting Point (Multi-person)")
    print("  8. Load Sample Dhaka-style City Map")
    print("  0. Exit")
    print("=" * 52)


def main():
    os.makedirs("data", exist_ok=True)
    graph = CityGraph()
    print("\nWelcome to DhakaRoute — model your city as a weighted graph")
    print("and let Dijkstra's algorithm find the optimal route.")

    while True:
        print_menu()
        choice = input("Enter your choice: ").strip()

        if choice == "1":
            name = input("\nArea name: ").strip()
            ok, msg = graph.add_area(name)
            print(msg)

        elif choice == "2":
            print("\n-- Add Road --")
            a = input("Area A: ").strip()
            b = input("Area B: ").strip()
            try:
                cost = float(input("Travel cost (minutes): ").strip())
            except ValueError:
                cost = 10.0
            try:
                risk = float(input("Risk level (0=safe to 10=risky, default 1): ").strip() or 1.0)
            except ValueError:
                risk = 1.0
            ok, msg = graph.add_road(a, b, cost, risk)
            print(msg)

        elif choice == "3":
            areas = graph.list_areas()
            if not areas:
                print("\nNo areas yet. Try option 8 to load a sample city.")
            else:
                print(f"\n{len(areas)} area(s): {', '.join(areas)}")

        elif choice == "4":
            roads = graph.list_roads()
            if not roads:
                print("\nNo roads yet.")
            else:
                print(f"\n{'From':<15}{'To':<15}{'Cost(min)':<12}{'Risk'}")
                print("-" * 50)
                for a, b, cost, risk in roads:
                    print(f"{a:<15}{b:<15}{cost:<12}{risk}")

        elif choice == "5":
            print("\n-- Find Fastest/Cheapest Route --")
            source = input("From: ").strip()
            dest = input("To: ").strip()
            dist, path, explored = dijkstra_shortest_path(graph, source, dest)
            if dist == INF:
                print(f"\nNo route found between {source} and {dest}.")
            else:
                print(f"\nFastest route: {' -> '.join(path)}")
                print(f"Total travel cost: {dist} minutes")
                print(f"Areas explored by Dijkstra: {explored}")

        elif choice == "6":
            print("\n-- Find Safest Route (Minimax Risk) --")
            source = input("From: ").strip()
            dest = input("To: ").strip()
            risk, path, explored = safest_path(graph, source, dest)
            if risk == INF:
                print(f"\nNo route found between {source} and {dest}.")
            else:
                print(f"\nSafest route: {' -> '.join(path)}")
                print(f"Maximum risk level on this route: {risk}")
                print("(This minimizes the WORST road segment, not total risk —")
                print(" a longer but uniformly safe route beats a short risky one.)")

        elif choice == "7":
            print("\n-- Find Best Meeting Point --")
            print("Enter each person's starting area. Type 'done' when finished.")
            people = []
            while True:
                loc = input(f"  Person {len(people) + 1} location (or 'done'): ").strip()
                if loc.lower() == "done":
                    break
                if loc:
                    people.append(loc)
            if len(people) < 2:
                print("Need at least 2 people to find a meeting point.")
            else:
                best_area, results = find_meeting_point(graph, people)
                if best_area is None:
                    print("No common reachable meeting point found.")
                else:
                    max_d, total_d, dists = results[best_area]
                    print(f"\nBest meeting point: {best_area}")
                    print(f"Maximum travel time for any person: {max_d} minutes")
                    print(f"Combined travel time for everyone: {total_d} minutes")
                    for p, d in zip(people, dists):
                        print(f"   {p} -> {best_area}: {d} minutes")

        elif choice == "8":
            seed_sample_city(graph)
            print("\nSample Dhaka-style city map loaded (10 areas, 15 roads).")

        elif choice == "0":
            print("\nSafe travels! Goodbye.\n")
            break

        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()
