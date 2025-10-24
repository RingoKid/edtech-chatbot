from langchain_core.messages import AIMessage, SystemMessage  # type: ignore[import-not-found]
from app.graph.state import GraphState
from app.schemas.task_route import TaskRoute
from app.schemas.lesson_params import HandwritingParams, VocabularyParams, IdeaGenerationParams
from app.graph.context import Context
from app.graph.prompts import (
    GREETING_WELCOME_MESSAGE,
    MAIN_ROUTER_SYSTEM_PROMPT,
    MAIN_ROUTER_ERROR_MESSAGE,
    MAIN_ROUTER_CLARIFICATION_MESSAGE,
    HANDWRITING_STUB_MESSAGE,
    VOCABULARY_STUB_MESSAGE,
    IDEA_GENERATION_STUB_MESSAGE,
)
from pydantic import BaseModel, Field, ValidationError, create_model
from typing import get_origin, get_args, Literal


ALLOWED_TASKS = {"Handwriting", "Vocabulary", "Idea Generation"}


def greeting_node(state: GraphState) -> dict:
    """
    Greets the user and presents the main task options.
    """
    welcome_message = AIMessage(content=GREETING_WELCOME_MESSAGE)
    return {"messages": [welcome_message]}


def main_router(state: GraphState) -> dict:
    """
    Routes the user's choice to the appropriate task node.
    Uses structured output with Pydantic to classify the user's intent.
    If the intent is unclear, sets task_name to __CLARIFY__.
    """
    # Get the context and LLM with structured output
    context = Context()
    llm = context.model
    structured_llm = llm.with_structured_output(TaskRoute, strict=True)

    # Get the last message (user's choice)
    last_message = state["messages"][-1]

    # Create a system message to guide the classification
    system_prompt = SystemMessage(content=MAIN_ROUTER_SYSTEM_PROMPT)

    try:
        # Invoke the LLM with structured output, including system prompt
        route = structured_llm.invoke([system_prompt, last_message])
        task_name = route.task_name

        # Check if LLM explicitly requested clarification
        if task_name == "__CLARIFY__":
            print(f"DEBUG: LLM requested clarification")
            return {"task_name": "__CLARIFY__"}
        
        # On successful task classification, update task_name
        print(f"DEBUG: Successfully routed to {task_name}")
        return {"task_name": task_name}
    except Exception as e:
        # On failure (e.g., validation error), treat as clarification needed
        print(f"DEBUG: Routing failed with error: {e}")
        return {"task_name": "__CLARIFY__"}


def clarification_node(state: GraphState) -> dict:
    """
    Sends a clarification message when the user's intent is unclear.
    """
    clarification_message = AIMessage(content=MAIN_ROUTER_CLARIFICATION_MESSAGE)
    return {"messages": [clarification_message]}


def setup_handwriting(state: GraphState) -> dict:
    """
    Setup node for handwriting task. Initializes parameter collection state.
    """
    param_names = list(HandwritingParams.model_fields.keys())
    return {
        "parameter_schema_name": "HandwritingParams",
        "required_parameters": param_names,
        "collected_parameters": {},
        "current_question": None,
        "collection_error_message": None
    }


def setup_vocabulary(state: GraphState) -> dict:
    """
    Setup node for vocabulary task. Initializes parameter collection state.
    """
    param_names = list(VocabularyParams.model_fields.keys())
    return {
        "parameter_schema_name": "VocabularyParams",
        "required_parameters": param_names,
        "collected_parameters": {},
        "current_question": None,
        "collection_error_message": None
    }


def setup_idea_generation(state: GraphState) -> dict:
    """
    Setup node for idea generation task. Initializes parameter collection state.
    """
    param_names = list(IdeaGenerationParams.model_fields.keys())
    return {
        "parameter_schema_name": "IdeaGenerationParams",
        "required_parameters": param_names,
        "collected_parameters": {},
        "current_question": None,
        "collection_error_message": None
    }


# Schema registry for looking up classes by name
SCHEMA_REGISTRY = {
    "HandwritingParams": HandwritingParams,
    "VocabularyParams": VocabularyParams,
    "IdeaGenerationParams": IdeaGenerationParams
}


def collect_parameters_node(state: GraphState) -> dict:
    """
    Collects parameters dynamically based on the parameter_schema.
    Asks questions, extracts values, validates, and loops until all required parameters are collected.
    """
    # Get state values
    messages = state["messages"]
    parameter_schema_name = state.get("parameter_schema_name")
    required_parameters = state.get("required_parameters", []).copy()  # Make a copy to avoid mutation issues
    collected_parameters = state.get("collected_parameters", {}).copy()  # Make a copy
    error_to_show = state.get("collection_error_message")
    
    # Look up the actual schema class
    parameter_schema = SCHEMA_REGISTRY.get(parameter_schema_name) if parameter_schema_name else None
    
    # Initialize
    next_question = None
    ai_message_content = None
    
    # Get context and LLM
    context = Context()
    llm = context.model
    
    print(f"DEBUG collect_parameters_node: required_parameters={required_parameters}, collected_parameters={collected_parameters}")
    
    # Check if this is the first time entering collection (no question asked yet)
    is_first_entry = state.get("current_question") is None and required_parameters
    
    # Attempt extraction if we have a user response (but not on first entry)
    if not is_first_entry and required_parameters and len(messages) > 0 and hasattr(messages[-1], 'type') and messages[-1].type == 'human':
        print(f"DEBUG: Attempting extraction, is_first_entry={is_first_entry}")
        param_to_extract = required_parameters[0]
        field_definition = parameter_schema.model_fields[param_to_extract]
        user_response = messages[-1].content.strip()
        
        print(f"DEBUG: User response: {user_response}")
        
        # Create single-field model for extraction
        SingleFieldModel = create_model(
            f"Dynamic_{param_to_extract}",
            __base__=BaseModel,
            value=(field_definition.annotation, Field(..., description=field_definition.description))
        )
        
        # Bind to LLM
        extractor_llm = llm.with_structured_output(SingleFieldModel, strict=True)
        
        try:
            # Invoke LLM to extract the value
            extracted_result = extractor_llm.invoke(user_response)
            extracted_value = extracted_result.value
            
            print(f"DEBUG: LLM extracted {param_to_extract}={extracted_value}")
            
            # Check if LLM indicated clarification is needed
            if extracted_value == "__CLARIFY__":
                print(f"DEBUG: LLM indicated clarification needed")
                error_to_show = "Sorry, I didn't quite understand that. Could you please try again?"
                # Don't modify collected_parameters or required_parameters - stay on same question
            else:
                # Success: add to collected and remove from required
                print(f"DEBUG: Successfully extracted {param_to_extract}={extracted_value}")
                collected_parameters[param_to_extract] = extracted_value
                required_parameters = required_parameters[1:]  # Remove first item
                error_to_show = None
            
        except ValidationError as e:
            print(f"DEBUG: ValidationError: {e}")
            # Validation error - re-ask the question
            error_to_show = "Sorry, I didn't quite understand that. Could you please try again?"
        except Exception as e:
            print(f"DEBUG: Exception during extraction: {e}")
            # Other error - re-ask the question
            error_to_show = "Sorry, I didn't quite understand that. Could you please try again?"
    
    # Determine next action
    if not required_parameters:
        # All parameters collected
        print(f"DEBUG: All parameters collected! collected_parameters={collected_parameters}")
        next_question = None
        error_to_show = None
    else:
        # Still have parameters to collect
        next_param_name = required_parameters[0]
        field_info = parameter_schema.model_fields[next_param_name]
        
        # Generate question from field description
        next_question = field_info.description
        
        # Check if it's a Literal type and add options
        origin = get_origin(field_info.annotation)
        if origin is Literal:
            choices = get_args(field_info.annotation)
            # Filter out __CLARIFY__ from displayed options
            user_choices = [c for c in choices if c != "__CLARIFY__"]
            next_question += f" Please choose one of: {', '.join(user_choices)}."
        
        print(f"DEBUG: Generated question: {next_question}")
    
    # Prepare AI message
    if error_to_show and next_question:
        ai_message_content = f"{error_to_show}\n\n{next_question}"
    elif error_to_show:
        ai_message_content = error_to_show
    elif next_question:
        ai_message_content = next_question
    
    print(f"DEBUG: ai_message_content={ai_message_content}")
    
    # Return state update
    result = {
        "required_parameters": required_parameters,
        "collected_parameters": collected_parameters,
        "current_question": next_question,
        "collection_error_message": error_to_show
    }
    
    if ai_message_content:
        result["messages"] = [AIMessage(content=ai_message_content)]
    
    print(f"DEBUG: Returning result with required_parameters={result['required_parameters']}")
    
    return result


def stub_generate_lesson_node(state: GraphState) -> dict:
    """
    Stub node for lesson generation. Will be implemented later.
    """
    collected_params = state.get("collected_parameters", {})
    
    # Format the collected parameters nicely
    param_str = ", ".join([f"{k}: {v}" for k, v in collected_params.items()])
    
    stub_message = AIMessage(content=f"Lesson generation coming soon! Parameters collected: {param_str}")
    return {"messages": [stub_message]}


def route_from_main_router(state: GraphState) -> str:
    """
    Routing function to determine the next node after main_router.
    Returns the name of the next node based on the task_name in state.
    """
    task_name = state.get("task_name")

    if task_name == "Handwriting":
        return "handwriting"
    elif task_name == "Vocabulary":
        return "vocabulary"
    elif task_name == "Idea Generation":
        return "idea_generation"
    elif task_name == "__CLARIFY__":
        # Route to clarification node
        return "clarification"
    else:
        # Fallback - should not happen
        return "clarification"


def wait_for_user_input(state: GraphState) -> dict:
    """
    Dummy node that serves as an interrupt point while waiting for user input.
    This node does nothing - it just provides a place to interrupt the graph.
    """
    return {}


def route_parameter_collection(state: GraphState) -> str:
    """
    Routing function for parameter collection loop.
    Returns 'wait_for_input' if more params needed, 'generate_lesson' if done.
    """
    required_parameters = state.get("required_parameters", [])
    
    if not required_parameters:
        return "generate_lesson"
    else:
        return "wait_for_input"
