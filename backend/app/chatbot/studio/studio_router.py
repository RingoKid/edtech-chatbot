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
from app.chatbot.checkpointer import get_shared_checkpointer

# Import all bots at module level to avoid blocking I/O during async execution
from app.chatbot.specialists.general.bot import GeneralBot, VocabularyBot, IdeasBot
from app.chatbot.specialists.handwriting.nodes import handwriting_nodes
from app.chatbot.routing.router_nodes import routing_decision_node


async def general_bot_response_node(state: RoutingState) -> Dict[str, Any]:
    """
    GeneralBot Response Node - Handles simple queries only.
    Routing logic has been moved to dedicated routing_decision_node.

    This node is called only when router determines query is simple.
    """
    try:
        messages = state.get("messages", [])
        query = state.get("original_query", "")

        if not query and messages:
            latest_message = messages[-1]
            if hasattr(latest_message, 'content'):
                query = latest_message.content
            else:
                query = str(latest_message)

        print(f"🎓 General Bot answering simple query: '{query[:60]}...'")

        # Create GeneralBot instance
        general_bot = GeneralBot()

        # Get intent from state (set by router)
        intent = state.get("intent")

        # Process message - GeneralBot now only answers, doesn't route
        result = await general_bot.process_message(
            query,
            conversation_history=messages,
            intent=intent
        )

        return {
            "messages": [AIMessage(content=result.response)],
            "bot_response": result.response,
            "bot_type": "general_bot",
            "relevant_forms": result.relevant_forms or [],
            "follow_up_questions": result.follow_up_questions or []
        }

    except Exception as e:
        print(f"❌ Error in general bot response: {str(e)}")
        import traceback
        traceback.print_exc()

        fallback = "I apologize, but I'm having trouble right now. Please try rephrasing your question."
        return {
            "messages": [AIMessage(content=fallback)],
            "bot_response": fallback,
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

        # Initialize handwriting state from routing state
        handwriting_state = {
            "messages": messages,
            "teacher_id": teacher_id,
            "session_id": session_id,
            "original_query": query,
            "query_type": None,
            "target_letters": [],
            "grade_level": None,
            "relevant_forms": [],
            "form_context": "",
            "response_generated": False,
            "response_quality_check": False,
            "retry_count": 0,
            "last_error": None,
            "needs_human_escalation": False,
            "conversation_depth": 0,
            "previous_topics": [],
            "follow_up_questions": []
        }

        # Run handwriting nodes sequentially
        # 1. Analyze query
        handwriting_state.update(await handwriting_nodes.analyze_query_node(handwriting_state))

        # 2. Retrieve forms
        handwriting_state.update(await handwriting_nodes.retrieve_forms_node(handwriting_state))

        # 3. Generate response
        handwriting_state.update(await handwriting_nodes.generate_response_node(handwriting_state))

        # 4. Quality check (optional)
        handwriting_state.update(await handwriting_nodes.quality_check_node(handwriting_state))

        # 5. Follow-up questions
        handwriting_state.update(await handwriting_nodes.follow_up_node(handwriting_state))

        # Extract response from messages
        bot_messages = handwriting_state.get("messages", [])
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
        relevant_forms = handwriting_state.get("relevant_forms", [])
        follow_up_questions = handwriting_state.get("follow_up_questions", [])

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


def route_after_router(state: RoutingState) -> str:
    """
    Decision point after routing_decision_node.
    Routes to appropriate bot based on router's decision.
    """
    target_bot = state.get("target_bot", "general")

    routing_map = {
        "general": "general_bot",
        "handwriting": "handwriting_specialist",
        "vocabulary": "vocabulary_specialist",
        "ideas": "ideas_specialist"
    }

    next_node = routing_map.get(target_bot, "general_bot")
    print(f"🔀 [ROUTER DECISION] Routing to: {next_node}")

    return next_node


def create_studio_routing_graph():
    """
    Creates Router-First routing graph with dedicated routing node.

    Flow:
    User Query → Router Node → [Decision]
                                  ↓
                      Simple? → General Bot → END
                      Complex? → Specialist → END

    Routing logic is separated from bot logic for clarity.
    """
    print("🔧 Building Router-First Graph (Dedicated Routing Node)...")

    # Initialize graph
    graph = StateGraph(RoutingState)

    # Add nodes
    print("📍 Adding nodes...")
    graph.add_node("router", routing_decision_node)
    graph.add_node("general_bot", general_bot_response_node)
    graph.add_node("handwriting_specialist", execute_handwriting_specialist_node)
    graph.add_node("vocabulary_specialist", execute_vocabulary_specialist_node)
    graph.add_node("ideas_specialist", execute_ideas_specialist_node)

    # Entry point: ALWAYS start with router
    print("🚀 Setting entry point to Router Node...")
    graph.add_edge(START, "router")

    # Routing logic - route based on router's decision
    print("🔀 Adding routing logic...")
    graph.add_conditional_edges(
        "router",
        route_after_router,
        {
            "general_bot": "general_bot",
            "handwriting_specialist": "handwriting_specialist",
            "vocabulary_specialist": "vocabulary_specialist",
            "ideas_specialist": "ideas_specialist"
        }
    )

    # All bots return to user
    graph.add_edge("general_bot", END)
    graph.add_edge("handwriting_specialist", END)
    graph.add_edge("vocabulary_specialist", END)
    graph.add_edge("ideas_specialist", END)

    # Compile graph WITHOUT checkpointer (for Studio compatibility)
    print("⚙️ Compiling graph...")
    compiled_graph = graph.compile()

    print("✅ Router-First Graph compiled successfully!")
    print("📊 Flow:")
    print("   User → Router Node → [Intelligent Decision]")
    print("                           ↓")
    print("              General Bot OR Specialist")
    print("                           ↓")
    print("                   User gets answer")
    print("")
    print("🎯 Key Feature: Routing logic separated from bot logic!")
    print("💾 Memory: Managed by chat service layer")

    return compiled_graph


def create_studio_routing_graph_with_memory():
    """
    Creates the same routing graph but WITH SqliteSaver for conversation persistence.
    This version is used by the chat service API for production.

    Uses SqliteSaver instead of MemorySaver for persistent storage across server restarts.
    """
    print("🔧 Building Router-First Graph WITH PERSISTENT MEMORY...")

    # Initialize graph
    graph = StateGraph(RoutingState)

    # Add nodes (same as above)
    print("📍 Adding nodes...")
    graph.add_node("router", routing_decision_node)
    graph.add_node("general_bot", general_bot_response_node)
    graph.add_node("handwriting_specialist", execute_handwriting_specialist_node)
    graph.add_node("vocabulary_specialist", execute_vocabulary_specialist_node)
    graph.add_node("ideas_specialist", execute_ideas_specialist_node)

    # Entry point
    print("🚀 Setting entry point to Router Node...")
    graph.add_edge(START, "router")

    # Routing logic
    print("🔀 Adding routing logic...")
    graph.add_conditional_edges(
        "router",
        route_after_router,
        {
            "general_bot": "general_bot",
            "handwriting_specialist": "handwriting_specialist",
            "vocabulary_specialist": "vocabulary_specialist",
            "ideas_specialist": "ideas_specialist"
        }
    )

    # All bots return to user
    graph.add_edge("general_bot", END)
    graph.add_edge("handwriting_specialist", END)
    graph.add_edge("vocabulary_specialist", END)
    graph.add_edge("ideas_specialist", END)

    # Compile WITH AsyncSqliteSaver for persistent conversation memory
    print("⚙️ Compiling graph with AsyncSqliteSaver (persistent storage)...")
    checkpointer = get_shared_checkpointer()  # AsyncSqliteSaver - persists across restarts
    compiled_graph = graph.compile(checkpointer=checkpointer)

    print("✅ Router-First Graph WITH PERSISTENT MEMORY compiled successfully!")
    print("💾 Memory: AsyncSqliteSaver enabled - conversation history persists across server restarts")
    print("🔄 Cross-bot context: ENABLED - context shared across specialist switches")
    print("📁 Database: backend/checkpoints/conversations.db")

    return compiled_graph


# ===================================================================
# LAZY GRAPH INITIALIZATION
# ===================================================================
# Graphs are created on-demand to avoid checkpointer initialization race conditions

# 1. For LangGraph Studio (no checkpointer)
studio_router = create_studio_routing_graph()

# 2. For API with conversation memory (with checkpointer) - LAZY INITIALIZATION
_studio_router_with_memory_cache = None

def get_studio_router_with_memory():
    """
    Lazy initialization of the routing graph with memory.
    Creates the graph on first use, after checkpointer is initialized.

    Returns:
        Compiled LangGraph with AsyncSqliteSaver checkpointer
    """
    global _studio_router_with_memory_cache

    if _studio_router_with_memory_cache is None:
        print("🔧 First access: Creating routing graph with persistent memory...")
        _studio_router_with_memory_cache = create_studio_routing_graph_with_memory()

    return _studio_router_with_memory_cache

# Keep backward compatibility
studio_routing_graph = studio_router