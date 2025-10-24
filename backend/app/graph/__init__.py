"""
Backward compatibility module for graph imports.
All graphs have been migrated to app.chatbot/ structure.
"""
from app.chatbot.specialists.handwriting.graph import handwriting_graph

# Default graph for backwards compatibility - use handwriting_graph
graph = handwriting_graph

__all__ = ["graph", "handwriting_graph"]
