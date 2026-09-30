"""
Agents Module
=============
Defines the two AI routing agents:
  - PATHFINDER: uses Greedy Best-First Search
  - ORBIT:      uses A* Search

Both agents share the same campus graph and heuristic. The difference
lies solely in their search strategy.
"""

from src.campus_map import CampusGraph
from src.search import SearchResult, greedy_best_first_search, astar_search
from src.utils.errors import (
    InvalidLocationError,
    InvalidRouteRequestError,
)


class _BaseAgent:
    """
    Base class for campus routing agents.

    Provides shared validation logic. Subclasses must set `name` and
    `algorithm_name` and implement `_search()`.
    """

    name: str = ""
    algorithm_name: str = ""

    def __init__(self, graph: CampusGraph):
        self.graph = graph

    def find_route(self, source: str, destination: str) -> SearchResult:
        """
        Find a route from *source* to *destination*.

        Validates input locations, then delegates to the subclass
        search implementation.
        """
        self._validate(source, destination)
        return self._search(source, destination)

    def _validate(self, source: str, destination: str) -> None:
        """Validate that source and destination are valid locations."""
        if not self.graph.has_location(source):
            raise InvalidLocationError(source, self.graph.get_locations())
        if not self.graph.has_location(destination):
            raise InvalidLocationError(destination, self.graph.get_locations())
        if source == destination:
            raise InvalidRouteRequestError(
                f"Source and destination are the same: '{source}'"
            )

    def _search(self, source: str, destination: str) -> SearchResult:
        """Execute the search algorithm. Must be overridden."""
        raise NotImplementedError


class Pathfinder(_BaseAgent):
    """
    PATHFINDER agent — uses Greedy Best-First Search.

    At each step, PATHFINDER expands the node that appears closest to
    the destination based on h(n), without considering the distance
    already travelled.

    f(n) = h(n)
    """

    name = "PATHFINDER"
    algorithm_name = "Greedy Best-First Search"

    def _search(self, source: str, destination: str) -> SearchResult:
        return greedy_best_first_search(self.graph, source, destination)


class Orbit(_BaseAgent):
    """
    ORBIT agent — uses A* Search.

    ORBIT considers both the actual cost travelled g(n) and the
    estimated remaining cost h(n) to make routing decisions.

    f(n) = g(n) + h(n)
    """

    name = "ORBIT"
    algorithm_name = "A* Search"

    def _search(self, source: str, destination: str) -> SearchResult:
        return astar_search(self.graph, source, destination)
