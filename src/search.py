"""
Search Module
=============
Implements Greedy Best-First Search and A* Search from scratch.
Both algorithms use a priority queue (min-heap) and respect the
CSE-zone routing constraint through state-aware neighbour generation.
"""

import heapq
import time
from dataclasses import dataclass, field

from src.campus_map import CampusGraph
from src.utils.errors import RouteNotFoundError


# ---------------------------------------------------------------------------
# Search result
# ---------------------------------------------------------------------------

@dataclass
class SearchResult:
    """
    Structured result returned by both search algorithms.

    Attributes:
        path:           ordered list of location names from source to destination
        total_cost:     actual accumulated edge-weight cost of the path
        nodes_explored: number of nodes expanded during search
        execution_time: wall-clock search time in seconds
        success:        whether a valid route was found
        algorithm:      name of the search algorithm used
    """
    path: list[str] = field(default_factory=list)
    total_cost: float = 0.0
    nodes_explored: int = 0
    execution_time: float = 0.0
    success: bool = False
    algorithm: str = ""

    def format_path(self) -> str:
        """Return a human-readable path string like 'A → B → C'."""
        if not self.path:
            return "No path found"
        return " → ".join(self.path)


# ---------------------------------------------------------------------------
# Search state
# ---------------------------------------------------------------------------

@dataclass(frozen=True, order=True)
class _SearchState:
    """
    Internal search state for the priority queue.

    The state tracks:
      - priority (f-value for ordering in the heap)
      - counter  (tie-breaker for insertion order)
      - location (current node name)
    - in_cse   (whether we are inside the CSE zone)
    - cse_entry_authorized (whether Lift Area was reached from an entry)
    """
    priority: float
    counter: int = field(compare=True)
    location: str = field(compare=False)
    in_cse: bool = field(compare=False)
    cse_entry_authorized: bool = field(compare=False)


# ---------------------------------------------------------------------------
# Greedy Best-First Search
# ---------------------------------------------------------------------------

def greedy_best_first_search(
    graph: CampusGraph,
    source: str,
    destination: str,
) -> SearchResult:
    """
    Greedy Best-First Search: f(n) = h(n)

    Expands the node that appears closest to the destination according to
    the heuristic, without considering the cost already travelled.

    Parameters:
        graph:       the campus graph
        source:      starting location name
        destination: goal location name

    Returns:
        SearchResult with the found path and metrics.

    Raises:
        RouteNotFoundError: if no valid path exists.
    """
    start_time = time.perf_counter()
    counter = 0  # tie-breaker for equal priorities

    # Determine initial CSE state
    source_in_cse = graph.is_cse_location(source)

    # Priority queue: (f-value, counter, location, CSE state flags)
    initial_h = graph.heuristic(source, destination)
    start_state = _SearchState(
        priority=initial_h,
        counter=counter,
        location=source,
        in_cse=source_in_cse,
        cse_entry_authorized=False,
    )
    frontier: list[_SearchState] = [start_state]

    # Visited: (location, in_cse) → True
    visited: set[tuple[str, bool, bool]] = set()

    # Parent tracking: (location, in_cse) → (parent_location, parent_in_cse)
    parent: dict[tuple[str, bool, bool], tuple[str, bool, bool] | None] = {
        (source, source_in_cse, False): None
    }

    # Cost tracking: (location, in_cse) → actual cost to reach
    cost_so_far: dict[tuple[str, bool, bool], float] = {
        (source, source_in_cse, False): 0.0
    }

    nodes_explored = 0

    while frontier:
        current = heapq.heappop(frontier)
        state_key = (
            current.location,
            current.in_cse,
            current.cse_entry_authorized,
        )

        # Skip if already visited
        if state_key in visited:
            continue

        visited.add(state_key)
        nodes_explored += 1

        # Goal check
        if current.location == destination:
            # Reconstruct path
            path = _reconstruct_path(parent, state_key)
            elapsed = time.perf_counter() - start_time
            return SearchResult(
                path=path,
                total_cost=cost_so_far[state_key],
                nodes_explored=nodes_explored,
                execution_time=elapsed,
                success=True,
                algorithm="Greedy Best-First Search",
            )

        # Expand neighbours (CSE-aware)
        for neighbour, weight, new_in_cse in graph.get_valid_neighbours(
            current.location,
            current.in_cse,
            current.cse_entry_authorized,
        ):
            new_entry_authorized = (
                not new_in_cse
                and current.location in graph.cse_entry_points
                and neighbour == graph.cse_transition_node
            )
            neighbour_key = (neighbour, new_in_cse, new_entry_authorized)
            if neighbour_key in visited:
                continue

            new_cost = cost_so_far[state_key] + weight

            # Greedy: only use h(n) for priority
            if neighbour_key not in cost_so_far or new_cost < cost_so_far[neighbour_key]:
                cost_so_far[neighbour_key] = new_cost
                parent[neighbour_key] = state_key
                counter += 1
                h = graph.heuristic(neighbour, destination)
                new_state = _SearchState(
                    priority=h,
                    counter=counter,
                    location=neighbour,
                    in_cse=new_in_cse,
                    cse_entry_authorized=new_entry_authorized,
                )
                heapq.heappush(frontier, new_state)

    # No path found
    elapsed = time.perf_counter() - start_time
    raise RouteNotFoundError(source, destination, "No valid path exists")


# ---------------------------------------------------------------------------
# A* Search
# ---------------------------------------------------------------------------

def astar_search(
    graph: CampusGraph,
    source: str,
    destination: str,
) -> SearchResult:
    """
    A* Search: f(n) = g(n) + h(n)

    Considers both the actual cost travelled so far g(n) and the
    estimated remaining cost h(n) to find an optimal path.

    Parameters:
        graph:       the campus graph
        source:      starting location name
        destination: goal location name

    Returns:
        SearchResult with the found path and metrics.

    Raises:
        RouteNotFoundError: if no valid path exists.
    """
    start_time = time.perf_counter()
    counter = 0

    source_in_cse = graph.is_cse_location(source)

    initial_h = graph.heuristic(source, destination)
    start_state = _SearchState(
        priority=0.0 + initial_h,  # f = g + h, g=0 at start
        counter=counter,
        location=source,
        in_cse=source_in_cse,
        cse_entry_authorized=False,
    )
    frontier: list[_SearchState] = [start_state]

    visited: set[tuple[str, bool, bool]] = set()

    parent: dict[tuple[str, bool, bool], tuple[str, bool, bool] | None] = {
        (source, source_in_cse, False): None
    }

    # g(n): actual cost from source to each state
    g_cost: dict[tuple[str, bool, bool], float] = {
        (source, source_in_cse, False): 0.0
    }

    nodes_explored = 0

    while frontier:
        current = heapq.heappop(frontier)
        state_key = (
            current.location,
            current.in_cse,
            current.cse_entry_authorized,
        )

        if state_key in visited:
            continue

        visited.add(state_key)
        nodes_explored += 1

        # Goal check
        if current.location == destination:
            path = _reconstruct_path(parent, state_key)
            elapsed = time.perf_counter() - start_time
            return SearchResult(
                path=path,
                total_cost=g_cost[state_key],
                nodes_explored=nodes_explored,
                execution_time=elapsed,
                success=True,
                algorithm="A* Search",
            )

        # Expand neighbours (CSE-aware)
        for neighbour, weight, new_in_cse in graph.get_valid_neighbours(
            current.location,
            current.in_cse,
            current.cse_entry_authorized,
        ):
            new_entry_authorized = (
                not new_in_cse
                and current.location in graph.cse_entry_points
                and neighbour == graph.cse_transition_node
            )
            neighbour_key = (neighbour, new_in_cse, new_entry_authorized)
            if neighbour_key in visited:
                continue

            tentative_g = g_cost[state_key] + weight

            # Only expand if we found a cheaper path to this state
            if neighbour_key not in g_cost or tentative_g < g_cost[neighbour_key]:
                g_cost[neighbour_key] = tentative_g
                parent[neighbour_key] = state_key

                h = graph.heuristic(neighbour, destination)
                f = tentative_g + h  # f(n) = g(n) + h(n)

                counter += 1
                new_state = _SearchState(
                    priority=f,
                    counter=counter,
                    location=neighbour,
                    in_cse=new_in_cse,
                    cse_entry_authorized=new_entry_authorized,
                )
                heapq.heappush(frontier, new_state)

    elapsed = time.perf_counter() - start_time
    raise RouteNotFoundError(source, destination, "No valid path exists")


# ---------------------------------------------------------------------------
# Path reconstruction helper
# ---------------------------------------------------------------------------

def _reconstruct_path(
    parent: dict[tuple[str, bool, bool], tuple[str, bool, bool] | None],
    goal_key: tuple[str, bool, bool],
) -> list[str]:
    """
    Reconstruct the path from source to goal using the parent map.
    Returns a list of location names in order [source, ..., goal].
    """
    path: list[str] = []
    current: tuple[str, bool, bool] | None = goal_key

    while current is not None:
        path.append(current[0])  # location name
        current = parent.get(current)

    path.reverse()
    return path
