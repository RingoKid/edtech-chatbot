from __future__ import annotations

from typing import Callable, Dict

from app.graph.nodes import generate_lesson_node
from app.graph.state import GraphState


END = "END"


def create_graph() -> Dict[str, Callable[[GraphState], GraphState]]:
    """A lightweight placeholder graph mapping for local runs/tests.

    Real deployment may build a LangGraph; this keeps the contract simple.
    """
    return {
        "generate_lesson": generate_lesson_node,  # routes directly after params collected
        END: lambda s: s,
    }


