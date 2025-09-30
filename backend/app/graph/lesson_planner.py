from typing import Optional, TypedDict

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import StateGraph, END
from app.config import settings

# Ensure LangSmith is initialized when this module is imported
settings.initialize_langsmith()


class LessonPlannerState(TypedDict):
    """State for the lesson planner graph."""
    topic: Optional[str]
    lesson_plan: Optional[str]


def ask_for_topic(state: LessonPlannerState) -> dict:
    """Node function that asks for the topic to create a lesson plan.
    
    Args:
        state: The current state of the lesson planner graph
        
    Returns:
        Dictionary to update the state with the lesson plan question
    """
    return {"lesson_plan": "What lesson plan do you want to make?"}


def generate_lesson_plan(state: LessonPlannerState) -> dict:
    """Node function that generates a lesson plan based on the topic.
    
    Args:
        state: The current state of the lesson planner graph
        
    Returns:
        Dictionary to update the state with the generated lesson plan
    """
    # Get OpenAI API key from settings
    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY is not configured in environment variables")
    
    # Initialize ChatOpenAI with the latest model and API key from settings
    llm = ChatOpenAI(
        model="gpt-4o",
        api_key=settings.openai_api_key.get_secret_value()
    )
    
    # Create a prompt template
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an educational expert who creates engaging and effective lesson plans. Generate a comprehensive lesson plan based on the given topic."),
        ("user", "Create a detailed lesson plan for the topic: {topic}. The lesson plan should include learning objectives, materials needed, activities, and assessment methods. Make it engaging and age-appropriate.")
    ])
    
    # Create the chain
    chain = prompt | llm | StrOutputParser()
    
    # Get the topic from state
    topic = state.get("topic", "general education")
    
    # Invoke the chain
    lesson_plan_content = chain.invoke({"topic": topic})
    
    return {"lesson_plan": lesson_plan_content}


# Create and compile the graph
def create_lesson_planner_graph():
    """Create and compile the lesson planner graph."""
    # Instantiate a StateGraph with the LessonPlannerState
    workflow = StateGraph(LessonPlannerState)
    
    # Add the nodes
    workflow.add_node("ask_for_topic", ask_for_topic)
    workflow.add_node("generate_lesson_plan", generate_lesson_plan)
    
    # Set the entry point
    workflow.set_entry_point("ask_for_topic")
    
    # Create an edge from ask_for_topic to generate_lesson_plan
    workflow.add_edge("ask_for_topic", "generate_lesson_plan")
    
    # Set the finish point from generate_lesson_plan
    workflow.add_edge("generate_lesson_plan", END)
    
    # Compile the graph into a runnable app object
    app = workflow.compile()
    
    return app


# Create the compiled graph
lesson_planner_app = create_lesson_planner_graph()