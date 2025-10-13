"""
Simplified Routing Graph for LangGraph Studio visualization.
This version removes complex dependencies to ensure it loads properly.
"""
from typing import Dict, Any
from langgraph.graph import StateGraph, END, START
from langchain_core.messages import HumanMessage, AIMessage
from app.graph.routing_state import RoutingState

async def simple_classify_intent_node(state: RoutingState) -> Dict[str, Any]:
    """Simplified intent classification node for demo purposes."""
    messages = state.get("messages", [])
    if not messages:
        return {"intent": "general", "confidence": 0.5}
    
    query = messages[-1].content if hasattr(messages[-1], 'content') else str(messages[-1])
    
    # Simple keyword-based classification for demo
    query_lower = query.lower()
    
    if any(word in query_lower for word in ["letter", "handwriting", "write", "pencil", "grip"]):
        intent = "handwriting"
        confidence = 0.8
    elif any(word in query_lower for word in ["word", "vocabulary", "spelling", "reading", "phonics"]):
        intent = "vocabulary" 
        confidence = 0.8
    elif any(word in query_lower for word in ["story", "creative", "ideas", "brainstorm", "narrative"]):
        intent = "ideas"
        confidence = 0.8
    else:
        intent = "general"
        confidence = 0.6
    
    return {
        "original_query": query,
        "intent": intent,
        "confidence": confidence,
        "classification_reasoning": f"Keyword-based classification identified as {intent}",
        "processing_steps": [f"Intent: {intent} ({confidence})"]
    }

async def simple_route_decision_node(state: RoutingState) -> Dict[str, Any]:
    """Simple routing decision node."""
    intent = state.get("intent", "general")
    confidence = state.get("confidence", 0.5)
    
    if confidence >= 0.7:
        target_bot = intent
    else:
        target_bot = "general"
    
    return {
        "target_bot": target_bot,
        "routing_decision": f"Routing to {target_bot} bot based on {intent} intent with {confidence} confidence"
    }

async def simple_response_node(state: RoutingState) -> Dict[str, Any]:
    """Generate a simple response based on the target bot."""
    target_bot = state.get("target_bot", "general")
    original_query = state.get("original_query", "")
    
    responses = {
        "handwriting": f"🖊️ **Handwriting Specialist Response**\n\nFor your question about '{original_query}', here are some handwriting strategies:\n\n• Focus on proper pencil grip\n• Practice letter formation with guided lines\n• Use multi-sensory approaches\n• Strengthen fine motor skills with activities",
        "vocabulary": f"📚 **Vocabulary Specialist Response**\n\nFor your question about '{original_query}', here are some vocabulary strategies:\n\n• Use sight word practice\n• Implement phonics instruction\n• Create word walls and word banks\n• Practice with context clues",
        "ideas": f"💡 **Ideas Specialist Response**\n\nFor your question about '{original_query}', here are some creative writing ideas:\n\n• Use story starters and prompts\n• Encourage brainstorming sessions\n• Try different narrative structures\n• Celebrate creative expression",
        "general": f"🎓 **General Education Response**\n\nFor your question about '{original_query}', here are some general strategies:\n\n• Consider differentiated instruction\n• Use assessment to guide instruction\n• Create supportive learning environments\n• Engage with families and communities"
    }
    
    response_content = responses.get(target_bot, responses["general"])
    ai_message = AIMessage(content=response_content)
    
    return {
        "messages": [ai_message],
        "bot_response": response_content,
        "bot_type": f"{target_bot}_specialist",
        "relevant_forms": [f"Forms relevant to {target_bot}"],
        "follow_up_questions": [f"Would you like more specific {target_bot} strategies?"]
    }

def create_simple_routing_graph():
    """Create a simplified routing graph for LangGraph Studio."""
    print("🔧 Building Simple Routing Graph for Studio...")
    
    # Initialize the graph
    graph = StateGraph(RoutingState)
    
    # Add nodes
    graph.add_node("classify_intent", simple_classify_intent_node)
    graph.add_node("route_decision", simple_route_decision_node)
    graph.add_node("generate_response", simple_response_node)
    
    # Set entry point
    graph.add_edge(START, "classify_intent")
    
    # Add edges
    graph.add_edge("classify_intent", "route_decision")
    graph.add_edge("route_decision", "generate_response")
    graph.add_edge("generate_response", END)
    
    # Compile the graph
    compiled_graph = graph.compile()
    
    print("✅ Simple Routing Graph compiled successfully!")
    return compiled_graph

# Create the simple graph instance
simple_routing_graph = create_simple_routing_graph()