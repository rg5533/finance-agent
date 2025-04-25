# bank_agent.py

from dotenv import load_dotenv
from google.adk.agents import Agent, LlmAgent
from tools.bank_statement_tool import bank_statement_tool  # Import the updated tool
from tools.categorization_tool import categorization_tool # Import the new tool

from google.genai.types import GenerateContentConfig

load_dotenv(override=True)

generation_config = GenerateContentConfig(
    max_output_tokens=8192, # Keep this, but less likely to be hit now
    # temperature=0.7,
    # top_p=1.0,
)

agent = LlmAgent(
    name="bank_statement_agent",
    description="Extracts and categorizes bank statement transactions.", # Slightly updated description
    instruction=(
        "You are a helpful assistant for analyzing bank statements. The user will provide a question and the file path."
        "Follow these steps precisely:"
        "1. Call the `bank_statement_tool` with the `file_path` argument provided by the user to extract the raw transaction data. You will receive a JSON string list back as the tool's result."
        "2. Take the JSON string result from step 1 and call the `categorize_transactions` tool, passing this JSON string as the `transactions_json` argument. This tool will categorize the transactions and return a new JSON string list, now including a 'category' field for each transaction."
        "3. Using the **categorized** JSON data returned by the `categorize_transactions` tool (the result from step 2), answer the original user's question in a clear, readable, natural language format. **Do NOT output raw JSON to the user.**"
        "4. If the user asks to list transactions (like 'List all transactions'), present them neatly (e.g., using bullet points or a simple table format) including the Date, Description, Amount, and the assigned Category from the categorized JSON."
        "Ensure you complete both tool calls sequentially before formulating the final answer for the user."
    ),
    model="gemini-1.5-pro",
    tools=[bank_statement_tool, categorization_tool],  # Register the tool so Gemini can call it.
    generate_content_config=generation_config
)