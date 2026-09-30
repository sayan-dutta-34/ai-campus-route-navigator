# AI Campus Route Navigator

## 🎓 Assignment Information

**Course:** AI/ML Laboratory | B.Tech. 5th Semester  
**Assignment:** X_03 — AI Campus Route Navigator

---

## 📋 Project Objective

Build an AI-based campus navigation system for the **CU Technology Campus** (University of Calcutta). The system converts a satellite map of the campus into a weighted graph and uses **two AI routing agents** with different search strategies to find routes between locations, allowing comparison of their behaviour.

---

## 🧩 Problem Statement

Given a satellite map of the CU Technology Campus:

1. Convert the map into a **weighted graph** using known campus locations.
2. Build two AI routing agents:
   - **PATHFINDER** → Greedy Best-First Search
   - **ORBIT** → A\* Search
3. Give both agents different source–destination problems.
4. Compare the routes and computational behaviour.

> _Does the path that looks closest to the destination also produce the best route?_

---

## 🗺️ Campus Graph Representation

### Nodes (19 Campus Locations)

| #   | Location             | Description                          |
| --- | -------------------- | ------------------------------------ |
| 1   | Entry Gate 1         | Main entrance (south-west)           |
| 2   | Entry Gate 2         | Secondary entrance (south-east)      |
| 3   | Reception            | Reception of Calcutta University     |
| 4   | Canteen              | CU Technology Campus Canteen         |
| 5   | Power Area           | Power/utility area                   |
| 6   | Playground           | Technology Campus playground         |
| 7   | Parking Area         | Vehicle parking                      |
| 8   | Tower 2 Front Entry  | Front entrance to Tower 2            |
| 9   | Tower 2 Rear Entry   | Rear entrance to Tower 2             |
| 10  | CSE_Reflexon Room    | CSE zone — Reflexon Room             |
| 11  | CSE Laboratory       | CSE zone — Main Lab                  |
| 12  | CSE_AKC Seminar Hall | CSE zone — Seminar Hall              |
| 13  | Lift Area            | Transition point for CSE zone access |
| 14  | Library              | Campus Library                       |
| 15  | Garden Area          | Technology Campus garden             |
| 16  | CRNN Centre          | CRNN Centre (Nano Technology)        |
| 17  | Auditorium Hall      | Main auditorium                      |
| 18  | New Building 1       | New Building 1                       |
| 19  | New Building 2       | Workshop Building                    |

### Edges & Weights

Edges represent **walkable connections** between locations. Weights represent **approximate walking distances** in meters, determined from the campus map and experience.

### Data Storage — `campus.json`

The campus graph is stored separately in [`campus.json`](campus.json) and loaded at runtime. This separates the data from the algorithm implementation, allowing the campus map to be modified without changing any code.

```json
{
  "nodes": { "Location Name": {"x": 100.0, "y": 200.0}, ... },
  "edges": [ {"from": "A", "to": "B", "weight": 120}, ... ],
  "cse_zone": ["CSE Laboratory", "CSE_AKC Seminar Hall", "CSE_Reflexon Room"],
  "cse_entry_points": ["Tower 2 Front Entry", "Tower 2 Rear Entry"],
  "cse_transition_node": "Lift Area"
}
```

---

## 🔍 Heuristic Function

Both agents use the **same heuristic** — a conservatively scaled **Euclidean (straight-line) distance** between two locations based on their approximate map coordinates. The graph derives the scale from its edge weights so the heuristic remains admissible despite the approximate coordinate units.

```
h(n) = √((x₁ - x₂)² + (y₁ - y₂)²)
```

This heuristic is **admissible** (never overestimates the actual walking distance) and **consistent**, making it suitable for both Greedy Best-First Search and A\*.

Using the same heuristic for both agents ensures the comparison is meaningful — the only difference is how each agent uses the heuristic.

---

## 🤖 Agent 1: PATHFINDER — Greedy Best-First Search

**PATHFINDER** uses **Greedy Best-First Search** and asks at each step:

> _"Which location appears closest to my destination?"_

**Priority function:**

```
f(n) = h(n)
```

- Uses only the heuristic (estimated remaining distance)
- Does **not** consider the cost already travelled
- Tends to find paths quickly but may not find the shortest path
- Can be misled by the heuristic into suboptimal routes

**Implementation:** Custom implementation from scratch using Python's `heapq` module for the priority queue. No external pathfinding libraries used.

---

## 🤖 Agent 2: ORBIT — A\* Search

**ORBIT** uses **A\* Search** and considers both:

- **g(n):** actual distance already travelled
- **h(n):** estimated remaining distance

**Priority function:**

```
f(n) = g(n) + h(n)
```

- Balances exploration vs. exploitation
- With an admissible heuristic, A\* guarantees finding the **optimal (shortest) path**
- May explore more nodes than Greedy Best-First but produces better solutions

**Implementation:** Custom implementation from scratch using Python's `heapq` module. No external pathfinding libraries used.

---

## 🚧 CSE-Zone Routing Constraint

The following locations form the **CSE zone**:

- CSE Laboratory
- CSE_AKC Seminar Hall
- CSE_Reflexon Room

### Entry Rule

To enter a CSE-labelled location, the route must follow:

```
Tower 2 Front/Rear Entry → Lift Area → CSE locations
```

### Inside the CSE Zone

Once the Lift Area has been crossed during entry, **only CSE-labelled locations** may be visited until the agent returns to the Lift Area.

### Exit Rule

```
CSE locations → Lift Area → Tower 2 Front/Rear Entry → Other campus locations
```

### Invalid Example

```
Lift → CSE Laboratory → Garden → Library  ❌ (Garden is not a CSE location)
```

### Implementation

The CSE constraint is enforced **directly in the search algorithm's neighbour generation**, not as a post-processing check. The search state includes both the current location and a boolean flag indicating whether the agent is currently inside the CSE zone: `state = (location, in_cse_zone)`. This ensures that both agents naturally respect the constraint during pathfinding.

---

## 📁 Project Structure

```
ai-campus-route-navigator/
│
├── Assignment_X3.pdf          # Problem statement
├── README.md                  # This file
├── campus.json                # Campus graph data
├── results.csv                # Generated experiment results
│
├── src/
│   ├── __init__.py
│   ├── main.py                # CLI entry point
│   ├── campus_map.py          # Graph, heuristic, CSE constraints
│   ├── search.py              # Greedy BFS & A* implementations
│   ├── agents.py              # PATHFINDER & ORBIT agents
│   ├── experiment.py          # Experiment runner & CSV export
│   │
│   └── utils/
│       ├── __init__.py
│       └── errors.py          # Custom exceptions
```

### Module Responsibilities

| Module          | Responsibility                                                                        |
| --------------- | ------------------------------------------------------------------------------------- |
| `campus_map.py` | Graph representation, loading, coordinates, heuristic, CSE-aware neighbour generation |
| `search.py`     | Greedy Best-First Search and A\* Search implementations                               |
| `agents.py`     | PATHFINDER and ORBIT agent classes with validation                                    |
| `experiment.py` | Multi-route experiment runner, metrics collection, CSV export                         |
| `main.py`       | CLI interface (interactive mode + experiment mode)                                    |
| `errors.py`     | Custom exception classes for meaningful error handling                                |

---

## 🚀 How to Run

### Prerequisites

- Python 3.10+ (uses `match` statements and type unions)
- No external dependencies required (uses only Python standard library)

### Interactive Mode

```bash
python -m src.main
```

The program will display available campus locations and prompt:

```
Enter starting location: Reception
Enter destination: Library
```

Both PATHFINDER and ORBIT will find routes and display results.

### Experiment Mode

```bash
python -m src.main --experiment
```

Runs all predefined experiments and saves results to `results.csv`.

---

## 🧪 Experiment Routes

The following source–destination pairs are tested (as specified in the assignment):

| #   | Source          | Destination          | Type           |
| --- | --------------- | -------------------- | -------------- |
| 1   | Reception       | Library              | Ordinary       |
| 2   | Canteen         | New Building 2       | Ordinary       |
| 3   | Entry Gate 1    | CSE Laboratory       | CSE route      |
| 4   | Auditorium Hall | CSE_AKC Seminar Hall | CSE route      |
| 5   | Library         | Canteen              | Ordinary       |
| 6   | Entry Gate 1    | Library              | Ordinary       |
| 7   | Playground      | New Building 1       | Ordinary       |
| 8   | CSE Laboratory  | Canteen              | CSE exit route |

---

## 📊 Results Summary

Results generated by running `python -m src.main --experiment`. Full data in [`results.csv`](results.csv).

### Key Findings

| Route                                  | PATHFINDER Cost | ORBIT Cost | Same Path? |
| -------------------------------------- | --------------- | ---------- | ---------- |
| Reception → Library                    | 340 m           | 340 m      | Yes        |
| Canteen → New Building 2               | 260 m           | 260 m      | Yes        |
| Entry Gate 1 → CSE Laboratory          | 600 m           | 520 m      | **No**     |
| Auditorium Hall → CSE_AKC Seminar Hall | 445 m           | 445 m      | Yes        |
| Library → Canteen                      | 440 m           | 390 m      | **No**     |
| Entry Gate 1 → Library                 | 460 m           | 460 m      | Yes        |
| Playground → New Building 1            | 430 m           | 420 m      | **No**     |
| CSE Laboratory → Canteen               | 450 m           | 430 m      | **No**     |

---

## 🔬 Observations

### 1. Does Greedy Best-First always find the shortest route?

**No.** In 4 out of 8 test cases (Entry Gate 1→CSE Laboratory, Library→Canteen, Playground→New Building 1, CSE Laboratory→Canteen), PATHFINDER found a **more expensive** route than ORBIT. Greedy Best-First only considers the estimated remaining distance h(n), which can mislead it into choosing paths that initially look promising but are actually longer.

### 2. How does A\* use the distance already travelled?

A* uses f(n) = g(n) + h(n), where g(n) is the **actual accumulated cost**. This prevents ORBIT from being misled by the heuristic alone — even if a node appears close to the destination, A* will avoid it if reaching that node requires a very long detour.

### 3. When do the two agents choose different paths?

The agents choose different paths when the graph has multiple routes where the heuristically promising direction is not the shortest. For example, on the Library→Canteen route, PATHFINDER went through Lift Area and Tower 2 (which are heuristically closer to Canteen) while ORBIT found the shorter path through Garden Area and CRNN Centre.

### 4. How does the heuristic affect their behaviour?

The Euclidean distance heuristic gives a reasonable estimate but can mislead Greedy Best-First when a straight-line direction doesn't correspond to the actual shortest walking path. A\* compensates by also tracking actual distance travelled, making it less susceptible to heuristic inaccuracy.

### 5. What happens when the CSE constraint restricts possible routes?

The CSE constraint creates a strict routing bottleneck because agents must enter through `Tower 2 Front/Rear Entry → Lift Area`. This exposes a major weakness in PATHFINDER (Greedy BFS). Because PATHFINDER only looks at straight-line distance, it may path towards the CSE building (e.g., via Garden Area), hit the constraint boundary, and be forced to inefficiently backtrack to a valid entry point (as seen in the *Entry Gate 1 → CSE Laboratory* route, taking 600m). ORBIT (A*), tracking total cost, successfully plans ahead to route through the correct entry point from the start (taking 520m).

---

## ⚠️ Limitations & Assumptions

- **Distance values are approximate** — based on visual estimation from the satellite map, not surveyed measurements.
- **Coordinate positions are approximate** — used for heuristic calculation, not for display.
- **Walking paths** — the graph assumes direct walkable connections between adjacent buildings; actual campus paths may differ slightly.
- **Euclidean heuristic** — assumes roughly open terrain; indoor routing or building obstacles are not modelled.
