"""
Experiment Module
=================
Runs multiple source-destination experiments using both PATHFINDER and
ORBIT agents, collects metrics, and saves results to CSV.
"""

import csv
from dataclasses import dataclass
from pathlib import Path

from src.campus_map import CampusGraph, load_campus_graph
from src.agents import Pathfinder, Orbit
from src.search import SearchResult
from src.utils.errors import NavigatorError


# ---------------------------------------------------------------------------
# Experiment route definition
# ---------------------------------------------------------------------------

# Predefined experiment routes from the assignment
EXPERIMENT_ROUTES: list[tuple[str, str]] = [
    ("Reception", "Library"),
    ("Canteen", "New Building 2"),
    ("Entry Gate 1", "CSE Laboratory"),
    ("Auditorium Hall", "CSE_AKC Seminar Hall"),
    ("Library", "Canteen"),
    ("Entry Gate 1", "Library"),
    ("Playground", "New Building 1"),
    ("CSE Laboratory", "Canteen"),
]


# ---------------------------------------------------------------------------
# Experiment result
# ---------------------------------------------------------------------------

@dataclass
class ExperimentResult:
    """Result of running both agents on a single route."""
    source: str
    destination: str
    pathfinder_result: SearchResult | None
    orbit_result: SearchResult | None
    pathfinder_error: str
    orbit_error: str


# ---------------------------------------------------------------------------
# Experiment runner
# ---------------------------------------------------------------------------

class ExperimentRunner:
    """
    Runs routing experiments comparing PATHFINDER and ORBIT.

    Usage:
        runner = ExperimentRunner()
        results = runner.run_all()
        runner.save_results(results, "results.csv")
        runner.print_results(results)
    """

    def __init__(self, campus_json_path: str | Path = "campus.json"):
        self.graph = load_campus_graph(campus_json_path)
        self.pathfinder = Pathfinder(self.graph)
        self.orbit = Orbit(self.graph)

    def run_single(self, source: str, destination: str) -> ExperimentResult:
        """Run both agents on a single source → destination route."""
        pf_result: SearchResult | None = None
        pf_error = ""
        orbit_result: SearchResult | None = None
        orbit_error = ""

        # Run PATHFINDER
        try:
            pf_result = self.pathfinder.find_route(source, destination)
        except NavigatorError as e:
            pf_error = str(e)

        # Run ORBIT
        try:
            orbit_result = self.orbit.find_route(source, destination)
        except NavigatorError as e:
            orbit_error = str(e)

        return ExperimentResult(
            source=source,
            destination=destination,
            pathfinder_result=pf_result,
            orbit_result=orbit_result,
            pathfinder_error=pf_error,
            orbit_error=orbit_error,
        )

    def run_all(
        self, routes: list[tuple[str, str]] | None = None
    ) -> list[ExperimentResult]:
        """Run experiments on all predefined or supplied routes."""
        if routes is None:
            routes = EXPERIMENT_ROUTES

        results: list[ExperimentResult] = []
        for source, destination in routes:
            result = self.run_single(source, destination)
            results.append(result)

        return results

    @staticmethod
    def save_results(
        results: list[ExperimentResult],
        filepath: str | Path = "results.csv",
    ) -> None:
        """Save experiment results to a CSV file."""
        filepath = Path(filepath)

        headers = [
            "Route",
            "Agent",
            "Path",
            "Cost",
            "Nodes Explored",
            "Time (s)",
            "Status",
        ]

        rows: list[list[str]] = []
        for result in results:
            route_label = f"{result.source} → {result.destination}"

            # PATHFINDER row
            if result.pathfinder_result and result.pathfinder_result.success:
                r = result.pathfinder_result
                rows.append([
                    route_label,
                    "PATHFINDER",
                    r.format_path(),
                    f"{r.total_cost:.1f}",
                    str(r.nodes_explored),
                    f"{r.execution_time:.6f}",
                    "Success",
                ])
            else:
                rows.append([
                    route_label,
                    "PATHFINDER",
                    "N/A",
                    "N/A",
                    "N/A",
                    "N/A",
                    f"Failed: {result.pathfinder_error}",
                ])

            # ORBIT row
            if result.orbit_result and result.orbit_result.success:
                r = result.orbit_result
                rows.append([
                    route_label,
                    "ORBIT",
                    r.format_path(),
                    f"{r.total_cost:.1f}",
                    str(r.nodes_explored),
                    f"{r.execution_time:.6f}",
                    "Success",
                ])
            else:
                rows.append([
                    route_label,
                    "ORBIT",
                    "N/A",
                    "N/A",
                    "N/A",
                    "N/A",
                    f"Failed: {result.orbit_error}",
                ])

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)

    @staticmethod
    def print_results(results: list[ExperimentResult]) -> None:
        """Print experiment results in a readable format."""
        print("\n" + "=" * 80)
        print("  EXPERIMENT RESULTS — PATHFINDER vs ORBIT")
        print("=" * 80)

        for i, result in enumerate(results, 1):
            print(f"\n{'─' * 70}")
            print(f"  Route {i}: {result.source} → {result.destination}")
            print(f"{'─' * 70}")

            _print_agent_result(
                "PATHFINDER",
                result.pathfinder_result,
                result.pathfinder_error,
            )
            _print_agent_result(
                "ORBIT",
                result.orbit_result,
                result.orbit_error,
            )

            # Comparison
            if (result.pathfinder_result and result.pathfinder_result.success
                    and result.orbit_result and result.orbit_result.success):
                pf = result.pathfinder_result
                orb = result.orbit_result
                same_path = pf.path == orb.path
                print(f"\n  📊 Comparison:")
                print(f"     Same path: {'Yes' if same_path else 'No'}")
                print(f"     Cost difference: "
                      f"{abs(pf.total_cost - orb.total_cost):.1f} m")
                if pf.total_cost < orb.total_cost:
                    print(f"     Lower cost: PATHFINDER")
                elif orb.total_cost < pf.total_cost:
                    print(f"     Lower cost: ORBIT")
                else:
                    print(f"     Lower cost: Same cost")

        print(f"\n{'=' * 80}\n")


def _print_agent_result(
    agent_name: str,
    result: SearchResult | None,
    error: str,
) -> None:
    """Pretty-print a single agent's result."""
    print(f"\n  🤖 {agent_name}")
    if result and result.success:
        print(f"     Route: {result.format_path()}")
        print(f"     Cost:  {result.total_cost:.1f} m")
        print(f"     Nodes explored: {result.nodes_explored}")
        print(f"     Time:  {result.execution_time:.6f} s")
    else:
        print(f"     ❌ Failed: {error}")
