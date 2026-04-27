"""Discovery engine for Mycelium."""
"""Discovery engine for Mycelium."""

try:
    from mycelium.discovery.semantic import SemanticSearchEngine
    __all__ = ["SemanticSearchEngine"]
except ImportError:
    __all__ = []