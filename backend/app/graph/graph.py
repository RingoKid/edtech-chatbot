"""
Graph definition for v2 architecture - ReAct routing agent with task generators.

Architecture:
1. User message comes in
2. Routing agent (ReAct) processes and either:
   - Asks clarifying questions (continues conversation)
   - Calls a routing tool (triggers handoff)
3. If routing tool was called, route to param agent
4. Param agent collects task-specific parameters
5. When params collected, route to generator agent
6. Generator produces lesson, allows modifications until finalized
"""

import os

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph_checkpoint_aws import DynamoDBSaver
from langchain_core.messages import AIMessage, ToolMessage

from app.graph.state import (
    GraphState,
    FeedbackData,
    HandwritingParams,
    VocabularySyntaxParams,
    IdeaGenerationParams,
)
from app.graph.agents.routing import (
    create_routing_agent,
    TOOL_TO_TASK_TYPE,
)
from app.graph.agents.param import (
    create_param_agent,
    HANDWRITING_TOOL_NAME,
    VOCABULARY_TOOL_NAME,
    IDEA_GENERATION_TOOL_NAME,
)
from app.graph.agents.handwriting_generator import (
    create_handwriting_generator_agent,
    FINALIZE_TOOL_NAME,
)
from app.graph.agents.feedback_collector import (
    create_feedback_collector_agent,
    SUBMIT_FEEDBACK_TOOL_NAME,
    SKIP_FEEDBACK_TOOL_NAME,
)
from app.graph.nodes.placeholders import (
    handwriting_placeholder,
    vocabulary_placeholder,
    idea_generation_placeholder,
    vocabulary_generator_placeholder,
    idea_generation_generator_placeholder,
)
from app.config import settings


# Configure boto3 to use DynamoDB Local endpoint (for langgraph-checkpoint-aws)
# This must be set before DynamoDBSaver is instantiated
if settings.dynamodb_endpoint_url:
    os.environ['AWS_ENDPOINT_URL_DYNAMODB'] = settings.dynamodb_endpoint_url
    os.environ['AWS_DEFAULT_REGION'] = settings.aws_region


def routing_agent_node(state: GraphState) -> dict:
    """
    Node that runs the routing ReAct agent.

    The agent will either:
    1. Generate a response (greeting, clarification question)
    2. Call a routing tool (indicating user intent is clear)

    Returns state updates including messages and optionally task_type.
    """
    # Create fresh agent instance (stateless)
    agent = create_routing_agent()

    # Invoke the agent with current messages
    result = agent.invoke({"messages": state["messages"]})

    # Extract messages from agent result
    new_messages = result.get("messages", [])

    # Check if a routing tool was called by looking at the last messages
    task_type = None
    for msg in reversed(new_messages):
        # Tool messages indicate a tool was called
        if isinstance(msg, ToolMessage):
            tool_name = msg.name
            if tool_name in TOOL_TO_TASK_TYPE:
                task_type = TOOL_TO_TASK_TYPE[tool_name]
                break

    return {
        "messages": new_messages,
        "task_type": task_type,
        "routing_complete": task_type is not None,
    }


def route_after_agent(state: GraphState) -> str:
    """
    Routing function: decide where to go after the routing agent runs.

    If a routing tool was called (task_type is set), go to param agent.
    Otherwise, end the graph (agent will continue on next invoke).
    """
    task_type = state.get("task_type")

    if task_type == "handwriting":
        # Go to param agent to collect handwriting parameters
        return "param_agent"
    elif task_type == "vocabulary":
        # Go to param agent to collect vocabulary parameters
        return "param_agent"
    elif task_type == "idea_generation":
        # Go to param agent to collect idea generation parameters
        return "param_agent"
    else:
        # No routing tool called - agent asked a question or greeted
        # End this invocation; user will respond and invoke again
        return END


def param_agent_node(state: GraphState) -> dict:
    """
    Node that runs the parameter collection ReAct agent.

    The agent will either:
    1. Ask for missing parameters
    2. Call the appropriate submit tool when all params collected

    After the agent runs, we inspect messages for tool calls and
    extract parameters to state.
    """
    # Create fresh agent instance (stateless)
    agent = create_param_agent()

    # Invoke the agent with current messages
    result = agent.invoke({"messages": state["messages"]})

    # Extract messages from agent result
    new_messages = result.get("messages", [])

    # Check which tool was called and extract parameters
    handwriting_params = extract_handwriting_params(new_messages)
    vocabulary_params = extract_vocabulary_params(new_messages)
    idea_generation_params = extract_idea_generation_params(new_messages)

    return {
        "messages": new_messages,
        "handwriting_params": handwriting_params,
        "vocabulary_params": vocabulary_params,
        "idea_generation_params": idea_generation_params,
    }


def extract_handwriting_params(messages: list) -> HandwritingParams | None:
    """
    Extract handwriting parameters from tool call in messages.

    Looks for the submit_handwriting_params tool call and extracts
    the arguments as HandwritingParams.

    Returns None if the tool wasn't called.
    """
    # Look for AI message with tool_calls
    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and hasattr(msg, 'tool_calls') and msg.tool_calls:
            for tool_call in msg.tool_calls:
                if tool_call.get('name') == HANDWRITING_TOOL_NAME:
                    args = tool_call.get('args', {})
                    # Normalize letter to uppercase
                    letter = args.get('letter', '').upper().strip()
                    return HandwritingParams(
                        grade=args.get('grade'),
                        letter=letter,
                        student_level=args.get('student_level', 'on-level'),
                    )
    return None


def extract_vocabulary_params(messages: list) -> VocabularySyntaxParams | None:
    """
    Extract vocabulary parameters from tool call in messages.

    Looks for the submit_vocabulary_params tool call and extracts
    the arguments as VocabularySyntaxParams.

    Returns None if the tool wasn't called.
    """
    # Look for AI message with tool_calls
    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and hasattr(msg, 'tool_calls') and msg.tool_calls:
            for tool_call in msg.tool_calls:
                if tool_call.get('name') == VOCABULARY_TOOL_NAME:
                    args = tool_call.get('args', {})
                    return VocabularySyntaxParams(
                        grade=args.get('grade'),
                        writing_type=args.get('writing_type'),
                        key_vocabulary=args.get('key_vocabulary', []),
                        objectives=args.get('objectives', ''),
                        student_level=args.get('student_level', 'on-level'),
                    )
    return None


def extract_idea_generation_params(messages: list) -> IdeaGenerationParams | None:
    """
    Extract idea generation parameters from tool call in messages.

    Looks for the submit_idea_generation_params tool call and extracts
    the arguments as IdeaGenerationParams.

    Returns None if the tool wasn't called.
    """
    # Look for AI message with tool_calls
    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and hasattr(msg, 'tool_calls') and msg.tool_calls:
            for tool_call in msg.tool_calls:
                if tool_call.get('name') == IDEA_GENERATION_TOOL_NAME:
                    args = tool_call.get('args', {})
                    return IdeaGenerationParams(
                        grade=args.get('grade'),
                        genre=args.get('genre'),
                        genre_component=args.get('genre_component', ''),
                        writing_stage=args.get('writing_stage'),
                        objectives=args.get('objectives', ''),
                        student_level=args.get('student_level', 'on-level'),
                    )
    return None


def route_after_param_agent(state: GraphState) -> str:
    """
    Routing function: decide where to go after the param agent runs.

    If params were collected, go to appropriate generator.
    Otherwise, end the graph (user needs to provide more info).
    """
    if state.get("handwriting_params") is not None:
        return "handwriting_generator"

    if state.get("vocabulary_params") is not None:
        return "vocabulary_generator_placeholder"

    if state.get("idea_generation_params") is not None:
        return "idea_generation_generator_placeholder"

    # Param agent asked for more info - wait for user response
    return END


def handwriting_generator_node(state: GraphState) -> dict:
    """
    Node that runs the handwriting generator ReAct agent.

    The agent will:
    1. Generate a complete lesson on first invocation
    2. Allow modifications based on user feedback
    3. Call finalize_lesson when user is satisfied

    Returns state updates including messages and lesson_finalized flag.
    """
    # Get params from state
    params = state.get("handwriting_params")
    if params is None:
        # Shouldn't happen, but handle gracefully
        return {
            "messages": [AIMessage(content="Error: No handwriting parameters found.")],
        }

    # Create agent with params
    agent = create_handwriting_generator_agent(
        grade=params["grade"],
        letter=params["letter"],
        student_level=params["student_level"],
    )

    # Invoke the agent with current messages
    result = agent.invoke({"messages": state["messages"]})

    # Extract messages from agent result
    new_messages = result.get("messages", [])

    # Check if finalize_lesson tool was called
    lesson_finalized = check_finalize_called(new_messages)

    return {
        "messages": new_messages,
        "lesson_finalized": lesson_finalized,
    }


def check_finalize_called(messages: list) -> bool:
    """
    Check if the finalize_lesson tool was called in messages.

    Returns True if the tool was called, False otherwise.
    """
    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and hasattr(msg, 'tool_calls') and msg.tool_calls:
            for tool_call in msg.tool_calls:
                if tool_call.get('name') == FINALIZE_TOOL_NAME:
                    return True
    return False


def route_after_handwriting_generator(state: GraphState) -> str:
    """
    Routing function: decide where to go after the handwriting generator runs.

    If finalize_lesson was called, route to feedback_collector.
    Otherwise, end this invocation and wait for user response.
    """
    if state.get("lesson_finalized"):
        return "feedback_collector"

    # Generator presented lesson or made modifications - wait for user feedback
    return END


def feedback_collector_node(state: GraphState) -> dict:
    """
    Node that runs the feedback collector ReAct agent.

    The agent will either:
    1. Ask the user for optional feedback (first run after finalize)
    2. Parse user feedback and call submit_feedback or skip_feedback

    Returns state updates including messages, feedback_submitted, and feedback_data.
    """
    agent = create_feedback_collector_agent()

    result = agent.invoke({"messages": state["messages"]})

    new_messages = result.get("messages", [])

    # Check which feedback tool was called
    feedback_submitted = False
    feedback_data = None

    for msg in reversed(new_messages):
        if isinstance(msg, AIMessage) and hasattr(msg, 'tool_calls') and msg.tool_calls:
            for tool_call in msg.tool_calls:
                tool_name = tool_call.get('name')
                if tool_name == SUBMIT_FEEDBACK_TOOL_NAME:
                    args = tool_call.get('args', {})
                    feedback_data = FeedbackData(
                        category=args.get('category', 'general'),
                        rating=args.get('rating', 0),
                        text=args.get('text', ''),
                    )
                    feedback_submitted = True
                    break
                elif tool_name == SKIP_FEEDBACK_TOOL_NAME:
                    feedback_submitted = True
                    break
        if feedback_submitted:
            break

    return {
        "messages": new_messages,
        "feedback_submitted": feedback_submitted,
        "feedback_data": feedback_data,
    }


def route_after_feedback_collector(state: GraphState) -> str:
    """
    Routing function: after feedback collector, always go to END.
    """
    return END


def entry_router(state: GraphState) -> str:
    """
    Entry point router: decide where to start based on current state.

    Priority:
    1. Mid-feedback: finalized but feedback not yet submitted → feedback_collector
    2. Mid-generation: params set, not finalized → generator
    3. Default: routing_agent
    """
    # Check if we're in an active handwriting generation session
    if (
        state.get("handwriting_params") is not None
        and not state.get("lesson_finalized", False)
    ):
        return "handwriting_generator"

    # Mid-feedback: lesson finalized but feedback not yet submitted
    if (
        state.get("lesson_finalized", False)
        and not state.get("feedback_submitted", False)
    ):
        return "feedback_collector"

    # Default: go through routing
    return "routing_agent"


async def create_graph(checkpointer: BaseCheckpointSaver | None = None):
    """
    Factory function to create the graph with proper dependency injection.

    Args:
        checkpointer: Optional checkpointer for state persistence.
                      If None, creates a DynamoDBSaver.

    Returns:
        CompiledStateGraph: The compiled LangGraph
    """
    # Use provided checkpointer or create DynamoDB one
    if checkpointer is None:
        checkpointer = DynamoDBSaver(
            table_name=settings.checkpoint_table_name,
            region_name=settings.aws_region
        )

    # Create the state graph
    graph = StateGraph(GraphState)

    # Add nodes
    graph.add_node("routing_agent", routing_agent_node)
    graph.add_node("param_agent", param_agent_node)
    graph.add_node("handwriting_placeholder", handwriting_placeholder)
    graph.add_node("handwriting_generator", handwriting_generator_node)
    graph.add_node("feedback_collector", feedback_collector_node)
    graph.add_node("vocabulary_placeholder", vocabulary_placeholder)
    graph.add_node("vocabulary_generator_placeholder", vocabulary_generator_placeholder)
    graph.add_node("idea_generation_placeholder", idea_generation_placeholder)
    graph.add_node("idea_generation_generator_placeholder", idea_generation_generator_placeholder)

    # Set conditional entry point - routes based on current session state
    graph.set_conditional_entry_point(
        entry_router,
        {
            "routing_agent": "routing_agent",
            "handwriting_generator": "handwriting_generator",
            "feedback_collector": "feedback_collector",
        }
    )

    # Add conditional edges from routing agent
    graph.add_conditional_edges(
        "routing_agent",
        route_after_agent,
        {
            "param_agent": "param_agent",
            "vocabulary_placeholder": "vocabulary_placeholder",
            "idea_generation_placeholder": "idea_generation_placeholder",
            END: END,
        }
    )

    # Add conditional edges from param agent
    graph.add_conditional_edges(
        "param_agent",
        route_after_param_agent,
        {
            "handwriting_generator": "handwriting_generator",
            "vocabulary_generator_placeholder": "vocabulary_generator_placeholder",
            "idea_generation_generator_placeholder": "idea_generation_generator_placeholder",
            END: END,
        }
    )

    # Handwriting generator routes to feedback_collector after finalize
    graph.add_conditional_edges(
        "handwriting_generator",
        route_after_handwriting_generator,
        {
            "feedback_collector": "feedback_collector",
            END: END,
        }
    )

    # Feedback collector always ends after collecting or skipping
    graph.add_conditional_edges(
        "feedback_collector",
        route_after_feedback_collector,
        {END: END}
    )

    # Placeholder nodes always end the conversation
    graph.add_edge("handwriting_placeholder", END)
    graph.add_edge("vocabulary_placeholder", END)
    graph.add_edge("vocabulary_generator_placeholder", END)
    graph.add_edge("idea_generation_placeholder", END)
    graph.add_edge("idea_generation_generator_placeholder", END)

    # Compile the graph
    # Note: No interrupt_after needed - the ReAct agent naturally returns
    # after generating a response, and we call it again on next user message
    return graph.compile(checkpointer=checkpointer)


# Create the graph instance at module level for langgraph.json
# Note: This needs to be called with await in an async context
graph = create_graph
