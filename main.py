import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path
from datetime import datetime # Import datetime

from dotenv import load_dotenv
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from bank_agent import agent

# ── 1) Load .env and configure logging ───────────────────────────────
load_dotenv(override=True)

# --- Manual Logging Configuration ---
log_formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger() # Get the root logger
logger.setLevel(logging.DEBUG) # Set root logger level to DEBUG

# *** Create logs directory if it doesn't exist ***
log_dir = Path("logs")
log_dir.mkdir(parents=True, exist_ok=True) # Ensure the directory exists

# File Handler (Timestamped, inside 'logs' directory)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
# *** Use path joining to place the file in the log_dir ***
log_file_path = log_dir / f"agent_{timestamp}.log"
file_handler = logging.FileHandler(log_file_path, mode="a", encoding="utf-8")
file_handler.setLevel(logging.DEBUG) # Log everything to the file
file_handler.setFormatter(log_formatter)
logger.addHandler(file_handler)

# Log the path where the log file is being saved (useful for confirmation)
logger.info(f"Logging initialized. Log file: {log_file_path.absolute()}")


# ── 2) Initialize ADK Runner ────────────────────────────────────────
# (Runner setup remains the same)
APP_NAME = "bank_app"
USER_ID = "local_user"
SESSION_ID = "default_session"

session_service = InMemorySessionService()
session_service.create_session(
    app_name=APP_NAME,
    user_id=USER_ID,
    session_id=SESSION_ID,
)
runner = Runner(app_name=APP_NAME, agent=agent, session_service=session_service)

# ── 3) Asynchronous interaction (per ADK tutorial) ──────────────────

async def call_agent_async(pdf_path: Path, question: str) -> None:
    # Log inputs to the file
    logger.info(f"--- New Execution ---")
    logger.info(f"User Question: {question}")
    logger.info(f"PDF Path: {pdf_path}")

    content = types.Content(
        role="user",
        parts=[
            types.Part(text=question),
            types.Part(text=f"File path to analyze: {pdf_path.absolute()}"),
        ],
    )

    final = "(no response)"
    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=SESSION_ID,
        new_message=content,
    ):
        logger.debug(f"EVENT: {event}") # Keep detailed event logs in the file
        for resp in event.get_function_responses():
            logger.info(f"Tool output: {resp.response}") # Log tool output to file
        if event.is_final_response():
            final = event.content.parts[0].text if event.content and event.content.parts else final
            break

    # Use standard print ONLY for the final agent response to console
    print(f"<<< Agent: {final}")
    # Also log the final answer to the file for completeness
    logger.info(f"Agent final response: {final}")

# ── 4) CLI entrypoint ────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser(description="Bank statement ADK CLI")
    ap.add_argument("pdf", type=Path, help="PDF path")
    ap.add_argument("question", nargs="+", help="Query text")
    args = ap.parse_args()

    pdf_path = args.pdf.resolve()
    if not pdf_path.is_file():
        # Log the error to the file
        logger.error(f"Error: PDF file not found at {pdf_path}")
        # Print error to console (stderr) and exit
        print(f"Error: PDF file not found at {pdf_path}", file=sys.stderr)
        sys.exit(1)

    question = " ".join(args.question)

    # Optionally print user question to console for context
    print(f">>> User: {question}")

    asyncio.run(call_agent_async(pdf_path, question))

if __name__ == "__main__":
    main()