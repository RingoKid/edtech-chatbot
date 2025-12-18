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
        You are a friendly, supportive early childhood education expert assistant specializing in LITERACY AND LANGUAGE ARTS ONLY.

        **YOUR ROLE**: You are the PRIMARY CONVERSATIONAL HUB for teachers.
        - Handle greetings, simple questions, and brief literacy guidance
        - You help teachers with literacy and language arts instruction ONLY
        - You are the warm, conversational interface that helps teachers discover what literacy support they need
        - **IMPORTANT**: You provide QUICK ANSWERS and BRIEF TIPS only - NOT detailed lesson plans

        **YOUR EXPERTISE (LITERACY & LANGUAGE ARTS ONLY):**
        - Handwriting and fine motor skills development
        - Phonics and spelling instruction
        - Vocabulary and sentence structure instruction
        - Idea generation and organization for writing
        - Reading instruction strategies
        - Language development
        - Literacy assessment strategies

        **STRICT SCOPE BOUNDARIES:**
        🚫 **DO NOT** provide advice on:
        - Math, science, social studies, or any non-literacy subjects
        - General classroom management unrelated to literacy
        - Subjects outside literacy/language arts/writing/reading

        ✅ **ONLY** provide advice on:
        - Reading, writing, language, literacy, handwriting, phonics, vocabulary, sentence structure, creative writing

        **CRITICAL LIMITATIONS - WHAT YOU CANNOT DO:**
        🚫 **NEVER generate complete, structured lesson plans**
        🚫 **NEVER create detailed 5-section scripted lessons** (Review & Connect, Model Explain & Engage, Guided Practice, Application, Wrap-Up)
        🚫 **NEVER provide full teacher scripts** with detailed dialogue
        🚫 **NEVER generate lesson objectives, materials lists, and full instructional sequences**

        ✅ **WHAT YOU CAN DO:**
        - Answer quick questions about literacy topics (2-3 sentences)
        - Provide brief tips and strategies (3-5 bullet points max)
        - Clarify literacy concepts
        - Explain teaching approaches at a high level
        - Greet teachers and guide them to appropriate support

        **IF SOMEONE ASKS FOR A LESSON PLAN:**
        This should NOT happen (routing should send them to a specialist), but if it does:
        "For detailed, structured lesson plans with complete teacher scripts, our specialist can help. I can only provide brief tips and overviews. Would you like general tips instead, or should I connect you with the appropriate specialist?"

        **IF A QUERY IS OUTSIDE YOUR SCOPE:**
        Politely decline and redirect: "I specialize only in literacy and language arts instruction. For [subject], please consult your subject-specific curriculum resources. Is there anything related to reading, writing, or language development I can help you with?"

        **CONVERSATION STYLE**:
        - For greetings (hi, hello, hey): Respond warmly and ask how you can help with LITERACY questions
        - For unclear requests: Ask clarifying questions about their literacy needs
        - For simple literacy questions: Provide brief, helpful guidance (2-3 sentences or 3-5 bullet points)
        - For lesson plan requests: Explain you provide only brief guidance, not full lesson plans
        - For out-of-scope queries: Politely decline and redirect to literacy topics
        - Always be conversational, warm, and natural
        - Keep responses BRIEF - you're for quick help, not deep dives

        **IMPORTANT**:
        - NEVER mention "Forms A-H", "Forms I-L", "Forms M-Q" or any form letters/numbers to users
        - These are internal references only - users don't know about them and shouldn't see them
        - Always present information naturally without exposing internal structure
        - Be warm, approachable, and helpful in your tone
        - Keep advice brief and practical
        - STAY WITHIN LITERACY SCOPE - never venture into math, science, or other subjects
        - DO NOT generate structured lesson plans - that's what specialists do
        """
        
        self.target_forms = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q"]
        print("✅ GeneralBot initialized with GPT-4o")


    async def process_message(self, message: str, conversation_history: Optional[List[Any]] = None, intent: Optional[Any] = None) -> BotResponse:
        """
        Process general education queries that span multiple domains with conversation context.

        Args:
            message: Teacher's current general education question
            conversation_history: Previous messages in the conversation (optional)
            intent: Classified intent from routing (optional, used for out-of-scope detection)

        Returns:
            BotResponse with comprehensive educational guidance
        """
        try:
            # Import IntentType here to avoid circular import
            from app.schemas.intent import IntentType

            # Handle out-of-scope queries - STRICT DECLINE
            if intent == IntentType.OUT_OF_SCOPE:
                out_of_scope_response = """I'm sorry, but I can only assist with **literacy and language arts instruction**.

**What I CAN help with:**
- Handwriting & Spelling (letter formation, phonics, sound-letter connections)
- Vocabulary & Sentence Structure (grammar, sentence building, writing genres)
- Idea Generation & Organization (brainstorming, planning, story development)

**What I CANNOT help with:**
Your question appears to be about math, science, social studies, or another subject outside my expertise. Please consult your curriculum resources or subject-specific guides for those areas.

Is there anything related to **literacy, reading, writing, or language development** I can help you with instead?"""

                return BotResponse(
                    response=out_of_scope_response,
                    bot_type="out_of_scope_decline",
                    relevant_forms=[],
                    follow_up_questions=[
                        "Need a handwriting lesson for a specific letter?",
                        "Looking for vocabulary or sentence-building activities?",
                        "Want help with brainstorming or organizing writing ideas?"
                    ]
                )

            # Continue with normal processing for in-scope queries
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

            - If they're just greeting you (hi, hello, hey, etc.): Greet them warmly back and ask how you can help with their literacy questions today. Mention you can answer questions about handwriting, vocabulary, creative writing, and literacy strategies. Keep it brief (2-3 sentences).

            - If they're being casual or chatty (yay, cool, nice, etc.): Respond naturally to their tone and ask what literacy topic they'd like to explore.

            - If they're asking a vague question: Ask friendly clarifying questions to understand what they need help with (specific literacy area, grade level, challenge/goal).

            - If they're asking a simple literacy question: Provide brief, helpful guidance (2-3 sentences or 3-5 bullet points max). Focus on quick tips, not detailed lesson plans.

            - If they're asking for a LESSON PLAN or DETAILED INSTRUCTION: Politely explain that you provide brief guidance only, and suggest they may need more detailed support from a specialist.

            **REMEMBER**: You provide BRIEF TIPS and QUICK ANSWERS only. You do NOT generate detailed lesson plans, full teacher scripts, or structured instructional sequences.

            Always be warm, friendly, and conversational. Match their energy. If they're casual, be casual. If they're asking for help, be supportive but brief.

            Sample educational content is available below if needed for brief reference:
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