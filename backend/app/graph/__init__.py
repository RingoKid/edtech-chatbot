from app.graph.graph import graph as lesson_planner_graph
from app.graph.handwriting_graph import handwriting_graph

# Temporarily disable routing_graph import due to LangGraph installation issue
# from app.graph.routing_graph import routing_graph

# Default graph for backwards compatibility - temporarily use handwriting_graph
graph = handwriting_graph

__all__ = ["graph", "lesson_planner_graph", "handwriting_graph"]
