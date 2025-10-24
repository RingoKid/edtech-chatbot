"""
Specialized Educational Bots for Vocabulary and Ideas domains.
These bots work alongside the existing handwriting bot to provide domain-specific expertise.
"""
from typing import List, Optional, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from app.config import settings
from app.services.form_retrieval import form_retrieval_service
from app.schemas.intent import BotResponse

class VocabularyBot:
    """Specialized bot for vocabulary and reading skills (Forms I-L)."""
    
    def __init__(self):
        """Initialize the vocabulary bot."""
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key not configured for vocabulary bot")
        
        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.7,
            api_key=settings.openai_api_key.get_secret_value()
        )
        
        self.system_prompt = """
        You are an expert in vocabulary and sentence structure instruction for early childhood education.

        **YOUR EXPERTISE: Vocabulary & Sentence Structure Instruction**

        You generate COMPLETE, SCRIPTED LESSON PLANS in this exact structure:

        **LESSON PLAN STRUCTURE:**

        **A. Standards**
        - Reference appropriate Pre-K/Kindergarten language/writing standards
        - Example: "ELAGSEKL1f: Produce and expand complete sentences in shared language activities"

        **B. Objectives**
        - Derive specific, measurable objectives from lesson content
        - Example: "Students will use action verbs to build complete sentences about animals for informational writing"
        - Example: "Students will use sentence frames with subject-verb agreement"

        **C. Materials**
        - List everything needed with bullet points
        - Example: "Vocabulary cards, sentence frames, writing paper, word wall, picture cards"

        **D. Scripted Lesson Plan for Vocabulary & Sentence Structure**

        **1. Review & Connect**

        [The purpose of this part of the lesson is to review previously learned vocabulary or sentence patterns and connect to the current writing unit/genre.]

        Teacher Script:

        Provide exact dialogue the teacher will say, without hashtags or special symbols
        {{Teacher actions in curly braces}}
        (Expected child responses in parentheses)

        **2. Model, Explain & Engage**

        [The purpose of this part of the lesson is to introduce new vocabulary words and model how to use them in sentences aligned with the writing genre.]

        Teacher Script:

        Include vocabulary word introduction with definitions and visual support
        Include sentence structure modeling (subject-verb patterns, be-verbs, action verbs)
        Include genre-specific sentence examples (narrative, informational, opinion)
        Include think-aloud demonstrating vocabulary in sentences

        **3. Guided Practice**

        [The purpose is to give children practice building sentences using target vocabulary with teacher support.]

        Teacher Script:

        Include sentence building activities (Sentence Scramble, Fill-in-the-Blank, etc.)
        Include vocabulary practice in context
        Include collaborative sentence creation

        **4. Application**

        [The purpose of this part of the lesson is to facilitate children's independent use of vocabulary in genre-specific sentence writing.]

        Teacher Script:

        Include independent sentence writing using target vocabulary
        Include genre-specific writing application
        Include partner sharing and feedback

        **5. Wrap-Up**

        [The purpose of this part of the lesson is to review target vocabulary and sentence patterns and celebrate student work.]

        Teacher Script:

        Review target vocabulary and sentence patterns
        Share student examples
        Connect to ongoing writing unit

        **KEY PRINCIPLES:**
        - Connect vocabulary to specific writing genres (narrative, informational, opinion)
        - Teach sentence structures: subject-verb patterns, be-verbs, action verbs
        - Use unit themes and topics for vocabulary selection
        - Model sentence building explicitly before practice
        - Provide sentence frames for differentiation
        - Link to ongoing writing projects and genres

        **CRITICAL OUTPUT REQUIREMENTS:**
        ✅ Be a complete, rehearsal-ready lesson plan
        ✅ Include ALL 5 subsections with detailed scripts
        ✅ MUST include the bracketed [Explanation] at the start of EVERY section (1-5)
        ✅ MUST include full "Teacher Script:" with complete dialogue for every section
        ✅ Use clean formatting: [explanations], plain Teacher Script sections, (responses), {{actions}}
        ✅ DO NOT use hashtags (#), plus signs (+Level), asterisks (*Adaptation), or double hashtags (##) in user-facing output
        ✅ Include specific sentence-building activities
        ✅ Connect to specific writing genre (narrative, informational, opinion)
        ✅ Be 20-25 minutes total lesson time
        ✅ NEVER mention "Forms I-L", "Form K", "Form J" or any form letters/numbers to users
        ✅ Present all content as if you are the expert, not referencing external forms

        **MANDATORY STRUCTURE FOR EACH SECTION:**
        Each of the 5 sections MUST have:
        1. Section heading (e.g., "**1. Review & Connect**")
        2. Bracketed explanation (e.g., "[The purpose of this part of the lesson is to...]")
        3. "Teacher Script:" heading
        4. Complete, detailed dialogue with {{actions}} and (expected responses)
        """
        
        self.target_forms = ["I", "J", "K", "L"]
        print("✅ VocabularyBot initialized with GPT-4o")
    
    async def process_message(self, message: str, conversation_history: Optional[List[Any]] = None) -> BotResponse:
        """
        Process vocabulary and reading-related queries with form content and conversation context.

        Args:
            message: Teacher's current question about vocabulary/reading
            conversation_history: Previous messages in the conversation (optional)

        Returns:
            BotResponse with comprehensive vocabulary guidance
        """
        try:
            # Retrieve relevant vocabulary forms from database
            forms = await form_retrieval_service.get_vocabulary_forms()
            form_context = form_retrieval_service.build_context_string(forms, max_length=3500)

            # Build conversation context string if history exists
            context_summary = ""
            if conversation_history and len(conversation_history) > 1:
                # Extract previous exchanges (exclude current message)
                previous_exchanges = []
                for msg in conversation_history[:-1]:  # All except the latest
                    if hasattr(msg, 'content'):
                        role = "Teacher" if hasattr(msg, 'type') and msg.type == 'human' else "Assistant"
                        previous_exchanges.append(f"{role}: {msg.content}")

                if previous_exchanges:
                    # Include last 3 exchanges for context (6 messages)
                    recent_context = previous_exchanges[-6:]
                    context_summary = f"""
                CONVERSATION HISTORY (recent exchanges):
                {chr(10).join(recent_context)}

                ---
                """

            # Build enhanced prompt with form content and conversation context
            if forms:
                prompt = f"""
                {context_summary}CURRENT TEACHER REQUEST: "{message}"

                RELEVANT EDUCATIONAL FORMS CONTENT (Forms I-L):
                {form_context}

                **IMPORTANT**: Use the conversation history above to understand the full context of the teacher's request. If they're following up on a previous question, continue that discussion naturally.

                **DETERMINE YOUR RESPONSE TYPE:**

                IF the teacher asks for:
                - "Create a lesson plan"
                - "Generate a lesson"
                - "Help me teach [specific vocabulary/sentences]"
                - "I need a vocabulary lesson for..."

                → THEN generate a **COMPLETE SCRIPTED LESSON PLAN** using the structure in your system prompt.

                IF the teacher asks for:
                - "How do I..." questions
                - "What are some strategies for..." questions
                - "Can you explain..." questions
                - General guidance or tips

                → THEN provide **TARGETED GUIDANCE** with:
                1. **Direct Answer** to their question
                2. **2-3 Specific Activities** from Form K with materials and steps
                3. **Differentiation** for beginning/developing/fluent writers
                4. **Genre Connection** (narrative, informational, opinion writing)
                5. **References** to relevant Forms (I-L)

                Always use the exact content from the provided forms. Reference Form I for structure, Form J for templates, Form K for activities, and Form L for modifications.

                Make your response immediately actionable and classroom-ready.
                """
            else:
                # Fallback if no forms are available
                prompt = f"""
                {context_summary}A teacher is asking about vocabulary or reading instruction. Use your expertise to provide helpful guidance.

                Current teacher's question: "{message}"

                Provide a comprehensive response that includes:
                1. **Direct Answer**: Address the teacher's specific question
                2. **Specific Teaching Strategies**: Evidence-based vocabulary/reading activities
                3. **Materials and Resources**: What teachers need to implement strategies
                4. **Differentiation**: Approaches for various skill levels
                5. **Assessment Ideas**: Ways to track student progress

                Focus on practical, research-based approaches that build literacy skills.
                """

            response = await self.llm.ainvoke([
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=prompt)
            ])
            
            # Extract form IDs that were used
            used_form_ids = [f"Form {form['form_letter']}" for form in forms] if forms else []
            
            # Generate activity suggestions
            suggested_activities = [
                "Phonics games and word building activities",
                "Sight word practice with multi-sensory approaches",
                "Vocabulary development through read-alouds",
                "Word study and morphology activities"
            ]
            
            return BotResponse(
                response=response.content,
                bot_type="vocabulary_specialist",
                relevant_forms=used_form_ids,
                follow_up_questions=suggested_activities
            )
            
        except Exception as e:
            print(f"Error in VocabularyBot: {str(e)}")
            return BotResponse(
                response=f"I apologize, but I'm having trouble processing your vocabulary question right now. Please try rephrasing your question or contact support if the issue persists.",
                bot_type="vocabulary_specialist_error",
                relevant_forms=[],
                follow_up_questions=[]
            )

class IdeasBot:
    """Specialized bot for creative writing and idea generation (Forms M-Q)."""
    
    def __init__(self):
        """Initialize the ideas bot."""
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key not configured for ideas bot")
        
        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.8,  # Higher temperature for creativity
            api_key=settings.openai_api_key.get_secret_value()
        )
        
        self.system_prompt = """
        You are an expert in idea generation and organization instruction for early childhood education.

        **YOUR EXPERTISE: Forms M-Q Idea Generation & Organization Instruction**

        You generate COMPLETE, SCRIPTED LESSON PLANS in this exact structure:

        **LESSON PLAN STRUCTURE:**

        1. **Standards**: Reference Pre-K/Kindergarten writing standards from the provided forms

        2. **Objectives**: Derive from lesson content (e.g., "Students will generate and organize ideas for [genre] writing about [topic] using [graphic organizer]")

        3. **Materials**: List everything needed (e.g., graphic organizers, mentor texts, writing paper, brainstorming charts)

        4. **Scripted Lesson Plan** with 5 subsections:

        **A. Review & Connect** (2-3 minutes)
        - [Explanation in brackets]: Purpose and connection to writing unit/genre
        - #Teacher Script: Exact dialogue introducing topic and genre
        - (Expected child responses)
        - {{Teacher actions in curly braces}}
        - *Adaptation: Prompt at end

        **B. Model, Explain & Engage** (5-7 minutes)
        - Genre introduction (narrative, informational, opinion, personal narrative)
        - Mentor text analysis for idea generation
        - Think-aloud demonstrating brainstorming process
        - Graphic organizer introduction from Form P
        - Topic and purpose explanation
        - *Adaptation: Prompt at end

        **C. Guided Practice** (5-7 minutes)
        - Collaborative brainstorming using activities from Form P
        - Graphic organizer completion as a group
        - Idea organization strategies
        - Text-to-writing connections
        - *Adaptation: Prompt at end

        **D. Application** (5-7 minutes)
        - Independent idea generation
        - Personal graphic organizer completion
        - Partner sharing of ideas
        - Beginning draft/drawing based on organized ideas
        - *Adaptation: Prompt at end

        **E. Wrap-Up** (2-3 minutes)
        - Review genre elements and topic
        - Share student examples
        - Connect to next writing steps
        - Celebrate idea generation

        **KEY PRINCIPLES (Forms M-Q):**
        - Focus on specific writing genres: narrative, informational, opinion, personal narrative
        - Use graphic organizers to organize ideas (story maps, webs, lists, T-charts)
        - Connect to unit topics and themes
        - Use mentor texts to inspire ideas
        - Teach genre-specific elements (characters/setting for narrative, facts for informational, etc.)
        - Support drawing, dictation, and writing based on developmental level
        - Celebrate all forms of idea expression

        **YOUR OUTPUT MUST:**
        ✅ Be a complete, rehearsal-ready lesson plan
        ✅ Include ALL 5 subsections with detailed scripts
        ✅ Use exact formatting: [explanations], #scripts#, (responses), {{actions}}, *adaptations
        ✅ Include specific brainstorming and organizing activities
        ✅ Connect to specific writing genre (narrative, informational, opinion, personal narrative)
        ✅ Be 20-25 minutes total lesson time
        ✅ Include differentiation for drawing/dictating, emerging writers, developing writers

        **CRITICAL - USER-FACING COMMUNICATION:**
        ✅ NEVER mention "Forms M-Q", "Form P", "Form N" or any form letters/numbers to users
        ✅ These are internal references - users don't know about them and shouldn't see them
        ✅ Present information naturally without exposing internal structure
        """
        
        self.target_forms = ["M", "N", "O", "P", "Q"]
        print("✅ IdeasBot initialized with GPT-4o")
    
    async def process_message(self, message: str, conversation_history: Optional[List[Any]] = None) -> BotResponse:
        """
        Process creative writing and idea generation queries with form content and conversation context.

        Args:
            message: Teacher's current question about creative writing/ideas
            conversation_history: Previous messages in the conversation (optional)

        Returns:
            BotResponse with inspiring creative writing guidance
        """
        try:
            # Retrieve relevant ideas forms from database
            forms = await form_retrieval_service.get_ideas_forms()
            form_context = form_retrieval_service.build_context_string(forms, max_length=3500)

            # Build conversation context string if history exists
            context_summary = ""
            if conversation_history and len(conversation_history) > 1:
                # Extract previous exchanges (exclude current message)
                previous_exchanges = []
                for msg in conversation_history[:-1]:  # All except the latest
                    if hasattr(msg, 'content'):
                        role = "Teacher" if hasattr(msg, 'type') and msg.type == 'human' else "Assistant"
                        previous_exchanges.append(f"{role}: {msg.content}")

                if previous_exchanges:
                    # Include last 3 exchanges for context (6 messages)
                    recent_context = previous_exchanges[-6:]
                    context_summary = f"""
                CONVERSATION HISTORY (recent exchanges):
                {chr(10).join(recent_context)}

                ---
                """

            # Build enhanced prompt with form content and conversation context
            if forms:
                prompt = f"""
                {context_summary}CURRENT TEACHER REQUEST: "{message}"

                RELEVANT EDUCATIONAL FORMS CONTENT (Forms M-Q):
                {form_context}

                **IMPORTANT**: Use the conversation history above to understand the full context of the teacher's request. If they're following up on a previous question, continue that discussion naturally.

                **DETERMINE YOUR RESPONSE TYPE:**

                IF the teacher asks for:
                - "Create a lesson plan"
                - "Generate a lesson"
                - "Help me teach [specific genre/topic]"
                - "I need an idea generation lesson for..."

                → THEN generate a **COMPLETE SCRIPTED LESSON PLAN** using the structure in your system prompt.

                IF the teacher asks for:
                - "How do I..." questions
                - "What are some strategies for..." questions
                - "Can you explain..." questions
                - General guidance or tips

                → THEN provide **TARGETED GUIDANCE** with:
                1. **Direct Answer** to their question
                2. **2-3 Specific Activities** from Form P with materials and steps
                3. **Differentiation** for drawing/dictating, emerging writers, developing writers
                4. **Genre Connection** (narrative, informational, opinion, personal narrative)
                5. **References** to relevant Forms (M-Q)

                Always use the exact content from the provided forms. Reference Form M for genre elements, Form N for structure, Form O for templates, Form P for activities, and Form Q for modifications.

                Make your response immediately actionable and classroom-ready. Inspire creativity while providing clear structure.
                """
            else:
                # Fallback if no forms are available
                prompt = f"""
                {context_summary}A teacher is asking about creative writing or idea generation. Use your expertise to provide inspiring guidance.

                Current teacher's question: "{message}"

                Provide a comprehensive response that includes:
                1. **Direct Answer**: Address the teacher's specific question
                2. **Creative Activities**: Engaging writing prompts and activities
                3. **Materials and Setup**: What teachers need to create inspiring writing environments
                4. **Differentiation**: Approaches for various writing levels
                5. **Inspiration Strategies**: How to motivate young writers

                Make your suggestions engaging and inspiring for both teachers and students.
                """

            response = await self.llm.ainvoke([
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=prompt)
            ])
            
            # Extract form IDs that were used
            used_form_ids = [f"Form {form['form_letter']}" for form in forms] if forms else []
            
            # Generate creative activity suggestions
            suggested_activities = [
                "Story starter activities with visual prompts",
                "Character development exercises",
                "Creative writing journals and free writing",
                "Collaborative storytelling and idea sharing"
            ]
            
            return BotResponse(
                response=response.content,
                bot_type="ideas_specialist",
                relevant_forms=used_form_ids,
                follow_up_questions=suggested_activities
            )
            
        except Exception as e:
            print(f"Error in IdeasBot: {str(e)}")
            return BotResponse(
                response=f"I apologize, but I'm having trouble processing your creative writing question right now. Please try rephrasing your question or contact support if the issue persists.",
                bot_type="ideas_specialist_error",
                relevant_forms=[],
                follow_up_questions=[]
            )

class GeneralBot:
    """
    General education bot - Primary conversational hub that handles simple queries
    and routes complex requests to specialist bots when needed.
    """

    def __init__(self):
        """Initialize the general bot."""
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key not configured for general bot")

        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.7,
            api_key=settings.openai_api_key.get_secret_value()
        )

        self.system_prompt = """
        You are a friendly, supportive early childhood education expert assistant.

        **YOUR ROLE**: You are the PRIMARY CONVERSATIONAL HUB for teachers.
        - Handle greetings, simple questions, and general guidance
        - When teachers need DEEP, STRUCTURED lesson plans, you prepare them for handoff to specialist bots
        - You are the warm, conversational interface that helps teachers discover what they need

        Your expertise covers:
        - Handwriting and fine motor skills development
        - Vocabulary and sentence structure instruction
        - Idea generation and organization for writing
        - General classroom management strategies
        - Cross-curricular instruction approaches
        - Child development principles
        - Differentiated instruction techniques
        - Assessment strategies across domains
        - Parent communication and engagement

        When questions span multiple domains (handwriting, vocabulary, creative writing),
        provide balanced guidance across all relevant areas.

        **CONVERSATION STYLE**:
        - For greetings (hi, hello, hey) or vague messages: Respond warmly and ask how you can help with their teaching needs
        - For unclear requests: Ask clarifying questions to understand what they need
        - For specific educational questions: Provide detailed, structured guidance
        - Always be conversational, warm, and natural - avoid overly templated responses
        - Engage in a dialogue, not a monologue

        **IMPORTANT**:
        - NEVER mention "Forms A-H", "Forms I-L", "Forms M-Q" or any form letters/numbers to users
        - These are internal references only - users don't know about them and shouldn't see them
        - Always present information naturally without exposing internal structure
        - Be warm, approachable, and helpful in your tone
        - Always provide practical, actionable advice for classroom teachers
        """
        
        self.target_forms = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q"]
        print("✅ GeneralBot initialized with GPT-4o")

    async def detect_query_complexity(self, message: str, conversation_history: Optional[List[Any]] = None) -> str:
        """
        HYBRID APPROACH: Uses rule-based detection for obvious cases,
        LLM for ambiguous cases. Optimizes for speed, cost, and accuracy.

        Returns:
            "simple" - General bot can answer with quick guidance
            "complex" - Needs specialist for structured lesson plan generation
        """
        import re

        query_lower = message.lower()

        # ============================================================
        # FAST PATH 1: Obvious COMPLEX patterns (no LLM needed)
        # ============================================================
        obvious_complex = [
            "create lesson",
            "create a lesson",
            "generate lesson",
            "lesson plan",
            "scripted lesson",
            "step by step lesson",
            "full lesson",
            "complete lesson",
            "detailed lesson",
            "i need a lesson",
            "give me a lesson",
            "write a lesson",
            "build a lesson"
        ]

        if any(pattern in query_lower for pattern in obvious_complex):
            print(f"🎯 Rule-based: COMPLEX (lesson plan request detected)")
            return "complex"

        # ============================================================
        # FAST PATH 2: Obvious SIMPLE patterns (no LLM needed)
        # ============================================================
        obvious_simple = [
            "hi", "hello", "hey", "hey there",
            "good morning", "good afternoon", "good evening",
            "what is", "what are", "what's",
            "define", "briefly", "quickly",
            "in a few words", "simple answer"
        ]

        # Short greetings or definitional questions
        word_count = len(message.split())
        if any(pattern in query_lower for pattern in obvious_simple) and word_count < 12:
            print(f"🎯 Rule-based: SIMPLE (greeting or short question)")
            return "simple"

        # Single word queries
        if word_count <= 2:
            print(f"🎯 Rule-based: SIMPLE (very short query)")
            return "simple"

        # ============================================================
        # FAST PATH 3: Specific letter + teaching request = COMPLEX
        # ============================================================
        has_specific_letter = bool(re.search(r'\bletter\s+[A-Za-z]\b', query_lower))
        teaching_indicators = [
            "help me teach",
            "how do i teach",
            "how to teach",
            "teach letter",
            "teaching letter",
            "activities for letter",
            "step by step for",
            "stroke sequence for",
            "formation cues for"
        ]

        if has_specific_letter and any(ind in query_lower for ind in teaching_indicators):
            print(f"🎯 Rule-based: COMPLEX (specific letter + teaching request)")
            return "complex"

        # ============================================================
        # FAST PATH 4: Extended conversation = COMPLEX
        # ============================================================
        if conversation_history and len(conversation_history) >= 7:
            # 7+ messages = 3-4 exchanges, likely needs specialist
            print(f"🎯 Rule-based: COMPLEX (extended conversation depth)")
            return "complex"

        # ============================================================
        # AMBIGUOUS CASE: Use LLM for nuanced decision
        # ============================================================
        print(f"🤔 Ambiguous query, using LLM for intelligent classification...")

        # Build conversation context for LLM
        context_summary = ""
        if conversation_history and len(conversation_history) > 1:
            recent_msgs = conversation_history[-4:]  # Last 2 exchanges
            context_parts = []
            for msg in recent_msgs:
                if hasattr(msg, 'content'):
                    content = msg.content
                    if isinstance(content, str):
                        role = "Teacher" if (hasattr(msg, 'type') and msg.type == 'human') else "Assistant"
                        context_parts.append(f"{role}: {content[:120]}")

            if context_parts:
                context_summary = f"\n**Recent Conversation:**\n" + "\n".join(context_parts)

        # LLM classification prompt
        classification_prompt = f"""You are a routing classifier for an educational chatbot system.

Your job: Classify this teacher query as "simple" or "complex".

**Current Query**: "{message}"
{context_summary}

**Classification Guidelines**:

**SIMPLE** queries (general bot handles):
- Greetings: "hi", "hello", "can you help?"
- Quick questions: "what is handwriting?", "why teach phonics?"
- General tips: "tips for teaching", "strategies for..."
- Clarifications: "what do you mean?", "can you explain?"
- Short follow-ups: "okay", "yes", "that helps"

**COMPLEX** queries (needs specialist for structured lesson):
- Lesson plan requests: "create a lesson", "I need a lesson plan"
- Detailed teaching guides: "how do I teach letter M step by step?"
- Structured activities: "give me activities for teaching..."
- Full instructional sequences: "walk me through teaching..."
- Multi-part requests: requests combining multiple elements

**Context Clues**:
- If conversation history shows they're exploring a topic → might need specialist
- If query asks for "quick" or "brief" → likely simple
- If query mentions specific letters/topics with "teach" or "lesson" → likely complex

Respond with ONLY ONE WORD: "simple" or "complex"

Classification:"""

        try:
            response = await self.llm.ainvoke([HumanMessage(content=classification_prompt)])
            classification = response.content.strip().lower()

            # Validate LLM response
            if classification not in ["simple", "complex"]:
                print(f"⚠️ Invalid LLM response: '{classification}', defaulting to 'simple'")
                return "simple"

            print(f"🤖 LLM classified as: {classification.upper()}")
            return classification

        except Exception as e:
            print(f"❌ LLM classification error: {str(e)}, defaulting to 'simple'")
            return "simple"

    def classify_topic(self, message: str, conversation_history: Optional[List[Any]] = None) -> Optional[str]:
        """
        Determines which specialist bot domain this query belongs to.
        Uses both current message and conversation history for context.

        Returns:
            "handwriting" | "vocabulary" | "ideas" | None
        """
        query_lower = message.lower()

        # Check conversation history for context
        history_text = ""
        if conversation_history and len(conversation_history) > 1:
            # Get last few messages for context
            recent = conversation_history[-6:]  # Last 3 exchanges
            history_parts = []
            for msg in recent:
                if hasattr(msg, 'content'):
                    content = msg.content
                    if isinstance(content, str):
                        history_parts.append(content.lower())
            history_text = " ".join(history_parts)

        # Combine current query + history for classification
        combined_text = f"{query_lower} {history_text}"

        # Handwriting indicators
        handwriting_keywords = [
            "letter", "handwriting", "write", "writing the letter",
            "pencil", "grip", "formation", "stroke", "uppercase", "lowercase",
            "/m/", "/z/", "/a/",  # phoneme notation
            "proper grip", "letter formation"
        ]

        if any(keyword in combined_text for keyword in handwriting_keywords):
            return "handwriting"

        # Vocabulary/sentence indicators
        vocabulary_keywords = [
            "vocabulary", "sentence", "word", "reading", "phonics",
            "sight word", "be-verb", "action verb", "compound sentence",
            "sentence structure", "sentence frame"
        ]

        if any(keyword in combined_text for keyword in vocabulary_keywords):
            return "vocabulary"

        # Ideas/creative writing indicators
        ideas_keywords = [
            "story", "creative", "ideas", "brainstorm", "narrative",
            "writing ideas", "topic", "genre", "informational writing",
            "opinion writing", "graphic organizer", "story map"
        ]

        if any(keyword in combined_text for keyword in ideas_keywords):
            return "ideas"

        return None

    async def process_message(self, message: str, conversation_history: Optional[List[Any]] = None) -> BotResponse:
        """
        Process general education queries that span multiple domains with conversation context.

        Args:
            message: Teacher's current general education question
            conversation_history: Previous messages in the conversation (optional)

        Returns:
            BotResponse with comprehensive educational guidance
        """
        try:
            # Get a representative sample of forms from all domains
            handwriting_forms = await form_retrieval_service.get_handwriting_forms(["A", "B"])
            vocabulary_forms = await form_retrieval_service.get_vocabulary_forms(["I", "J"])
            ideas_forms = await form_retrieval_service.get_ideas_forms(["M", "N"])

            all_forms = handwriting_forms + vocabulary_forms + ideas_forms
            form_context = form_retrieval_service.build_context_string(all_forms, max_length=2000)

            # Build conversation context string if history exists
            context_summary = ""
            if conversation_history and len(conversation_history) > 1:
                # Extract previous exchanges (exclude current message)
                previous_exchanges = []
                for msg in conversation_history[:-1]:  # All except the latest
                    if hasattr(msg, 'content'):
                        role = "Teacher" if hasattr(msg, 'type') and msg.type == 'human' else "Assistant"
                        previous_exchanges.append(f"{role}: {msg.content}")

                if previous_exchanges:
                    # Include last 3 exchanges for context (6 messages)
                    recent_context = previous_exchanges[-6:]
                    context_summary = f"""
            CONVERSATION HISTORY (recent exchanges):
            {chr(10).join(recent_context)}

            ---
            """

            # Simple, natural prompt for all messages - let the LLM decide how to respond
            prompt = f"""
            {context_summary}Current teacher's message: "{message}"

            Respond naturally and conversationally based on what the teacher needs:

            - If they're just greeting you (hi, hello, hey, etc.): Greet them warmly back and ask how you can help with their teaching today. Mention you can help with handwriting, vocabulary, creative writing, lesson planning, and classroom strategies. Keep it brief (2-3 sentences).

            - If they're being casual or chatty (yay, cool, nice, etc.): Respond naturally to their tone and ask what they'd like to work on.

            - If they're asking a vague question: Ask friendly clarifying questions to understand what they need help with (specific area, grade level, challenge/goal).

            - If they're asking a specific educational question: Provide helpful, actionable guidance that includes practical strategies, differentiation tips, and assessment ideas when relevant.

            Always be warm, friendly, and conversational. Match their energy. If they're casual, be casual. If they're asking for serious help, be thorough and professional.

            Sample educational content is available below if needed for specific questions:
            {form_context}
            """

            response = await self.llm.ainvoke([
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=prompt)
            ])
            
            # Include forms from all domains
            used_form_ids = [f"Form {form['form_letter']}" for form in all_forms]
            
            # Generate general activity suggestions
            suggested_activities = [
                "Integrated literacy activities combining domains",
                "Cross-curricular projects and themes",
                "Assessment strategies across learning areas",
                "Differentiated instruction approaches"
            ]
            
            return BotResponse(
                response=response.content,
                bot_type="general_education_specialist",
                relevant_forms=used_form_ids,
                follow_up_questions=suggested_activities
            )

        except Exception as e:
            print(f"Error in GeneralBot: {str(e)}")
            return BotResponse(
                response=f"I apologize, but I'm having trouble processing your question right now. Please try rephrasing your question or contact support if the issue persists.",
                bot_type="general_education_specialist_error",
                relevant_forms=[],
                follow_up_questions=[]
            )