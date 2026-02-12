from pydantic import BaseModel, Field
from typing import Literal, Optional


class User(BaseModel):
    pk: str = Field(alias='PK')
    sk: str = Field(alias='SK')
    type: Literal["User"]
    user_id: str
    name: str
    email: str
    created_at: str


class Conversation(BaseModel):
    """
    User-thread mapping stored in EdTechChatbotTable.
    PK: USER#{user_id}, SK: THREAD#{thread_id}
    """
    pk: str = Field(alias='PK')
    sk: str = Field(alias='SK')
    type: Literal["Conversation"]
    thread_id: str
    user_id: str
    title: str = "New Conversation"
    last_message_preview: Optional[str] = None
    created_at: str
    updated_at: str


class Message(BaseModel):
    pk: str = Field(alias='PK')
    sk: str = Field(alias='SK')
    type: Literal["Message"]
    message_id: str
    conversation_id: str
    sender: Literal["user", "llm"]
    text: str
    created_at: str


class Feedback(BaseModel):
    """
    Feedback record stored in EdTechChatbotTable.
    PK: THREAD#{thread_id}, SK: FEEDBACK#{feedback_id}
    GSI1PK: USER#{user_id}, GSI1SK: FEEDBACK#{created_at}
    """
    pk: str = Field(alias='PK')
    sk: str = Field(alias='SK')
    gsi1pk: str = Field(alias='GSI1PK')
    gsi1sk: str = Field(alias='GSI1SK')
    type: Literal["Feedback"]
    feedback_id: str
    thread_id: str
    user_id: str
    task_type: str
    category: Literal["lesson", "platform", "general"]
    rating: Optional[int] = None
    text: str
    created_at: str