"""
General-First Routing Graph - Transparent specialist handoffs.
Users interact with GeneralBot, which seamlessly routes to specialists when needed.
The handoff is invisible - users just get their answer.

Now with CONVERSATION MEMORY and CROSS-BOT CONTEXT SHARING!
"""
from typing import Dict, Any
from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, AIMessage
from app.chatbot.routing.router_state import RoutingState

# Import all bots at module level to avoid blocking I/O during async execution
from app.chatbot.specialists.general.bot import GeneralBot, VocabularyBot, IdeasBot
from app.chatbot.specialists.handwriting.graph import run_handwriting_bot


async def general_bot_hub_node(state: RoutingState) -> Dict[str, Any]:
    """
    PRIMARY HUB: GeneralBot handles all queries and decides routing.
    - Simple queries: Answers directly
    - Complex queries: Routes to specialist (invisible to user)
    """
    try:
        messages = state.get("messages", [])
        if not messages:
            return {
                "bot_response": "Hello! How can I help you today?",
                "messages": [AIMessage(content="Hello! How can I help you today?")],
                "needs_specialist": False
            }

        # Extract query from messages
        latest_message = messages[-1]
        if hasattr(latest_message, 'content'):
            query = latest_message.content
        elif isinstance(latest_message, dict) and 'content' in latest_message:
            query = latest_message['content']
        elif isinstance(latest_message, list):
            if len(latest_message) > 0 and isinstance(latest_message[0], dict):
                query = latest_message[0].get('text') or latest_message[0].get('content', '')
            else:
                query = " ".join(str(item) for item in latest_message)
        else:
            query = str(latest_message)

        if not isinstance(query, str):
            query = str(query)
        query = query.strip()

        print(f"🎓 General Bot Hub processing: '{query[:60]}...'")

        # Create GeneralBot instance
        general_bot = GeneralBot()

        # Detect complexity using hybrid approach
        complexity = await general_bot.detect_query_complexity(query, messages)

        if complexity == "simple":
            # SIMPLE QUERY: General bot answers directly
            print(f"✅ Simple query - General bot will answer directly")
            result = await general_bot.process_message(query, conversation_history=messages)

            return {
                "messages": [AIMessage(content=result.response)],
                "bot_response": result.response,
                "bot_type": "general_bot",
                "needs_specialist": False,
                "relevant_forms": result.relevant_forms or [],
                "follow_up_questions": result.follow_up_questions or []
            }

        else:
            # COMPLEX QUERY: Need specialist
            print(f"🔀 Complex query - routing to specialist")

            # Classify which specialist (using conversation history for context)
            topic = general_bot.classify_topic(query, conversation_history=messages)

            # If no specific topic detected, general bot handles it
            if topic is None:
                print(f"📝 Complex but general query - General bot will handle with conversation context")
                result = await general_bot.process_message(query, conversation_history=messages)

                return {
                    "messages": [AIMessage(content=result.response)],
                    "bot_response": result.response,
                    "bot_type": "general_bot",
                    "needs_specialist": False,
                    "relevant_forms": result.relevant_forms or [],
                    "follow_up_questions": result.follow_up_questions or []
                }

            # Route to specific specialist
            return {
                "original_query": query,
                "needs_specialist": True,
                "specialist_topic": topic,
                "processing_steps": [f"Detected complexity: {complexity}, topic: {topic}"]
            }

    except Exception as e:
        print(f"❌ Error in general bot hub: {str(e)}")
        import traceback
        traceback.print_exc()

        fallback = "I apologize, but I'm having trouble right now. Please try rephrasing your question."
        return {
            "messages": [AIMessage(content=fallback)],
            "bot_response": fallback,
            "needs_specialist": False,
            "bot_type": "general_bot_error"
        }


async def execute_handwriting_specialist_node(state: RoutingState) -> Dict[str, Any]:
    """
    Handwriting Specialist - Called transparently by general bot.
    User doesn't know they're being handed off.
    """
    try:
        query = state.get("original_query", "")
        messages = state.get("messages", [])
        teacher_id = state.get("teacher_id", "studio_teacher")
        session_id = state.get("session_id", "studio_session")

        print(f"🖊️ [TRANSPARENT HANDOFF] Handwriting specialist processing: '{query[:60]}...'")

        # Run handwriting bot
        result = await run_handwriting_bot(
            teacher_query=query,
            teacher_id=teacher_id,
            session_id=session_id,
            conversation_history=messages
        )

        # Extract response
        bot_messages = result.get("messages", [])
        bot_response = ""

        for message in reversed(bot_messages):
            if hasattr(message, 'type') and message.type == 'ai':
                bot_response = message.content
                break
            elif hasattr(message, 'content') and isinstance(message.content, str):
                bot_response = message.content
                break

        if not bot_response:
            bot_response = "I apologize, but I couldn't generate a proper response."

        # Extract metadata
        relevant_forms = result.get("relevant_forms", [])
        follow_up_questions = result.get("follow_up_questions", [])

        print(f"✅ [TRANSPARENT] Handwriting specialist completed - user receives seamless response")

        return {
            "messages": [AIMessage(content=bot_response)],
            "bot_response": bot_response,
            "bot_type": "handwriting_specialist",
            "relevant_forms": relevant_forms,
            "follow_up_questions": follow_up_questions
        }

    except Exception as e:
        print(f"❌ Error in handwriting specialist: {str(e)}")
        import traceback
        traceback.print_exc()

        # Graceful fallback
        fallback = "I can help with handwriting instruction, but I'm having a technical issue. Could you try rephrasing your question?"
        return {
            "messages": [AIMessage(content=fallback)],
            "bot_response": fallback,
            "bot_type": "handwriting_specialist_error"
        }


async def execute_vocabulary_specialist_node(state: RoutingState) -> Dict[str, Any]:
    """
    Vocabulary Specialist - Called transparently by general bot.
    """
    try:
        query = state.get("original_query", "")
        messages = state.get("messages", [])

        print(f"📚 [TRANSPARENT HANDOFF] Vocabulary specialist processing: '{query[:60]}...'")

        vocab_bot = VocabularyBot()
        result = await vocab_bot.process_message(query, conversation_history=messages)

        print(f"✅ [TRANSPARENT] Vocabulary specialist completed")

        return {
            "messages": [AIMessage(content=result.response)],
            "bot_response": result.response,
            "bot_type": "vocabulary_specialist",
            "relevant_forms": result.relevant_forms or [],
            "follow_up_questions": result.follow_up_questions or []
        }

    except Exception as e:
        print(f"❌ Error in vocabulary specialist: {str(e)}")
        fallback = "I can help with vocabulary and sentence instruction, but I'm having a technical issue. Please try again."
        return {
            "messages": [AIMessage(content=fallback)],
            "bot_response": fallback,
            "bot_type": "vocabulary_specialist_error"
        }


async def execute_ideas_specialist_node(state: RoutingState) -> Dict[str, Any]:
    """
    Ideas Specialist - Called transparently by general bot.
    """
    try:
        query = state.get("original_query", "")
        messages = state.get("messages", [])

        print(f"💡 [TRANSPARENT HANDOFF] Ideas specialist processing: '{query[:60]}...'")

        ideas_bot = IdeasBot()
        result = await ideas_bot.process_message(query, conversation_history=messages)

        print(f"✅ [TRANSPARENT] Ideas specialist completed")

        return {
            "messages": [AIMessage(content=result.response)],
            "bot_response": result.response,
            "bot_type": "ideas_specialist",
            "relevant_forms": result.relevant_forms or [],
            "follow_up_questions": result.follow_up_questions or []
        }

    except Exception as e:
        print(f"❌ Error in ideas specialist: {str(e)}")
        fallback = "I can help with creative writing and ideas, but I'm having a technical issue. Please try again."
        return {
            "messages": [AIMessage(content=fallback)],
            "bot_response": fallback,
            "bot_type": "ideas_specialist_error"
        }


def route_after_general_bot(state: RoutingState) -> str:
    """
    Decision point: Did general bot answer, or do we need a specialist?
    This routing is INVISIBLE to the user.
    """
    needs_specialist = state.get("needs_specialist", False)

    if not needs_specialist:
        # General bot handled it - done!
        print(f"✅ General bot answered directly - conversation complete")
        return "END"

    # Need specialist - route based on topic
    topic = state.get("specialist_topic", "general")

    routing_map = {
        "handwriting": "handwriting_specialist",
        "vocabulary": "vocabulary_specialist",
        "ideas": "ideas_specialist",
        "general": "END"  # Fallback to general bot's answer
    }

    next_node = routing_map.get(topic, "END")
    print(f"🔀 [TRANSPARENT ROUTING] {topic} → {next_node}")

    return next_node


def create_studio_routing_graph():
    """
    Creates GENERAL-FIRST routing graph with transparent specialist handoffs.

    Flow:
    User Query → General Bot Hub → [Decision]
                                      ↓
                          Simple? → Answer directly → END
                          Complex? → Route to Specialist → END

    User NEVER knows about the routing - they just get their answer!
    """
    print("🔧 Building General-First Routing Graph (Transparent Handoffs)...")

    # Initialize graph
    graph = StateGraph(RoutingState)

    # Add nodes
    print("📍 Adding nodes...")
    graph.add_node("general_bot_hub", general_bot_hub_node)
    graph.add_node("handwriting_specialist", execute_handwriting_specialist_node)
    graph.add_node("vocabulary_specialist", execute_vocabulary_specialist_node)
    graph.add_node("ideas_specialist", execute_ideas_specialist_node)

    # Entry point: ALWAYS start with general bot
    print("🚀 Setting entry point to General Bot Hub...")
    graph.add_edge(START, "general_bot_hub")

    # Routing logic (invisible to user)
    print("🔀 Adding transparent routing logic...")
    graph.add_conditional_edges(
        "general_bot_hub",
        route_after_general_bot,
        {
            "handwriting_specialist": "handwriting_specialist",
            "vocabulary_specialist": "vocabulary_specialist",
            "ideas_specialist": "ideas_specialist",
            "END": END
        }
    )

    # All specialists return to user
    graph.add_edge("handwriting_specialist", END)
    graph.add_edge("vocabulary_specialist", END)
    graph.add_edge("ideas_specialist", END)

    # Compile graph WITHOUT checkpointer (for Studio compatibility)
    print("⚙️ Compiling graph...")
    compiled_graph = graph.compile()

    print("✅ General-First Routing Graph compiled successfully!")
    print("📊 Flow:")
    print("   User → General Bot Hub → [Intelligent Decision]")
    print("                              ↓")
    print("                    Simple? Answer directly")
    print("                    Complex? → Specialist (TRANSPARENT)")
    print("                              ↓")
    print("                          User gets answer")
    print("")
    print("🎯 Key Feature: Handoffs are INVISIBLE to users!")
    print("💾 Memory: Managed by chat service layer")

    return compiled_graph


def create_studio_routing_graph_with_memory():
    """
    Creates the same routing graph but WITH MemorySaver for conversation persistence.
    This version is used by the chat service API for production.
    """
    print("🔧 Building General-First Routing Graph WITH MEMORY...")

    # Initialize graph
    graph = StateGraph(RoutingState)

    # Add nodes (same as above)
    print("📍 Adding nodes...")
    graph.add_node("general_bot_hub", general_bot_hub_node)
    graph.add_node("handwriting_specialist", execute_handwriting_specialist_node)
    graph.add_node("vocabulary_specialist", execute_vocabulary_specialist_node)
    graph.add_node("ideas_specialist", execute_ideas_specialist_node)

    # Entry point
    print("🚀 Setting entry point to General Bot Hub...")
    graph.add_edge(START, "general_bot_hub")

    # Routing logic
    print("🔀 Adding transparent routing logic...")
    graph.add_conditional_edges(
        "general_bot_hub",
        route_after_general_bot,
        {
            "handwriting_specialist": "handwriting_specialist",
            "vocabulary_specialist": "vocabulary_specialist",
            "ideas_specialist": "ideas_specialist",
            "END": END
        }
    )

    # All specialists return to user
    graph.add_edge("handwriting_specialist", END)
    graph.add_edge("vocabulary_specialist", END)
    graph.add_edge("ideas_specialist", END)

    # Compile WITH checkpointer for conversation memory
    print("⚙️ Compiling graph with MemorySaver...")
    checkpointer = MemorySaver()
    compiled_graph = graph.compile(checkpointer=checkpointer)

    print("✅ General-First Routing Graph WITH MEMORY compiled successfully!")
    print("💾 Memory: MemorySaver enabled - full conversation history persisted")
    print("🔄 Cross-bot context: ENABLED - context shared across specialist switches")

    return compiled_graph


# Create TWO graph instances:
# 1. For LangGraph Studio (no checkpointer)
studio_router = create_studio_routing_graph()

# 2. For API with conversation memory (with checkpointer)
studio_router_with_memory = create_studio_routing_graph_with_memory()

# Keep backward compatibility
studio_routing_graph = studio_router