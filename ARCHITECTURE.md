# EdTech Chatbot Architecture

## System Overview

The EdTech Chatbot is an AI-powered teaching assistant for early childhood literacy education, built using **LangGraph** for intelligent routing and **LangChain** for LLM orchestration. The system provides specialized instruction across three domains: Handwriting & Spelling, Vocabulary & Sentence Structure, and Idea Generation & Organization.

---

## Architecture Diagram

```mermaid
graph TB
    subgraph "Frontend - React"
        A[User Interface]
        A1[Chatbot Component]
        A2[API Client]
        A --> A1
        A1 --> A2
    end

    subgraph "Backend - FastAPI"
        B[FastAPI Main]
        C[Chat Router /chat2]
        D[Chat Service]
        B --> C
        C --> D
    end

    subgraph "LangGraph Routing System"
        E[Studio Router Graph]
        E1[Router Node<br/>routing_decision_node]
        E1A[Intent Classification]
        E1B[Complexity Detection]

        E --> E1
        E1 --> E1A
        E1 --> E1B
    end

    subgraph "Specialized Bots"
        F[General Bot<br/>general_bot_response_node]
        G[Handwriting Specialist<br/>execute_handwriting_specialist_node]
        H[Vocabulary Specialist<br/>execute_vocabulary_specialist_node]
        I[Ideas Specialist<br/>execute_ideas_specialist_node]
    end

    subgraph "Supporting Services"
        J[Form Retrieval Service]
        K[Intent Classification Service]
    end

    subgraph "Data Layer"
        M[(DynamoDB<br/>Forms A-Q, Standards)]
        N[(SQLite Checkpointer<br/>conversations.db)]
    end

    subgraph "External APIs"
        O[OpenAI GPT-4o]
    end

    A2 -->|HTTP POST/WebSocket| B
    D -->|ainvoke with config| E
    D -->|Load/Save Thread State| N

    E1 -->|route_after_router| F
    E1 -->|route_after_router| G
    E1 -->|route_after_router| H
    E1 -->|route_after_router| I

    E1A --> K
    K --> O
    E1B -->|Hybrid: Rules + LLM| O

    F --> J
    G --> J
    H --> J
    I --> J

    J --> M

    F -->|Generate Response| O
    G -->|Generate Lesson Plan| O
    H -->|Generate Lesson Plan| O
    I -->|Generate Lesson Plan| O

    style E fill:#e1f5ff
    style E1 fill:#b3e5fc
    style F fill:#c8e6c9
    style G fill:#ffccbc
    style H fill:#f8bbd0
    style I fill:#e1bee7
    style M fill:#fff9c4
    style N fill:#fff9c4
    style O fill:#ffecb3
    style K fill:#e8f5e9
```

---

## System Flow Diagram

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant FastAPI
    participant ChatService
    participant RouterGraph
    participant RouterNode
    participant IntentClassifier
    participant SpecialistBot
    participant FormRetrieval
    participant DynamoDB
    participant OpenAI
    participant Checkpointer

    User->>Frontend: Send message
    Frontend->>FastAPI: POST /chat2/message
    FastAPI->>ChatService: process_chat_request()
    ChatService->>Checkpointer: Load conversation history
    Checkpointer-->>ChatService: Previous messages
    ChatService->>RouterGraph: ainvoke(input_state, config)

    RouterGraph->>RouterNode: Process query
    RouterNode->>IntentClassifier: classify_intent()
    IntentClassifier->>OpenAI: Classify intent
    OpenAI-->>IntentClassifier: Intent classification
    IntentClassifier-->>RouterNode: Intent + confidence

    RouterNode->>RouterNode: detect_complexity()
    RouterNode-->>RouterGraph: Routing decision

    alt Simple Query
        RouterGraph->>SpecialistBot: General Bot
    else Complex Query - Handwriting
        RouterGraph->>SpecialistBot: Handwriting Specialist
    else Complex Query - Vocabulary
        RouterGraph->>SpecialistBot: Vocabulary Specialist
    else Complex Query - Ideas
        RouterGraph->>SpecialistBot: Ideas Specialist
    end

    SpecialistBot->>FormRetrieval: Retrieve relevant forms
    FormRetrieval->>DynamoDB: Query forms by category
    DynamoDB-->>FormRetrieval: Form content
    FormRetrieval-->>SpecialistBot: Formatted context

    SpecialistBot->>OpenAI: Generate response with context
    OpenAI-->>SpecialistBot: AI response
    SpecialistBot-->>RouterGraph: Bot response

    RouterGraph->>Checkpointer: Save conversation state
    RouterGraph-->>ChatService: Final response
    ChatService-->>FastAPI: ChatMessageResponse
    FastAPI-->>Frontend: JSON response
    Frontend-->>User: Display message
```

---

## Detailed Component Architecture

```mermaid
graph TB
    subgraph "Router Node Detail"
        RN1[Extract Query]
        RN2[Intent Classification]
        RN3[Complexity Detection]
        RN4[Routing Decision]
        RN5[Conversation Context]

        RN1 --> RN2
        RN1 --> RN3
        RN5 --> RN2
        RN5 --> RN3
        RN2 --> RN4
        RN3 --> RN4
    end

    subgraph "Handwriting Specialist Detail"
        HS1[Analyze Query Node]
        HS2[Retrieve Forms Node]
        HS3[Generate Response Node]
        HS4[Quality Check Node]
        HS5[Follow-up Node]

        HS1 --> HS2
        HS2 --> HS3
        HS3 --> HS4
        HS4 --> HS5
    end

    subgraph "Form Retrieval Service Detail"
        FR1[Get Forms by Category]
        FR2[Letter-Specific Content]
        FR3[Formation Cues]
        FR4[Phoneme Gestures]
        FR5[Standards by Grade]
        FR6[Build Context String]

        FR1 --> FR6
        FR2 --> FR6
        FR3 --> FR6
        FR4 --> FR6
        FR5 --> FR6
    end

    RN4 -->|handwriting| HS1
    HS2 --> FR1

    style RN4 fill:#b3e5fc
    style HS1 fill:#ffccbc
    style FR6 fill:#fff9c4
```

---

## Data Flow Architecture

```mermaid
graph LR
    subgraph "Input Layer"
        I1[User Query]
        I2[Thread ID]
        I3[Session ID]
    end

    subgraph "Processing Layer"
        P1[Intent Classification]
        P2[Complexity Detection]
        P3[Conversation History]
        P4[Form Context Retrieval]
        P5[LLM Prompt Engineering]
    end

    subgraph "State Management"
        S1[RoutingState]
        S2[HandwritingState]
        S3[Messages Array]
        S4[Checkpointer Storage]
    end

    subgraph "Output Layer"
        O1[AI Response]
        O2[Bot Type]
        O3[Relevant Forms]
        O4[Follow-up Questions]
    end

    I1 --> P1
    I1 --> P2
    I2 --> P3
    I3 --> P3

    P1 --> S1
    P2 --> S1
    P3 --> S3
    P4 --> S1

    S1 --> P5
    S2 --> P5
    S3 --> P5

    P5 --> O1
    S1 --> O2
    S1 --> O3
    S1 --> O4

    S1 --> S4
    S2 --> S4
    S3 --> S4

    style P1 fill:#e1f5ff
    style P5 fill:#ffecb3
    style S4 fill:#fff9c4
    style O1 fill:#c8e6c9
```

---

## Technology Stack

```mermaid
graph TB
    subgraph "Frontend Stack"
        FE1[React 19.1.1]
        FE2[Vite 7.1.6]
        FE3[TailwindCSS 3.4.17]
        FE4[Framer Motion 12.23.16]
        FE5[React Markdown 10.1.0]
        FE6[React Router 7.9.1]
    end

    subgraph "Backend Stack"
        BE1[Python 3.x]
        BE2[FastAPI 0.116.2]
        BE3[LangGraph 1.0.0a3]
        BE4[LangChain 1.0.0a9]
        BE5[LangChain OpenAI 0.3.33]
        BE6[Uvicorn 0.35.0]
    end

    subgraph "AI/ML Layer"
        AI1[OpenAI GPT-4o]
        AI2[LangSmith 0.4.28]
        AI3[LangGraph SDK 0.2.7]
    end

    subgraph "Data Storage"
        DB1[DynamoDB]
        DB2[SQLite Checkpointer]
        DB3[LangGraph Checkpoint 2.1.1]
    end

    subgraph "Infrastructure"
        IN1[AWS App Runner]
        IN2[AWS DynamoDB]
        IN3[WebSocket Support]
    end

    FE1 --> BE2
    BE2 --> BE3
    BE3 --> BE4
    BE4 --> BE5
    BE5 --> AI1

    BE3 --> DB2
    BE2 --> DB1
    DB2 --> DB3

    BE2 --> IN1
    DB1 --> IN2
    BE2 --> IN3

    style AI1 fill:#ffecb3
    style DB1 fill:#fff9c4
    style DB2 fill:#fff9c4
    style IN1 fill:#e1bee7
```

---

## Routing Logic Flow

```mermaid
flowchart TD
    A[User Query] --> B{Intent Classification}

    B -->|handwriting| C{Complexity Detection}
    B -->|vocabulary| C
    B -->|ideas| C
    B -->|general| C
    B -->|out_of_scope| D[General Bot - Decline]

    C -->|simple| E[General Bot]
    C -->|complex + handwriting| F[Handwriting Specialist]
    C -->|complex + vocabulary| G[Vocabulary Specialist]
    C -->|complex + ideas| H[Ideas Specialist]
    C -->|complex + general| E

    E --> I[Quick Answer/Tips]
    F --> J[Structured Lesson Plan]
    G --> K[Vocabulary Lesson]
    H --> L[Ideas Lesson]
    D --> M[Scope Boundary Message]

    I --> N[Response to User]
    J --> N
    K --> N
    L --> N
    M --> N

    style B fill:#e1f5ff
    style C fill:#b3e5fc
    style F fill:#ffccbc
    style G fill:#f8bbd0
    style H fill:#e1bee7
    style E fill:#c8e6c9
```

---

## Conversation Memory Architecture

```mermaid
graph TB
    subgraph "Conversation Flow"
        CF1[User Message 1]
        CF2[Bot Response 1]
        CF3[User Message 2]
        CF4[Bot Response 2]
        CF5[User Message N]
        CF6[Bot Response N]

        CF1 --> CF2
        CF2 --> CF3
        CF3 --> CF4
        CF4 --> CF5
        CF5 --> CF6
    end

    subgraph "Memory Layer"
        ML1[Messages Array]
        ML2[Thread ID]
        ML3[Checkpointer]
        ML4[SQLite Storage]

        ML2 --> ML3
        ML3 --> ML4
    end

    subgraph "Context Management"
        CM1[Previous Intents]
        CM2[Target Letters]
        CM3[Grade Level]
        CM4[Conversation Depth]
        CM5[Specialist Topic]

        CM1 --> CM5
        CM2 --> CM5
        CM3 --> CM5
        CM4 --> CM5
    end

    CF1 --> ML1
    CF2 --> ML1
    CF3 --> ML1
    CF4 --> ML1
    CF5 --> ML1
    CF6 --> ML1

    ML1 --> ML3
    ML3 --> CM1
    ML3 --> CM2
    ML3 --> CM3
    ML3 --> CM4

    style ML3 fill:#fff9c4
    style ML4 fill:#fff9c4
    style CM5 fill:#e1f5ff
```

---

## State Schema Architecture

```mermaid
classDiagram
    class RoutingState {
        +List~BaseMessage~ messages
        +str teacher_id
        +str session_id
        +str original_query
        +IntentType intent
        +float confidence
        +str classification_reasoning
        +str complexity
        +str target_bot
        +str routing_decision
        +bool needs_specialist
        +str specialist_topic
        +str bot_response
        +str bot_type
        +List~str~ relevant_forms
        +List~str~ follow_up_questions
        +List~str~ processing_steps
        +float total_processing_time
        +bool needs_clarification
        +str last_error
        +int retry_count
        +int conversation_depth
        +List~str~ previous_intents
    }

    class HandwritingState {
        +List~BaseMessage~ messages
        +str teacher_id
        +str session_id
        +str original_query
        +str query_type
        +List~str~ target_letters
        +str grade_level
        +List~str~ relevant_forms
        +str form_context
        +bool response_generated
        +bool response_quality_check
        +int retry_count
        +str last_error
        +bool needs_human_escalation
        +int conversation_depth
        +List~str~ previous_topics
        +List~str~ follow_up_questions
    }

    class IntentResult {
        +IntentType intent
        +float confidence
        +str reasoning
        +List~str~ suggested_forms
    }

    class ChatMessageRequest {
        +str message
        +str thread_id
    }

    class ChatMessageResponse {
        +str thread_id
        +str reply
    }

    RoutingState ..> IntentResult
    ChatMessageRequest ..> RoutingState
    RoutingState ..> HandwritingState
    HandwritingState ..> ChatMessageResponse
```

---

## Form Data Structure

```mermaid
graph TB
    subgraph "Educational Forms A-Q"
        FA[Forms A-H: Handwriting]
        FB[Forms I-L: Vocabulary]
        FC[Forms M-Q: Ideas]
    end

    subgraph "Handwriting Forms A-H"
        HA[Form A: Objectives]
        HB[Form B: Structure]
        HC[Form C: Template]
        HD[Form D: Activities]
        HE[Form E: Evidence-Based Practices]
        HF[Form F: Sequence Verbal Cues]
        HG[Form G: Phoneme Gestures]
        HH[Form H: Adaptations]
    end

    subgraph "Vocabulary Forms I-L"
        VI[Form I: Structure]
        VJ[Form J: Template]
        VK[Form K: Activities]
        VL[Form L: Modifications]
    end

    subgraph "Ideas Forms M-Q"
        IM[Form M: Genre Elements]
        IN[Form N: Structure]
        IO[Form O: Template]
        IP[Form P: Activities]
        IQ[Form Q: Modifications]
    end

    subgraph "Standards Data"
        SP[Pre-K Standards]
        SK[Kindergarten Standards]
        S1[1st Grade Standards]
    end

    subgraph "DynamoDB Storage"
        DB[(DynamoDB Table)]
        IDX1[CategoryIndex]
        IDX2[TypeIndex]
    end

    FA --> HA
    FA --> HB
    FA --> HC
    FA --> HD
    FA --> HE
    FA --> HF
    FA --> HG
    FA --> HH

    FB --> VI
    FB --> VJ
    FB --> VK
    FB --> VL

    FC --> IM
    FC --> IN
    FC --> IO
    FC --> IP
    FC --> IQ

    HA --> DB
    HB --> DB
    HC --> DB
    HD --> DB
    HE --> DB
    HF --> DB
    HG --> DB
    HH --> DB
    VI --> DB
    VJ --> DB
    VK --> DB
    VL --> DB
    IM --> DB
    IN --> DB
    IO --> DB
    IP --> DB
    IQ --> DB
    SP --> DB
    SK --> DB
    S1 --> DB

    DB --> IDX1
    DB --> IDX2

    style DB fill:#fff9c4
    style HA fill:#ffccbc
    style VI fill:#f8bbd0
    style IM fill:#e1bee7
```

---

## Deployment Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        C1[Web Browser]
        C2[Mobile Browser]
    end

    subgraph "CDN/Frontend"
        CDN[Static Assets]
        FE[React Application]
    end

    subgraph "AWS Cloud Infrastructure"
        ALB[Application Load Balancer]

        subgraph "AWS App Runner"
            AR1[FastAPI Instance 1]
            AR2[FastAPI Instance 2]
            AR3[FastAPI Instance N]
        end

        subgraph "Data Services"
            DDB[(DynamoDB)]
            DDB_IDX1[CategoryIndex]
            DDB_IDX2[TypeIndex]
        end

        subgraph "File Storage"
            FS[SQLite Checkpoints]
            FS_DIR[/checkpoints/]
        end
    end

    subgraph "External Services"
        OAI[OpenAI API]
        LS[LangSmith Tracing]
    end

    C1 --> CDN
    C2 --> CDN
    CDN --> FE
    FE --> ALB

    ALB --> AR1
    ALB --> AR2
    ALB --> AR3

    AR1 --> DDB
    AR2 --> DDB
    AR3 --> DDB

    DDB --> DDB_IDX1
    DDB --> DDB_IDX2

    AR1 --> FS
    AR2 --> FS
    AR3 --> FS

    FS --> FS_DIR

    AR1 --> OAI
    AR2 --> OAI
    AR3 --> OAI

    AR1 --> LS
    AR2 --> LS
    AR3 --> LS

    style ALB fill:#e1bee7
    style DDB fill:#fff9c4
    style OAI fill:#ffecb3
    style FS fill:#fff9c4
```

---

## API Endpoints Architecture

```mermaid
graph LR
    subgraph "REST Endpoints"
        E1[GET /health]
        E2[POST /chat2/message]
        E3[GET /chat2/ws/info]
    end

    subgraph "WebSocket Endpoints"
        W1[WS /chat2/ws/message]
    end

    subgraph "Router Handlers"
        H1[health_check]
        H2[send_message]
        H3[websocket_info]
        H4[websocket_message]
    end

    subgraph "Service Layer"
        S1[ChatService]
        S2[process_chat_request]
        S3[handle_websocket_connection]
        S4[handle_message]
    end

    E1 --> H1
    E2 --> H2
    E3 --> H3
    W1 --> H4

    H2 --> S1
    H4 --> S1

    S1 --> S2
    S1 --> S3
    S2 --> S4
    S3 --> S4

    style E2 fill:#c8e6c9
    style W1 fill:#e1bee7
    style S1 fill:#e1f5ff
```

---

## Key Design Principles

### 1. **Router-First Architecture**
- All queries pass through a dedicated routing node
- Intelligent intent classification using GPT-4o
- Complexity detection determines specialist vs. general response
- Transparent handoffs between specialists

### 2. **Conversation Memory**
- Persistent conversation history using SQLite checkpointer
- Thread-based context management
- Cross-bot context sharing (handwriting → vocabulary transitions)
- Automatic message history retrieval via thread_id

### 3. **Domain Specialization**
- **General Bot**: Quick answers, greetings, simple literacy guidance
- **Handwriting Specialist**: Structured 5-part lesson plans (Forms A-H)
- **Vocabulary Specialist**: Sentence structure lessons (Forms I-L)
- **Ideas Specialist**: Creative writing lessons (Forms M-Q)

### 4. **Form-Based Content Retrieval**
- Educational content stored in DynamoDB
- 17 forms (A-Q) containing structured lesson content
- Dynamic retrieval based on intent and query type
- Grade-level standards integration

### 5. **Scalable LangGraph Design**
- StateGraph for flow control
- Asynchronous node execution
- Conditional routing logic
- Checkpointer for state persistence
- Memory-efficient context management

---

## Performance Considerations

### Caching Strategy
- Forms cached in DynamoDB with indexed queries
- Conversation state persisted in SQLite
- Thread-based memory reduces redundant LLM calls

### Optimization Techniques
- Async/await throughout the pipeline
- Thread pool execution for blocking operations
- Selective form retrieval (only relevant categories)
- Context string length limits (2000-4000 chars)
- Parallel tool calls where possible

### Scalability
- Stateless FastAPI instances
- Thread-safe SQLite checkpointer
- AWS App Runner auto-scaling
- DynamoDB indexed queries for fast retrieval

---

## Security & Error Handling

### Security Measures
- Environment variable configuration
- Pydantic schema validation
- Secret management for API keys
- CORS configuration for frontend access

### Error Handling
- Try-catch blocks in all async nodes
- Fallback responses for LLM failures
- Retry logic with exponential backoff
- Graceful degradation for missing forms

---

## Future Architecture Enhancements

1. **Multi-Tenant Support**: Teacher-specific form customization
2. **Real-Time Streaming**: Token-by-token response streaming
3. **Analytics Dashboard**: Usage patterns and bot performance
4. **A/B Testing**: Compare routing strategies
5. **Cache Layer**: Redis for frequently accessed forms
6. **Voice Input**: Speech-to-text integration
7. **PDF Export**: Export lesson plans as formatted PDFs

---

## Configuration Files

### Backend Configuration
- `backend/app/config.py`: Environment variables, API keys
- `backend/langgraph.json`: LangGraph Studio configuration
- `backend/requirements.txt`: Python dependencies
- `backend/.env.local`: Local environment variables

### Frontend Configuration
- `frontend/package.json`: NPM dependencies
- `frontend/vite.config.js`: Build configuration
- `frontend/tailwind.config.js`: Styling configuration
- `frontend/.env`: API base URL configuration

---

## Development & Debugging

### LangGraph Studio Integration
```json
{
  "$schema": "https://langgra.ph/schema.json",
  "dependencies": ["."],
  "graphs": {
    "complete_routing": "app.chatbot.studio.studio_router:studio_router"
  },
  "env": ".env.local"
}
```

### Logging & Monitoring
- Print statements throughout graph execution
- LangSmith tracing integration
- Conversation depth tracking
- Processing time metrics

---

## Repository Structure

```
edtech-chatbot/
├── backend/
│   ├── app/
│   │   ├── chatbot/
│   │   │   ├── routing/
│   │   │   │   ├── router_state.py
│   │   │   │   └── router_nodes.py
│   │   │   ├── specialists/
│   │   │   │   ├── general/
│   │   │   │   │   └── bot.py
│   │   │   │   ├── handwriting/
│   │   │   │   │   ├── nodes.py
│   │   │   │   │   ├── prompts.py
│   │   │   │   │   └── state.py
│   │   │   │   ├── vocabulary/
│   │   │   │   └── ideas/
│   │   │   └── studio/
│   │   │       └── studio_router.py
│   │   ├── routers/
│   │   │   └── chat.py
│   │   ├── services/
│   │   │   ├── chat_service.py
│   │   │   ├── form_retrieval.py
│   │   │   └── intent_classifier.py
│   │   ├── schemas/
│   │   │   ├── chat.py
│   │   │   └── intent.py
│   │   ├── config.py
│   │   ├── database.py
│   │   └── main.py
│   ├── checkpoints/
│   │   └── conversations.db
│   ├── requirements.txt
│   └── langgraph.json
└── frontend/
    ├── src/
    │   ├── api/
    │   │   ├── client.js
    │   │   └── index.js
    │   ├── components/
    │   │   ├── Chatbot.jsx
    │   │   └── MarkdownRenderer.jsx
    │   ├── pages/
    │   │   └── AITeachingAssistant.jsx
    │   ├── App.jsx
    │   └── main.jsx
    └── package.json
```

---

## Conclusion

This architecture provides a robust, scalable, and intelligent AI teaching assistant that leverages **LangGraph's state management** and **LangChain's LLM orchestration** to deliver domain-specific educational content. The router-first design ensures queries are handled by the most appropriate specialist, while the persistent conversation memory enables natural, context-aware interactions across multiple turns.