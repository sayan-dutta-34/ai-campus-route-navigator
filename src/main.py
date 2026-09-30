"""
AI Campus Route Navigator — Main Entry Point
=============================================
Provides a CLI interface for:
  1. Interactive routing: user enters source and destination
  2. Running predefined experiments and saving results to CSV

Usage:
    python -m src.main                # Interactive mode
    python -m src.main --experiment   # Run all experiments
"""

import sys
import argparse
from pathlib import Path

from src.campus_map import load_campus_graph
from src.agents import Pathfinder, Orbit
from src.experiment import ExperimentRunner
from src.utils.errors import NavigatorError


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CAMPUS_JSON = Path(__file__).resolve().parent.parent / "campus.json"
RESULTS_CSV = Path(__file__).resolve().parent.parent / "results.csv"


# ---------------------------------------------------------------------------
# Interactive mode
# ---------------------------------------------------------------------------

def interactive_mode() -> None:
    """Run the interactive CLI where users enter source and destination."""
    print("\n" + "=" * 60)
    print("  🗺️  AI CAMPUS ROUTE NAVIGATOR")
    print("  CU Technology Campus")
    print("=" * 60)

    # Load graph
    try:
        graph = load_campus_graph(CAMPUS_JSON)
    except NavigatorError as e:
        print(f"\n❌ Error loading campus data: {e}")
        sys.exit(1)

    # Create agents
    pathfinder = Pathfinder(graph)
    orbit = Orbit(graph)

    # Show available locations
    locations = graph.get_locations()
    print("\n📍 Available campus locations:")
    for i, loc in enumerate(locations, 1):
        print(f"   {i:2d}. {loc}")

    while True:
        print(f"\n{'─' * 50}")
        source_input = input("\n  Enter starting location (name or number, or 'quit'): ").strip()
        if source_input.lower() in ("quit", "exit", "q"):
            print("\n  Goodbye! 👋\n")
            break

        dest_input = input("  Enter destination (name or number): ").strip()
        if dest_input.lower() in ("quit", "exit", "q"):
            print("\n  Goodbye! 👋\n")
            break

        # Helper to resolve input to location name
        def resolve_location(user_input: str) -> str:
            if user_input.isdigit():
                idx = int(user_input) - 1
                if 0 <= idx < len(locations):
                    return locations[idx]
            return user_input

        source = resolve_location(source_input)
        destination = resolve_location(dest_input)

        print(f"\n{'─' * 50}")
        print(f"  Routing: {source} → {destination}")
        print(f"{'─' * 50}")

        # Run PATHFINDER
        print(f"\n  🤖 PATHFINDER (Greedy Best-First Search)")
        try:
            pf_result = pathfinder.find_route(source, destination)
            print(f"     Route: {pf_result.format_path()}")
            print(f"     Cost:  {pf_result.total_cost:.1f} m")
            print(f"     Nodes explored: {pf_result.nodes_explored}")
            print(f"     Time:  {pf_result.execution_time:.6f} s")
        except NavigatorError as e:
            print(f"     ❌ {e}")
            pf_result = None

        # Run ORBIT
        print(f"\n  🤖 ORBIT (A* Search)")
        try:
            orbit_result = orbit.find_route(source, destination)
            print(f"     Route: {orbit_result.format_path()}")
            print(f"     Cost:  {orbit_result.total_cost:.1f} m")
            print(f"     Nodes explored: {orbit_result.nodes_explored}")
            print(f"     Time:  {orbit_result.execution_time:.6f} s")
        except NavigatorError as e:
            print(f"     ❌ {e}")
            orbit_result = None

        # Quick comparison
        if pf_result and orbit_result:
            print(f"\n  📊 Quick Comparison:")
            same = pf_result.path == orbit_result.path
            print(f"     Same path: {'Yes' if same else 'No'}")
            print(f"     Cost — PATHFINDER: {pf_result.total_cost:.1f} m, "
                  f"ORBIT: {orbit_result.total_cost:.1f} m")
            print(f"     Nodes — PATHFINDER: {pf_result.nodes_explored}, "
                  f"ORBIT: {orbit_result.nodes_explored}")


# ---------------------------------------------------------------------------
# Experiment mode
# ---------------------------------------------------------------------------

def experiment_mode() -> None:
    """Run predefined experiments and save results to CSV."""
    print("\n" + "=" * 60)
    print("  🧪 RUNNING ROUTE EXPERIMENTS")
    print("=" * 60)

    runner = ExperimentRunner(CAMPUS_JSON)
    results = runner.run_all()

    runner.print_results(results)
    runner.save_results(results, RESULTS_CSV)

    print(f"  ✅ Results saved to: {RESULTS_CSV}")
    print()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Parse arguments and run the appropriate mode."""
    parser = argparse.ArgumentParser(
        description="AI Campus Route Navigator — CU Technology Campus",
    )
    parser.add_argument(
        "--experiment",
        action="store_true",
        help="Run predefined route experiments and save results to CSV",
    )
    args = parser.parse_args()

    if args.experiment:
        experiment_mode()
    else:
        interactive_mode()


if __name__ == "__main__":
    main()
