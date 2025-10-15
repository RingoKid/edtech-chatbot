# EdTech Chatbot - Technical Documentation

## Overview
An AI-powered educational chatbot system designed to assist teachers with handwriting, vocabulary, and creative writing instruction. The system uses LangGraph for orchestrating multi-agent conversations and OpenAI's GPT-4 for intelligent responses.

---

## Tech Stack

### Core Framework
- **FastAPI** - High-performance async web framework for building REST APIs
- **Python 3.x** - Primary programming language
- **Uvicorn** - ASGI server for running the FastAPI application

### AI/ML Libraries
- **LangGraph** - Framework for building stateful, multi-agent conversational AI systems
- **LangChain** - Framework for developing applications powered by language models
  - `langchain-core` - Core abstractions and interfaces
  - `langchain-openai` - OpenAI integration for LangChain
- **OpenAI GPT-4 (gpt-4o)** - Large language model for query analysis and response generation

### Database & Storage
- **AWS DynamoDB** - NoSQL database for storing:
  - Educational forms content (Forms A-H, I-L, M-Q)
  - Conversation history and session management
  - User metadata and preferences
- **boto3** - AWS SDK for Python (DynamoDB operations)

### Testing & Monitoring
- **LangSmith** - Tracing and monitoring for LangGraph/LangChain applications
- **pytest** - Testing framework
- **httpx** - Async HTTP client for testing

### Development Tools
- **Pydantic** - Data validation using Python type annotations
- **python-dotenv** - Environment variable management
- **Docker** (implied) - Containerization for deployment

---

## System Architecture

### High-Level Flow
```
User Query → Intent Classification → Router Graph → Specialized Bot → Response Generation
                                                    ↓
                                            [Handwriting Bot]
                                            [Vocabulary Bot]
                                            [Ideas Bot]
                                            [General Bot]
```

### Component Breakdown

#### 1. API Layer (`app/routers/`)
- **`educational_bot.py`** - Master routing endpoint with intent classification
- **`handwriting_bot.py`** - Standalone handwriting bot endpoint
- **`auth.py`** - Authentication routes
- **`users.py`** - User management routes
- **`health.py`** - Health check endpoints

#### 2. LangGraph Implementation (`app/graph/`)

##### Routing Graph (`routing_graph.py`)
- **Purpose**: Master orchestrator that routes queries to appropriate specialized bots
- **Nodes**:
  - `classify_intent` - Determines educational domain (handwriting/vocabulary/ideas/general)
  - `route_to_bot` - Routes to appropriate specialized bot based on intent
  - `aggregate_response` - Collects and formats final response
- **State**: `RoutingState` - Tracks intent, confidence, bot type, messages

##### Handwriting Bot Graph (`handwriting_graph.py`)
- **Purpose**: Specialized bot for letter formation, fine motor skills, pencil grip
- **Forms Used**: A-H
- **Nodes**:
  1. `analyze_query` - Extracts target letters, grade level, query type
  2. `retrieve_forms` - Fetches relevant educational forms from DynamoDB
  3. `generate_response` - Creates lesson plans or guidance using GPT-4
  4. `quality_check` - Validates response completeness (heuristic-based)
  5. `follow_up` - Generates contextual follow-up questions
  6. `handle_error` - Graceful error handling with fallback responses
- **State**: `HandwritingState` - Tracks letters, grade level, forms, conversation depth
- **Retry Logic**: Up to 3 retries for errors, 2 for quality improvements

##### Vocabulary Bot Graph (`vocabulary_graph.py`)
- **Purpose**: Specialized bot for phonics, spelling, sentence structure, reading
- **Forms Used**: I-L
- **Nodes**: Same structure as Handwriting Bot
  1. `analyze_query` - Identifies vocabulary type, target words, genre
  2. `retrieve_forms` - Fetches vocabulary-specific forms
  3. `generate_response` - Creates vocabulary instruction content
  4. `quality_check` - (Disabled for performance)
  5. `follow_up` - Vocabulary-specific follow-ups
- **State**: `VocabularyState` - Tracks vocabulary words, genre, sentence patterns

##### Ideas Bot Graph (`ideas_graph.py`)
- **Purpose**: Specialized bot for creative writing, brainstorming, story development
- **Forms Used**: M-Q
- **Nodes**: Same structure as other bots
  1. `analyze_query` - Identifies idea generation type, topic, genre
  2. `retrieve_forms` - Fetches creative writing forms
  3. `generate_response` - Creates idea generation activities
  4. `quality_check` - (Disabled for performance)
  5. `follow_up` - Creative writing follow-ups
- **State**: `IdeasState` - Tracks topics, genres, organization strategies

#### 3. Services (`app/service/`)

##### Intent Classification Service (`intent_classification_service.py`)
- **Model**: GPT-4 with structured output
- **Function**: Classifies teacher queries into 4 domains:
  - `handwriting` - Letter formation, fine motor, penmanship
  - `vocabulary` - Phonics, spelling, reading comprehension
  - `ideas` - Creative writing, brainstorming, story development
  - `general` - Multi-domain or classroom management
- **Output**: Intent label + confidence score (0-1)

##### Form Retrieval Service (`form_retrieval_service.py`)
- **Purpose**: Manages educational forms content from DynamoDB
- **Caching**: In-memory cache for performance
- **Methods**:
  - `get_handwriting_forms()` - Forms A-H
  - `get_vocabulary_forms()` - Forms I-L
  - `get_ideas_forms()` - Forms M-Q
  - `get_letter_specific_content(letters)` - Filters by target letters
  - `get_forms_by_query_type(type)` - Filters by query category
  - `build_context_string(forms)` - Formats forms for LLM context

##### Conversation Memory Service (`conversation_memory.py`)
- **Purpose**: Persists conversation history across sessions
- **Storage**: DynamoDB with structure:
  - `PK`: `CONVERSATION#{teacher_id}`
  - `SK`: `SESSION#{session_id}`
  - `messages`: Serialized LangChain messages
  - `metadata`: Query type, target letters, grade level
- **Methods**:
  - `save_conversation()` - Stores full conversation
  - `get_conversation()` - Retrieves message history
  - `get_conversation_with_metadata()` - Returns messages + metadata
  - `append_message()` - Adds single message to existing conversation
  - `clear_conversation()` - Deletes session

##### Specialized Bots Service (`specialized_bots.py`)
- **Purpose**: Individual bot logic for each domain
- **Bots**:
  - `HandwritingSpecialistBot` - Letter formation expert
  - `VocabularySpecialistBot` - Phonics and reading expert
  - `IdeasSpecialistBot` - Creative writing expert
  - `GeneralEducationBot` - Cross-domain expert

#### 4. Data Models (`app/schemas/`)
- **`intent.py`** - Intent classification request/response models
- **`chat.py`** - Chat request/response models
- **State schemas** - TypedDict definitions for graph states

#### 5. Configuration (`app/config.py`)
- Environment variable management using Pydantic Settings
- Required variables:
  - `OPENAI_API_KEY` - OpenAI API access
  - `AWS_REGION` - DynamoDB region
  - `DYNAMODB_TABLE_NAME` - Forms table name
  - `LANGSMITH_API_KEY` - Optional tracing
  - `LANGSMITH_PROJECT` - Optional project name

#### 6. Database (`app/database.py`)
- DynamoDB client initialization
- Table structure:
  - Educational forms with PK/SK pattern
  - Conversation history storage
  - Session management

---

## Core Logic & Workflows

### 1. Complete Chat Flow (`/educational-bot/chat`)

```
1. Receive user query + session info
2. Retrieve conversation history from DynamoDB (via conversation_memory)
3. Append new user message to history
4. Run routing graph:
   a. Classify intent using GPT-4 (handwriting/vocabulary/ideas/general)
   b. Evaluate confidence score
   c. Route to appropriate specialized bot
5. Specialized bot processes query:
   a. Analyze query (extract letters, grade, query type)
   b. Preserve context from previous messages (target letters, grade level)
   c. Retrieve relevant forms from DynamoDB
   d. Generate response using GPT-4 + forms context
   e. Quality check (heuristic-based)
   f. Generate follow-up questions
6. Save updated conversation history (messages + metadata)
7. Return response with intent, confidence, bot type, forms used
```

### 2. Handwriting Bot Lesson Plan Generation

```
1. Analyze query to extract:
   - Target letter(s) (e.g., "Z", "b and d")
   - Grade level (PreK, K, 1st)
   - Query type (letter_formation, fine_motor, spelling, etc.)

2. Check for incomplete queries:
   - If lesson request but no letter specified → Ask for letter
   - If letter specified but no grade → Ask for grade and objectives

3. Retrieve forms from DynamoDB:
   - Filter Forms A-H by target letters
   - Extract Form F (sequence verbal cues) and Form G (phoneme gestures)

4. Generate complete scripted lesson plan with 5 sections:
   A. Standards - Pre-K/K standards references
   B. Objectives - Specific, measurable goals for target letter
   C. Materials - All required materials
   D. Scripted Lesson Plan:
      - Section 1: Review & Connect (2-3 min)
      - Section 2: Model, Explain & Engage (8-10 min)
      - Section 3: Guided Practice (5-7 min)
      - Section 4: Application (5 min)
      - Section 5: Wrap-Up (2-3 min)

5. Quality check using heuristics (check for required sections)

6. Generate follow-up questions based on query type
```

### 3. Conversation Context Preservation

```
Problem: Follow-up queries may not specify previously mentioned details
Solution: Multi-layer context preservation

1. Store metadata with each conversation:
   - query_type (e.g., "letter_formation")
   - target_letters (e.g., ["Z"])
   - grade_level (e.g., "kindergarten")

2. When retrieving conversation:
   - Load full message history
   - Load previous metadata

3. During query analysis:
   - Extract info from current query
   - If current query missing info (e.g., no letters mentioned):
     → Use previous metadata values
   - Merge: current_value OR previous_value

4. Example:
   Query 1: "How do I teach letter Z to kindergarten?"
   → Stores: target_letters=["Z"], grade="kindergarten"

   Query 2: "Give me a lesson plan"
   → Retrieves: target_letters=["Z"], grade="kindergarten"
   → Generates: Lesson plan for letter Z, kindergarten level
```

### 4. Intent Classification Logic

```
Using GPT-4 with structured output:

Prompt includes:
- Domain definitions with keywords
- Example queries for each domain
- Confidence scoring criteria

Classification rules:
- confidence >= 0.7 → Route directly to specialist bot
- confidence 0.5-0.7 → Route to specialist with caution
- confidence < 0.5 → Route to general bot for clarification

Example classifications:
- "How do I teach letter Z?" → handwriting (0.95)
- "What are good sight words?" → vocabulary (0.90)
- "Help with story ideas" → ideas (0.85)
- "Help with writing" → general (0.40) - ambiguous
```

### 5. Form Retrieval & Context Building

```
1. Forms stored in DynamoDB with structure:
   PK: "FORM#A" (form letter)
   SK: "CONTENT"
   form_letter: "A"
   content: { sections, activities, cues, etc. }

2. Retrieval strategies:
   a. By letter: get_letter_specific_content(["Z"])
      → Returns all forms containing letter Z content

   b. By query type: get_forms_by_query_type("letter_formation")
      → Returns forms with letter formation sections

   c. By domain: get_handwriting_forms() / get_vocabulary_forms()
      → Returns all forms for that domain

3. Context building:
   - Concatenate relevant form sections
   - Limit to max_length (default 3500 chars) to fit in LLM context
   - Format as structured text for LLM to reference
   - Include form references (Form A, Form F, etc.)

4. LLM uses context to:
   - Extract exact sequence verbal cues (Form F)
   - Extract phoneme gestures (Form G)
   - Reference specific activities (Form D)
   - Apply evidence-based practices (Form E)
```

### 6. Error Handling & Retry Logic

```
All graphs implement 3-tier error handling:

1. Node-level try/catch:
   - Each node wrapped in try/except
   - Returns error state on failure
   - Preserves partial progress

2. Conditional retry routing:
   - After error, check retry_count
   - If retry_count < 3: Route back to analyze_query
   - If retry_count >= 3: Route to handle_error node

3. Graceful degradation:
   - handle_error_node provides fallback response
   - Includes general best practices
   - Sets needs_human_escalation flag
   - end_with_error_node for terminal failures

4. Example flow:
   analyze_query → (error) → handle_error → (retry 1) → analyze_query
   → (error) → handle_error → (retry 2) → analyze_query
   → (error) → handle_error → (retry 3) → end_with_error → END
```

### 7. LangSmith Tracing

```
Configured in each graph file:

if settings.langsmith_api_key and settings.langsmith_tracing:
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = settings.langsmith_api_key
    os.environ["LANGCHAIN_PROJECT"] = "project-name"

Traces capture:
- Node execution order and timing
- LLM calls with prompts and responses
- State transitions between nodes
- Error occurrences and retry attempts
- Token usage and costs

Useful for:
- Debugging conversation flows
- Optimizing prompt engineering
- Monitoring production performance
- Understanding user interaction patterns
```

---

## Key Design Patterns

### 1. State Management
- **TypedDict schemas** define state structure for each graph
- **Immutable updates** - nodes return dict updates, graph merges
- **State inheritance** - specialized bot states extend base state

### 2. Conditional Routing
- **Edge functions** determine next node based on state
- **Named routes** map edge function outputs to node names
- **Fallback paths** ensure graph always reaches END node

### 3. Conversation Context
- **Full message history** passed through state
- **Metadata persistence** in DynamoDB
- **Context merging** combines current + previous state

### 4. Service Layer Pattern
- **Singleton instances** (form_retrieval_service, conversation_memory)
- **Caching** - in-memory cache for frequently accessed data
- **Separation of concerns** - business logic isolated from graph logic

### 5. Prompt Engineering
- **Structured system prompts** with clear instructions
- **JSON-mode responses** for query analysis
- **Few-shot examples** in classification prompts
- **Context injection** - forms data inserted into user prompt

---

## Data Flow Example

### Teacher asks: "How do I teach letter Z to kindergarten?"

```
1. API receives POST /educational-bot/chat
   {
     "message": "How do I teach letter Z to kindergarten?",
     "teacher_id": "teacher_001",
     "session_id": "session_001"
   }

2. Conversation Memory retrieves history (empty - first message)

3. Routing Graph - classify_intent node:
   - LLM call to GPT-4: "Classify this teacher query..."
   - Response: {"intent": "handwriting", "confidence": 0.95}
   - State updated: intent="handwriting", confidence=0.95

4. Routing Graph - route_to_bot node:
   - Confidence 0.95 >= 0.7 → route to handwriting_specialist
   - Calls run_handwriting_bot()

5. Handwriting Graph - analyze_query node:
   - LLM call: "Extract target letters, grade, query type"
   - Response: {
       "query_type": "letter_formation",
       "target_letters": ["Z"],
       "grade_level": "kindergarten"
     }
   - State updated with extracted info

6. Handwriting Graph - retrieve_forms node:
   - DynamoDB query: Forms A-H where content contains "Z"
   - Returns Form A, Form F, Form G with Z-specific content
   - Builds context string (3500 chars max)

7. Handwriting Graph - generate_response node:
   - LLM call to GPT-4 with:
     * System prompt: "You are an expert handwriting instructor..."
     * User prompt: Query + target letter instruction + forms context
   - GPT-4 generates complete 5-section lesson plan for letter Z
   - Response stored as AIMessage in state

8. Handwriting Graph - quality_check node:
   - Heuristic check: Does response contain all 5 sections?
   - Yes → quality_score = 8, needs_improvement = False

9. Handwriting Graph - follow_up node:
   - Generates 3 contextual follow-up questions
   - State updated with follow_up_questions array

10. Graph reaches END node
    - Returns final_state to routing graph

11. Routing Graph - aggregate_response:
    - Extracts bot_response from messages
    - Formats final response

12. Conversation Memory saves:
    - Messages: [HumanMessage("How do I..."), AIMessage("Here's a lesson plan...")]
    - Metadata: {query_type: "letter_formation", target_letters: ["Z"], grade_level: "kindergarten"}

13. API returns ChatResponse:
    {
      "intent": "handwriting",
      "confidence": 0.95,
      "response": "Here's a complete lesson plan for teaching letter Z...",
      "bot_type": "handwriting_specialist",
      "relevant_forms": ["Form A", "Form F", "Form G"],
      "follow_up_questions": [...],
      "processing_time_ms": 4523.12
    }
```

---

## Performance Optimizations

1. **In-memory caching** - Form retrieval service caches forms after first load
2. **Quality check disabled** - Heuristic-based instead of LLM call to avoid timeouts
3. **Context truncation** - Forms content limited to 3500 chars to reduce tokens
4. **Async operations** - All nodes use async/await for non-blocking I/O
5. **Conversation depth tracking** - Skip quality checks for simple queries
6. **DynamoDB efficient queries** - Indexed by PK/SK for fast retrieval

---

## Testing Strategy

1. **Unit tests** - Test individual node functions
2. **Integration tests** - Test complete graph flows
3. **Endpoint tests** - Test API routes with httpx
4. **Test queries endpoint** - `/educational-bot/test-queries` provides sample queries
5. **Health checks** - Verify all components operational

---

## Deployment

- **LangGraph Studio** - Local development and testing
- **langgraph.json** - Configuration for LangGraph deployment
- **startup.sh** - Initialization script for loading forms
- **Docker** - Containerized deployment (implied)
- **AWS Infrastructure** - DynamoDB for data persistence

---

## Environment Variables

```
# Required
OPENAI_API_KEY=sk-...
AWS_REGION=us-east-1
DYNAMODB_TABLE_NAME=edtech-forms

# Optional - LangSmith Tracing
LANGSMITH_API_KEY=lsv2_...
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=edtech-chatbot

# Optional - Auth
JWT_SECRET_KEY=...
```

---

## API Endpoints

### Master Router
- `POST /educational-bot/chat` - Complete routing + specialized bot
- `POST /educational-bot/classify-intent` - Intent classification only
- `GET /educational-bot/domains` - Domain information
- `GET /educational-bot/test-queries` - Sample test queries
- `GET /educational-bot/forms-status` - Forms loading status
- `GET /educational-bot/health` - Health check

### Handwriting Bot (Direct Access)
- `POST /handwriting-bot/chat` - Direct handwriting bot
- `GET /handwriting-bot/test-forms` - Test form retrieval
- `GET /handwriting-bot/test-queries` - Handwriting test queries
- `GET /handwriting-bot/health` - Health check

### System
- `GET /health` - Overall system health
- `POST /auth/*` - Authentication endpoints
- `GET /users/*` - User management endpoints

---

## Dependencies

### Core Dependencies
```
fastapi==0.115.6
uvicorn==0.34.0
langgraph==0.2.59
langchain-core==0.3.29
langchain-openai==0.2.14
langchain-community==0.3.14
openai==1.59.3
boto3==1.35.93
pydantic==2.10.4
python-dotenv==1.0.1
```

### Development Dependencies
```
pytest==8.3.4
httpx==0.28.1
pytest-asyncio==0.25.2
```

### Full list in `requirements.txt`