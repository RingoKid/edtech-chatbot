#!/usr/bin/env python3
import aws_cdk as cdk
from edtech_chatbot_stack import EdTechChatbotInfraStack


app = cdk.App()

# Create the EdTech Chatbot Infrastructure Stack
EdTechChatbotInfraStack(
    app,
    "EdTechChatbotInfraStack",
    # Add stack-level tags
    tags={
        "Project": "EdTechChatbot",
        "Environment": app.node.try_get_context("environment") or "sandbox",
    }
)

app.synth()
