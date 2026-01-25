"""
Routing Agent - ReAct agent for greeting and routing users to task agents.

Uses create_react_agent from langgraph.prebuilt for natural conversation flow.
The agent can ask clarifying questions when intent is ambiguous.
"""

from langchain_core.tools import tool
from langchain.agents import create_agent

from app.llm.client import get_chat_model
from app.langfuse.client import get_langfuse_client
from app.graph.state import GraphState


# Default prompt used when Langfuse is unavailable or prompt doesn't exist
DEFAULT_ROUTING_PROMPT = """You are a friendly lesson planning assistant for preschool teachers.

Your job is to:
1. Greet users warmly when they say hello
2. Ask what type of lesson they want to create
3. Route them to the appropriate lesson type when their intent is clear

Available lesson types:
- **Handwriting**: Letter formation, tracing letters, fine motor skills practice, writing practice
- **Vocabulary**: Word lists, vocabulary building activities, teaching new words
- **Idea Generation**: Brainstorming lesson ideas, activity suggestions, creative concepts, "give me ideas"

IMPORTANT ROUTING RULES:
- If the user mentions "handwriting", "letter", "tracing letters", or "writing practice" → Use route_to_handwriting
- If the user mentions "vocabulary", "vocab", "words", "word list" → Use route_to_vocabulary
- If the user mentions "ideas", "brainstorm", "activities", "suggestions", "concepts", or asks for help coming up with lessons → Use route_to_idea_generation
- Only ask for clarification when the user's request could genuinely fit multiple categories equally

Guidelines:
- Keep responses concise and friendly
- When in doubt between idea generation and another category, prefer routing to idea generation if the user seems to want suggestions
- If the user asks about something outside these three areas, politely explain what you can help with

Example routing decisions:
- "hi" → Greet them (don't route yet)
- "help with letter A" → route_to_handwriting (letter = handwriting)
- "vocabulary words for PreK" → route_to_vocabulary
- "give me some ideas" → route_to_idea_generation
- "brainstorm activities" → route_to_idea_generation (brainstorm = ideas)
- "creative lesson concepts" → route_to_idea_generation (concepts = ideas)
- "help me teach" → Ask for clarification (too vague)
"""


# Langfuse configuration for prompt management
LANGFUSE_PROMPT_NAME = "routing-agent"
LANGFUSE_PROMPT_LABEL = "production"


def get_routing_prompt() -> str:
    """
    Fetch the routing agent prompt from Langfuse.

    Falls back to DEFAULT_ROUTING_PROMPT if:
    - Langfuse is not configured
    - Prompt doesn't exist in Langfuse
    - Any error occurs during fetch

    Returns:
        str: The system prompt for the routing agent
    """
    client = get_langfuse_client()

    if client is None:
        return DEFAULT_ROUTING_PROMPT

    try:
        prompt = client.get_prompt(LANGFUSE_PROMPT_NAME, label=LANGFUSE_PROMPT_LABEL)
        # For text prompts, compile() returns the prompt string
        return prompt.compile()
    except Exception:
        # Prompt not found or other error - use default
        return DEFAULT_ROUTING_PROMPT


# --- Routing Tools ---
# These tools have no parameters. When called, they signal routing intent.
# The actual routing logic happens in the graph based on state updates.


@tool
def route_to_handwriting() -> str:
    """
    Route the user to the handwriting lesson creation flow.

    Use this tool when the user wants to:
    - Create a handwriting lesson
    - Practice letter formation
    - Work on tracing or writing letters
    - Develop fine motor skills through writing
    """
    return "Routing to handwriting lesson creation."


@tool
def route_to_vocabulary() -> str:
    """
    Route the user to the vocabulary lesson creation flow.

    Use this tool when the user wants to:
    - Create vocabulary lessons
    - Build word lists
    - Work on vocabulary building activities
    - Teach new words to students
    """
    return "Routing to vocabulary lesson creation."


@tool
def route_to_idea_generation() -> str:
    """
    Route the user to the lesson idea brainstorming flow.

    Use this tool when the user wants to:
    - Brainstorm lesson ideas
    - Get activity suggestions
    - Generate creative lesson concepts
    - Explore different teaching approaches
    """
    return "Routing to lesson idea brainstorming."


# All routing tools
ROUTING_TOOLS = [route_to_handwriting, route_to_vocabulary, route_to_idea_generation]

# Map tool names to task types
TOOL_TO_TASK_TYPE = {
    "route_to_handwriting": "handwriting",
    "route_to_vocabulary": "vocabulary",
    "route_to_idea_generation": "idea_generation",
}


def create_routing_agent(recursion_limit: int = 10):
    """
    Create the routing ReAct agent.

    Args:
        recursion_limit: Maximum number of agent turns (prevents infinite loops)

    Returns:
        CompiledStateGraph: The compiled ReAct agent
    """
    # Get model from registry (cost-effective for routing)
    model = get_chat_model("gpt-4o-mini")

    # Get prompt from Langfuse (or default)
    system_prompt = get_routing_prompt()

    # Create ReAct agent with tools
    # Note: create_agent handles the ReAct loop internally
    agent = create_agent(
        model=model,
        tools=ROUTING_TOOLS,
        system_prompt=system_prompt,
    )

    return agent
