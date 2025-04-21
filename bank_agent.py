# bank_agent.py

from dotenv import load_dotenv
from google.adk.agents import Agent, LlmAgent
from tools.bank_statement_tool import bank_statement_tool  # Import the updated tool
from google.genai.types import GenerateContentConfig

load_dotenv(override=True)

generation_config = GenerateContentConfig(
    max_output_tokens=8192, # Keep this, but less likely to be hit now
    # temperature=0.7,
    # top_p=1.0,
)

agent = LlmAgent(
    name="bank_statement_agent",
    description="Understands user questions about bank statement PDFs based on a file path.", # Slightly updated description
    instruction=(
        "You are a helpful assistant for analyzing bank statements. "
        "The user will provide a question and the file path to a PDF bank statement. "
        "Call the `bank_statement_tool` with the `file_path` argument "
        "to extract transactions from the PDF located at that path. "
        "You will receive the extracted transactions as a JSON list. "
        "**Based on the user's question and the JSON data, provide a concise, natural language answer.** " # Added emphasis
        "**Do not simply output the raw JSON.** Summarize the findings or list the key details as requested by the user in plain text." # Explicit negative constraint and guidance
        " For example, if asked to list transactions, present them clearly, perhaps as a readable list."
    ),
    model="gemini-1.5-pro",
    tools=[bank_statement_tool],  # Register the tool so Gemini can call it.
    generate_content_config=generation_config
)