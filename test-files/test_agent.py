import os
from dotenv import load_dotenv
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from bank_agent import agent  # Import the agent from bank_agent.py

# Load environment variables
load_dotenv(override=True)

# Define constants
APP_NAME = "bank_app"
USER_ID = "test_user"
SESSION_ID = "test_session"

# Initialize session service and create a session
session_service = InMemorySessionService()
session_service.create_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID)

# Initialize the runner
runner = Runner(app_name=APP_NAME, agent=agent, session_service=session_service)

# Create a test message
content = types.Content(
    role="user",
    parts=[types.Part(text="Hello, can you assist me with my bank statement?")],
)

# Run the agent and print the response
print("→ Agent thinking…\n")
final = None
for event in runner.run(user_id=USER_ID, session_id=SESSION_ID, new_message=content):
    print("EVENT:", event)
    if event.is_final_response() and event.content and event.content.parts:
        final = event.content.parts[0].text

print("\n←", final or "(no answer)")
