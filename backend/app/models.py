from pydantic import BaseModel, Field
from typing import Literal


class User(BaseModel):
    pk: str = Field(alias='PK')
    sk: str = Field(alias='SK')
    type: Literal["User"]
    user_id: str
    name: str
    email: str
    created_at: str


class Conversation(BaseModel):
    pk: str = Field(alias='PK')
    sk: str = Field(alias='SK')
    type: Literal["Conversation"]
    conversation_id: str
    user_id: str
    title: str
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