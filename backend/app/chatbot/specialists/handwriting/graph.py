"""
Handwriting and Spelling Bot LangGraph Implementation.
Creates the complete graph structure with nodes, edges, and routing logic.
"""
import os
from langgraph.graph import StateGraph, END, START
from app.chatbot.specialists.handwriting.state import HandwritingState
from app.chatbot.specialists.handwriting.nodes import handwriting_nodes
from app.config import settings
from langchain_core.messages import AIMessage

# Initialize LangSmith tracing if configured
if settings.langsmith_api_key and settings.langsmith_tracing:
    os.environ["LANGCHAIN_TRACING_V2"] = str(settings.langsmith_tracing)
    os.environ["LANGCHAIN_API_KEY"] = settings.langsmith_api_key  # langsmith_api_key is already a string
    os.environ["LANGCHAIN_PROJECT"] = settings.langsmith_project or "handwriting-bot"
    print(f"✅ LangSmith tracing enabled for project: {settings.langsmith_project}")

def should_retry(state: HandwritingState) -> str:
    """
    Conditional edge function to determine if we should retry after an error.

    Args:
        state: Current handwriting bot state

    Returns:
        Next node to execute based on retry logic
    """
    retry_count = state.get("retry_count", 0)
    last_error = state.get("last_error")

    if last_error and retry_count < 3:
        print(f"🔄 Retrying due to error (attempt {retry_count + 1}/3): {last_error}")
        return "analyze_query"
    elif retry_count >= 3:
        print(f"❌ Max retries reached, ending with error")
        return "end_with_error"
    else:
        return "generate_response"

def should_improve_response(state: HandwritingState) -> str:
    """
    Conditional edge function to determine if response needs improvement.
    
    Args:
        state: Current handwriting bot state
        
    Returns:
        Next node based on response quality
    """
    needs_improvement = state.get("needs_improvement", False)
    retry_count = state.get("retry_count", 0)
    
    if needs_improvement and retry_count < 2:
        print(f"🔄 Improving response (attempt {retry_count + 1}/2)")
        return "generate_response"
    else:
        return "follow_up"

def route_after_analysis(state: HandwritingState) -> str:
    """
    Conditional edge function to route after query analysis.
    
    Args:
        state: Current handwriting bot state
        
    Returns:
        Next node based on analysis results
    """
    last_error = state.get("last_error")
    query_type = state.get("query_type", "general")

    if last_error:
        return "handle_error"
    elif query_type in ["letter_formation", "spelling", "assessment", "pencil_grip", "general"]:
        return "retrieve_forms"
    else:
        print(f"⚠️ Unknown query type: {query_type}, defaulting to general")
        return "retrieve_forms"

async def handle_error_node(state: HandwritingState) -> dict:
    """
    Node to handle errors gracefully.
    
    Args:
        state: Current handwriting bot state
        
    Returns:
        Updated state with error handling
    """
    from langchain_core.messages import AIMessage
    
    retry_count = state.get("retry_count", 0)
    last_error = state.get("last_error", "Unknown error")
    
    if retry_count >= 3:
        # Create fallback response
        fallback_message = AIMessage(content="""
        I apologize, but I'm experiencing technical difficulties accessing the specific educational content right now. 
        
        However, I can still provide general handwriting guidance:
        
        **Quick Handwriting Tips:**
        • Start with proper posture and pencil grip
        • Practice with large movements first (air writing, sky writing)
        • Use multi-sensory approaches (visual, auditory, kinesthetic)
        • Keep practice sessions short and frequent
        • Celebrate small improvements to build confidence
        
        **Common Materials:**
        • Large crayons or markers for beginners
        • Dotted line practice sheets
        • Playdough for finger strengthening
        • Sand trays for letter formation practice
        
        Please try your question again, or feel free to ask about any specific aspect of handwriting instruction.
        """)
        
        return {
            "messages": [fallback_message],
            "needs_human_escalation": True,
            "response_generated": True
        }
    else:
        return {
            "retry_count": retry_count + 1,
            "last_error": None  # Clear error for retry
        }

async def end_with_error_node(state: HandwritingState) -> dict:
    """
    Terminal node for when max retries are reached.
    
    Args:
        state: Current handwriting bot state
        
    Returns:
        Final error state
    """
    from langchain_core.messages import AIMessage
    
    error_message = AIMessage(content="""
    I apologize, but I'm currently experiencing technical difficulties and cannot provide the detailed handwriting guidance you're looking for. 
    
    Please try your question again later, or contact support if this issue persists.
    
    In the meantime, you might find general handwriting resources helpful from educational websites or your school's curriculum materials.
    """)
    
    return {
        "messages": [error_message],
        "needs_human_escalation": True,
        "response_generated": True
    }

def create_handwriting_graph():
    """
    Create and compile the handwriting bot LangGraph.

    Returns:
        Compiled LangGraph for handwriting instruction
    """
    print("🔧 Building Handwriting Bot Graph...")

    # Initialize the graph with our state schema
    graph = StateGraph(HandwritingState)

    # Add all nodes to the graph
    print("📍 Adding nodes...")
    graph.add_node("analyze_query", handwriting_nodes.analyze_query_node)
    graph.add_node("retrieve_forms", handwriting_nodes.retrieve_forms_node)
    graph.add_node("generate_response", handwriting_nodes.generate_response_node)
    graph.add_node("quality_check", handwriting_nodes.quality_check_node)
    graph.add_node("follow_up", handwriting_nodes.follow_up_node)
    graph.add_node("handle_error", handle_error_node)
    graph.add_node("end_with_error", end_with_error_node)

    # Set the entry point
    print("🚀 Setting entry point...")
    graph.add_edge(START, "analyze_query")

    # Add conditional edges with routing logic
    print("🔀 Adding conditional edges...")

    # After query analysis, route based on success/error
    graph.add_conditional_edges(
        "analyze_query",
        route_after_analysis,
        {
            "retrieve_forms": "retrieve_forms",
            "handle_error": "handle_error"
        }
    )

    # After retrieving forms, check for errors or proceed
    graph.add_conditional_edges(
        "retrieve_forms",
        should_retry,
        {
            "analyze_query": "analyze_query",  # Retry from beginning
            "generate_response": "generate_response",  # Success path
            "end_with_error": "end_with_error"
        }
    )

    # After generating response, check if we need clarification or proceed to quality check
    def should_skip_quality_check(state: HandwritingState) -> str:
        """Skip quality check if we're asking for clarification."""
        needs_clarification = state.get("needs_clarification", False)
        if needs_clarification:
            print("⏭️ Skipping quality check - clarification question sent")
            return "END"
        return "quality_check"

    graph.add_conditional_edges(
        "generate_response",
        should_skip_quality_check,
        {
            "quality_check": "quality_check",
            "END": END
        }
    )

    # After quality check, decide if we need to improve or continue
    graph.add_conditional_edges(
        "quality_check",
        should_improve_response,
        {
            "generate_response": "generate_response",  # Retry response generation
            "follow_up": "follow_up"  # Continue to follow-up
        }
    )

    # After follow-up, end the conversation
    graph.add_edge("follow_up", END)

    # Error handling paths
    graph.add_conditional_edges(
        "handle_error",
        should_retry,
        {
            "analyze_query": "analyze_query",  # Retry from beginning
            "end_with_error": "end_with_error"  # Give up
        }
    )

    # Terminal error node
    graph.add_edge("end_with_error", END)

    # Compile graph - LangGraph API handles persistence automatically via thread_id
    print("⚙️ Compiling graph...")
    compiled_graph = graph.compile()

    print("✅ Handwriting Bot Graph compiled successfully!")
    print("📊 Graph structure:")
    print("   START -> analyze_query -> retrieve_forms -> generate_response -> quality_check -> follow_up -> END")
    print("   Error handling: handle_error -> end_with_error -> END")
    print("   Retry logic: Up to 3 retries for errors, up to 2 retries for low-quality responses")
    print("   💾 Memory: LangGraph API handles conversation persistence via thread_id")

    return compiled_graph

# Create the graph instance
handwriting_graph = create_handwriting_graph()

# Function to run the graph with a teacher's query
async def run_handwriting_bot(teacher_query: str, teacher_id: str = "teacher_001", session_id: str = "session_001", conversation_history: list = None, previous_metadata: dict = None):
    """
    Run the handwriting bot with a teacher's query.

    Args:
        teacher_query: The teacher's question about handwriting
        teacher_id: Unique identifier for the teacher
        session_id: Unique identifier for the conversation session
        conversation_history: Optional list of previous messages for context
        previous_metadata: Optional dict with previous analysis (query_type, target_letters, grade_level)

    Returns:
        Final state with the bot's response
    """
    from langchain_core.messages import HumanMessage

    print(f"🎯 Processing handwriting query: '{teacher_query[:50]}...'")

    # Use provided conversation history or create new message
    if conversation_history:
        messages = conversation_history
        print(f"📜 Using conversation history with {len(messages)} messages")
    else:
        messages = [HumanMessage(content=teacher_query)]

    # Use previous metadata if available (for follow-up queries)
    if previous_metadata is None:
        previous_metadata = {}

    # Create initial state with previous metadata to preserve context
    initial_state = {
        "messages": messages,  # Use full conversation history
        "teacher_id": teacher_id,
        "session_id": session_id,
        "original_query": teacher_query,
        "query_type": previous_metadata.get("query_type"),  # Preserve previous query type
        "target_letters": previous_metadata.get("target_letters", []),  # Preserve previous target letters
        "grade_level": previous_metadata.get("grade_level"),  # Preserve previous grade level
        "relevant_forms": [],
        "form_context": "",
        "response_generated": False,
        "response_quality_check": False,
        "retry_count": 0,
        "last_error": None,
        "needs_human_escalation": False,
        "conversation_depth": (len(messages) - 1) // 2 if conversation_history else 0,  # Calculate conversation depth
        "previous_topics": [],
        "follow_up_questions": []
    }

    print(f"🔍 Initial state - Target letters: {initial_state['target_letters']}, Grade: {initial_state['grade_level']}")
    
    # Configuration for the graph execution
    config = {
        "configurable": {
            "thread_id": f"{teacher_id}_{session_id}"
        }
    }
    
    try:
        # Execute the graph
        print("🚀 Executing handwriting bot graph...")
        final_state = await handwriting_graph.ainvoke(initial_state, config)
        
        print("✅ Graph execution completed!")
        return final_state
        
    except Exception as e:
        print(f"❌ Error executing handwriting bot: {str(e)}")
        # Return error state
        from langchain_core.messages import AIMessage
        error_message = AIMessage(content=f"I apologize, but I encountered an error: {str(e)}. Please try again.")
        return {
            **initial_state,
            "messages": initial_state["messages"] + [error_message],
            "last_error": str(e),
            "needs_human_escalation": True
        }

# Function to stream the graph execution (for real-time responses)
async def stream_handwriting_bot(teacher_query: str, teacher_id: str = "teacher_001", session_id: str = "session_001"):
    """
    Stream the handwriting bot execution for real-time responses.
    
    Args:
        teacher_query: The teacher's question about handwriting
        teacher_id: Unique identifier for the teacher
        session_id: Unique identifier for the conversation session
        
    Yields:
        State updates as the graph executes
    """
    from langchain_core.messages import HumanMessage
    
    print(f"🎯 Streaming handwriting query: '{teacher_query[:50]}...'")
    
    # Create initial state
    initial_state = {
        "messages": [HumanMessage(content=teacher_query)],
        "teacher_id": teacher_id,
        "session_id": session_id,
        "original_query": teacher_query,
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
    
    # Configuration for the graph execution
    config = {
        "configurable": {
            "thread_id": f"{teacher_id}_{session_id}"
        }
    }
    
    try:
        # Stream the graph execution
        print("🚀 Streaming handwriting bot graph...")
        async for chunk in handwriting_graph.astream(initial_state, config):
            yield chunk
            
        print("✅ Graph streaming completed!")
        
    except Exception as e:
        print(f"❌ Error streaming handwriting bot: {str(e)}")
        # Yield error state
        error_message = AIMessage(content=f"I apologize, but I encountered an error: {str(e)}. Please try again.")
        yield {
            "error": {
                **initial_state,
                "messages": initial_state["messages"] + [error_message],
                "last_error": str(e),
                "needs_human_escalation": True
            }
        }