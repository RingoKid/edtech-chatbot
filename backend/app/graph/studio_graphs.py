"""
LangGraph Studio configuration file for educational chatbot visualization.
Defines all graphs available in the studio interface with LangSmith tracing.
"""
import os
from app.graph.graph import graph as lesson_planner_graph
from app.graph.handwriting_graph import handwriting_graph
from app.graph.routing_graph import routing_graph
from app.config import settings

# Initialize LangSmith tracing for Studio visualization
if settings.langsmith_api_key and settings.langsmith_tracing:
    os.environ["LANGCHAIN_TRACING_V2"] = str(settings.langsmith_tracing)
    os.environ["LANGCHAIN_API_KEY"] = settings.langsmith_api_key
    os.environ["LANGCHAIN_PROJECT"] = settings.langsmith_project or "educational-chatbot-studio"
    print(f"✅ LangSmith tracing enabled for LangGraph Studio: {settings.langsmith_project}")

# Main educational chatbot graph (the complete flow)
educational_chatbot_graph = routing_graph

# Export graphs for LangGraph Studio
__all__ = [
    "lesson_planner_graph",
    "handwriting_graph", 
    "routing_graph",
    "educational_chatbot_graph"
]

# Graph metadata for Studio with enhanced descriptions
graphs = {
    "lesson_planner": {
        "graph": lesson_planner_graph,
        "title": "📚 Interactive Lesson Planner",
        "description": "Original lesson planning graph with topic selection and user interaction",
        "nodes": ["ask_for_topic"],
        "use_case": "General lesson planning with conditional interrupts",
        "domain": "General Education",
        "complexity": "Simple"
    },
    "handwriting_bot": {
        "graph": handwriting_graph,
        "title": "✍️ Handwriting & Spelling Specialist",
        "description": "Specialized bot for handwriting instruction using educational Forms A-H",
        "nodes": ["analyze_query", "retrieve_forms", "generate_response", "quality_check", "follow_up", "handle_error"],
        "use_case": "Letter formation, fine motor skills, spelling support, handwriting assessment",
        "domain": "Handwriting & Motor Skills",
        "complexity": "Advanced"
    },
    "routing_system": {
        "graph": routing_graph,
        "title": "🎯 Educational Domain Router",
        "description": "Master routing system with AI-powered intent classification for all domains",
        "nodes": ["classify_intent", "route_to_bot", "execute_handwriting_bot", "execute_vocabulary_bot", "execute_ideas_bot", "execute_general_bot"],
        "use_case": "Complete educational chatbot with automatic domain detection and routing",
        "domain": "Multi-Domain Routing",
        "complexity": "Complex"
    },
    "educational_chatbot": {
        "graph": educational_chatbot_graph,
        "title": "🤖 Complete Educational Chatbot",
        "description": "Full educational assistant with intent classification and specialized domain routing",
        "nodes": ["classify_intent", "route_to_bot", "execute_handwriting_bot", "execute_vocabulary_bot", "execute_ideas_bot", "execute_general_bot"],
        "use_case": "Production-ready educational chatbot for teachers",
        "domain": "Complete System",
        "complexity": "Production"
    }
}

print("📊 LangGraph Studio graphs configured:")
for key, info in graphs.items():
    print(f"   - {key}: {info['title']}")
print("🔗 Studio URL: http://localhost:2024")
print("📈 LangSmith URL: https://smith.langchain.com/")