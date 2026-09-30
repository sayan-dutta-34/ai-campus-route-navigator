"""Custom exceptions for the AI Campus Route Navigator."""


class NavigatorError(Exception):
    """Base exception for the campus navigator."""
    pass


class InvalidLocationError(NavigatorError):
    """Raised when a location is not found in the campus graph."""

    def __init__(self, location: str, available: list[str] | None = None):
        self.location = location
        self.available = available or []
        msg = f"Unknown location: '{location}'"
        if self.available:
            msg += f". Available locations: {', '.join(sorted(self.available))}"
        super().__init__(msg)


class InvalidGraphError(NavigatorError):
    """Raised when the campus graph data is invalid or corrupt."""
    pass


class RouteNotFoundError(NavigatorError):
    """Raised when no valid route exists between source and destination."""

    def __init__(self, source: str, destination: str, reason: str = ""):
        self.source = source
        self.destination = destination
        msg = f"No valid route from '{source}' to '{destination}'"
        if reason:
            msg += f": {reason}"
        super().__init__(msg)


class InvalidRouteRequestError(NavigatorError):
    """Raised when a route request is invalid (e.g., source == destination)."""
    pass
