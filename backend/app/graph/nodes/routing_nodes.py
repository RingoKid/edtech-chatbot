# backend/app/graph/nodes/routing_nodes.py

from langchain_core.language_models import BaseLanguageModel
from langchain_core.messages import AIMessage, SystemMessage
from app.graph.state import State
from app.schemas.routing import Route
from app.prompts.routing import ROUTER_SYSTEM_PROMPT, GREETING_MESSAGE

def greeting_node(state: State) -> dict:
    """Greets the user and asks them to choose a task."""
    # Check if greeting has already been sent (check for AI messages in history)
    has_greeting = any(isinstance(msg, AIMessage) and "AI assistant for lesson planning" in msg.content
                       for msg in state["messages"])

    if has_greeting:
        # Already greeted, skip
        return {}

    # Return the greeting message
    return {
        "messages": [
            AIMessage(content=GREETING_MESSAGE)
        ]
    }

class Router:
    def __init__(self, model: BaseLanguageModel):
        # Pre-configure the model with the tool and system prompt for efficiency
        self.model = model.bind_tools([Route])

    def route(self, state: State) -> dict:
        """Determines the user's desired task and updates the state with a route."""
        messages = state["messages"]
        last_message = messages[-1]

        system_prompt = SystemMessage(content=ROUTER_SYSTEM_PROMPT)
        response = self.model.invoke([system_prompt, last_message])

        # Default to the 'general' route if the model fails to classify
        task = "general"
        if response.tool_calls:
            tool_call = response.tool_calls[0]
            task = tool_call["args"]["task"]

        return {"route": task}
