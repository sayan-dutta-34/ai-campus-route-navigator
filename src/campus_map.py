"""
Campus Map Module
=================
Handles loading the campus graph from campus.json, representing it as a
weighted undirected graph, and providing heuristic computation for the
search algorithms.
"""

import json
import math
from dataclasses import dataclass, field
from pathlib import Path

from src.utils.errors import InvalidGraphError, InvalidLocationError


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Coordinate:
    """2D coordinate for a campus location (approximate, in meters)."""
    x: float
    y: float

    def euclidean_distance(self, other: "Coordinate") -> float:
        """Compute Euclidean distance to another coordinate."""
        return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)


@dataclass
class CampusGraph:
    """
    Weighted undirected graph representing the CU Technology Campus.

    Attributes:
        nodes: mapping of location name → Coordinate
        adjacency: mapping of location → list of (neighbour, weight)
        cse_zone: set of CSE-zone location names
        cse_entry_points: set of entry/exit locations for the CSE zone
                          (Tower 2 Front Entry / Tower 2 Rear Entry)
        cse_transition_node: the node that bridges entry points and CSE zone
                             (Lift Area)
    """
    nodes: dict[str, Coordinate] = field(default_factory=dict)
    adjacency: dict[str, list[tuple[str, int]]] = field(default_factory=dict)
    cse_zone: set[str] = field(default_factory=set)
    cse_entry_points: set[str] = field(default_factory=set)
    cse_transition_node: str = ""
    # Conservative factor that keeps coordinate distance admissible.
    heuristic_scale: float = 1.0

    # ------------------------------------------------------------------
    # Graph queries
    # ------------------------------------------------------------------

    def get_locations(self) -> list[str]:
        """Return a sorted list of all campus location names."""
        return sorted(self.nodes.keys())

    def has_location(self, name: str) -> bool:
        """Check whether a location exists in the graph."""
        return name in self.nodes

    def get_neighbours(self, location: str) -> list[tuple[str, int]]:
        """Return neighbours of *location* as [(neighbour, weight), ...]."""
        if location not in self.adjacency:
            raise InvalidLocationError(location, self.get_locations())
        return self.adjacency[location]

    def is_cse_location(self, location: str) -> bool:
        """Return True if *location* belongs to the CSE zone."""
        return location in self.cse_zone

    # ------------------------------------------------------------------
    # CSE-zone aware neighbour generation
    # ------------------------------------------------------------------

    def get_valid_neighbours(
        self,
        location: str,
        in_cse_zone: bool,
        cse_entry_authorized: bool = False,
    ) -> list[tuple[str, int, bool]]:
        """
        Return valid neighbours considering the CSE routing constraint.

        The CSE routing rule:
        - To ENTER the CSE zone, one must pass through a CSE entry point
          (Tower 2 Front/Rear Entry) → Lift Area → CSE locations.
        - Once inside the CSE zone (past Lift Area), only CSE locations
          and Lift Area are reachable.
        - To EXIT, one must return to Lift Area first, then to an entry
          point, then to the rest of campus.

        Parameters:
            location:    current location name
            in_cse_zone: whether the agent is currently inside the CSE zone
            cse_entry_authorized: whether the current Lift Area visit came
                directly from a Tower 2 entry point

        Returns:
            List of (neighbour, weight, new_in_cse_zone) tuples.
        """
        raw_neighbours = self.get_neighbours(location)
        valid: list[tuple[str, int, bool]] = []

        for neighbour, weight in raw_neighbours:
            # ---- Currently INSIDE the CSE zone ----
            if in_cse_zone:
                if self.is_cse_location(neighbour):
                    # Can move between CSE locations freely
                    valid.append((neighbour, weight, True))
                elif neighbour == self.cse_transition_node:
                    # Can return to Lift Area (exit path begins)
                    valid.append((neighbour, weight, False))
                # All other locations are BLOCKED while in CSE zone

            # ---- Currently OUTSIDE the CSE zone ----
            else:
                if self.is_cse_location(neighbour):
                    # Can only enter CSE zone from Lift Area
                    if (
                        location == self.cse_transition_node
                        and cse_entry_authorized
                    ):
                        valid.append((neighbour, weight, True))
                    # Otherwise, skip this CSE neighbour (invalid entry)
                else:
                    # Normal (non-CSE) neighbour: always reachable
                    authorized = (
                        location in self.cse_entry_points
                        and neighbour == self.cse_transition_node
                    )
                    valid.append((neighbour, weight, authorized))

        return valid

    # ------------------------------------------------------------------
    # Heuristic
    # ------------------------------------------------------------------

    def heuristic(self, location: str, destination: str) -> float:
        """
        Compute the heuristic h(n): estimated remaining cost from
        *location* to *destination*.

        Uses a conservatively scaled Euclidean (straight-line) distance
        between the two locations' coordinates. The scale accounts for
        the approximate coordinate and edge-weight units and keeps the
        heuristic admissible for this graph.
        """
        if location not in self.nodes:
            raise InvalidLocationError(location, self.get_locations())
        if destination not in self.nodes:
            raise InvalidLocationError(destination, self.get_locations())

        return (
            self.nodes[location].euclidean_distance(self.nodes[destination])
            * self.heuristic_scale
        )


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def load_campus_graph(filepath: str | Path = "campus.json") -> CampusGraph:
    """
    Load the campus graph from a JSON file.

    Expected JSON structure:
        {
            "nodes": { "Name": {"x": float, "y": float}, ... },
            "edges": [ {"from": "A", "to": "B", "weight": int}, ... ],
            "cse_zone": ["CSE Laboratory", ...],
            "cse_entry_points": ["Tower 2 Front Entry", ...],
            "cse_transition_node": "Lift Area"
        }
    """
    filepath = Path(filepath)
    if not filepath.exists():
        raise InvalidGraphError(f"Campus data file not found: {filepath}")

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as exc:
        raise InvalidGraphError(f"Invalid JSON in {filepath}: {exc}") from exc

    # --- Validate required keys ---
    required_keys = {"nodes", "edges", "cse_zone", "cse_entry_points", "cse_transition_node"}
    missing = required_keys - set(data.keys())
    if missing:
        raise InvalidGraphError(f"Missing keys in campus data: {missing}")

    # --- Build nodes ---
    nodes: dict[str, Coordinate] = {}
    for name, coords in data["nodes"].items():
        if "x" not in coords or "y" not in coords:
            raise InvalidGraphError(f"Node '{name}' missing x/y coordinates")
        nodes[name] = Coordinate(x=float(coords["x"]), y=float(coords["y"]))

    # --- Build adjacency list (undirected graph) ---
    adjacency: dict[str, list[tuple[str, int]]] = {name: [] for name in nodes}

    for edge in data["edges"]:
        src = edge.get("from", "")
        dst = edge.get("to", "")
        weight = edge.get("weight", 0)

        if src not in nodes:
            raise InvalidGraphError(f"Edge references unknown node: '{src}'")
        if dst not in nodes:
            raise InvalidGraphError(f"Edge references unknown node: '{dst}'")
        if weight <= 0:
            raise InvalidGraphError(
                f"Edge weight must be positive: {src} -> {dst} = {weight}"
            )

        adjacency[src].append((dst, int(weight)))
        adjacency[dst].append((src, int(weight)))

    # --- CSE zone data ---
    cse_zone = set(data["cse_zone"])
    cse_entry_points = set(data["cse_entry_points"])
    cse_transition_node = data["cse_transition_node"]

    # Validate CSE locations exist in nodes
    for loc in cse_zone | cse_entry_points | {cse_transition_node}:
        if loc not in nodes:
            raise InvalidGraphError(
                f"CSE configuration references unknown location: '{loc}'"
            )

    heuristic_scale = 1.0
    for source, neighbours in adjacency.items():
        for destination, weight in neighbours:
            coordinate_distance = nodes[source].euclidean_distance(
                nodes[destination]
            )
            if coordinate_distance > 0:
                heuristic_scale = min(
                    heuristic_scale, weight / coordinate_distance
                )

    graph = CampusGraph(
        nodes=nodes,
        adjacency=adjacency,
        cse_zone=cse_zone,
        cse_entry_points=cse_entry_points,
        cse_transition_node=cse_transition_node,
        heuristic_scale=heuristic_scale,
    )

    return graph
