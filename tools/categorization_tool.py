import os
import json
import logging
from typing import List, Dict, Any
import time

# --- Use Vertex AI SDK ---
import vertexai
from vertexai.generative_models import GenerativeModel, Part, GenerationConfig
from vertexai.generative_models import HarmCategory, HarmBlockThreshold # For safety settings

from google.adk.tools import FunctionTool
from dotenv import load_dotenv

load_dotenv(override=True)

logger = logging.getLogger(__name__)

# --- Vertex AI Configuration ---
try:
    PROJECT_ID = os.getenv("GCP_PROJECT_ID")
    LOCATION = os.getenv("GCP_LOCATION", "us-central1") # Default to 'us' if not set
    if not PROJECT_ID or not LOCATION:
        raise ValueError("GCP_PROJECT_ID and GCP_LOCATION environment variables must be set.")
    # Initialize Vertex AI - This uses Application Default Credentials or the service account
    # specified by GOOGLE_APPLICATION_CREDENTIALS in your .env
    vertexai.init(project=PROJECT_ID, location=LOCATION)
    logger.info(f"Vertex AI initialized for project '{PROJECT_ID}' in location '{LOCATION}'.")
except ValueError as e:
    logger.error(f"Configuration Error: {e}")
except Exception as e_init:
    logger.error(f"Failed to initialize Vertex AI: {e_init}", exc_info=True)
    # Handle error - subsequent calls will likely fail


# --- Predefined Categories (Same as before) ---
CATEGORIES = [
    "Income/Salary", "Rent/Mortgage", "Utilities", "Groceries",
    "Restaurants/Dining Out", "Food Delivery", "Transportation", "Shopping",
    "Subscriptions/Memberships", "Entertainment", "Travel", "Healthcare/Medical",
    "Insurance", "Education", "Personal Care", "Transfers Out", "Transfers In",
    "Cash Withdrawal", "Bank Fees", "Taxes", "Investments",
    "Charity/Donations", "Other Expenses", "Uncategorized"
]

# --- LLM Model for Categorization (Vertex AI Model Name) ---
# Use the appropriate Vertex AI model identifier
CAT_MODEL_NAME = "gemini-1.5-pro" # Or "gemini-1.5-flash-001" or other suitable Vertex model

# --- Helper function to call the categorization LLM using Vertex AI SDK ---
def get_category_from_llm_vertex(description: str) -> str:
    """Calls the Vertex AI Gemini API to categorize a single transaction description."""
    if not description:
        return "Uncategorized"

    # Check if Vertex AI was initialized successfully
    # (A more robust check might involve trying a dummy call or checking a global flag)
    if not PROJECT_ID or not LOCATION:
         logger.error("Vertex AI not initialized due to missing config. Cannot categorize.")
         return "Uncategorized"


    prompt = f"""
    Analyze the following bank transaction description and categorize it into exactly ONE of the following categories.
    Choose the single most appropriate category. If none fit well, choose 'Uncategorized'.
    Respond with ONLY the category name.

    Allowed Categories:
    {', '.join(CATEGORIES)}

    Transaction Description:
    "{description}"

    Category:"""

    try:
        model = GenerativeModel(CAT_MODEL_NAME)
        # Define generation config for Vertex AI
        generation_config = GenerationConfig(
            temperature=0.2,
            # max_output_tokens= # Optional: set a limit if needed, but category names are short
        )
        # Define safety settings for Vertex AI
        safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }

        response = model.generate_content(
            [prompt], # Vertex AI often takes a list of content parts
            generation_config=generation_config,
            safety_settings=safety_settings,
            stream=False, # Use non-streaming for this tool
        )

        # Check response and parse text safely
        if response.candidates and response.candidates[0].content.parts:
            category = response.text.strip()
            if category in CATEGORIES:
                logger.debug(f"Categorized '{description}' as '{category}' (Vertex)")
                return category
            else:
                logger.warning(f"Vertex LLM returned unexpected category '{category}' for '{description}'. Defaulting to Uncategorized.")
                return "Uncategorized"
        else:
            logger.warning(f"Vertex LLM returned no valid text for description '{description}'. Prompt: {prompt}, Response: {response}")
            # Consider logging response.prompt_feedback or response.candidates[0].finish_reason if available
            return "Uncategorized"

    except Exception as e:
        logger.error(f"Error calling Vertex AI categorization LLM for '{description}': {e}", exc_info=True)
        return "Uncategorized"


# --- The Main Tool Function (Updated to call the Vertex helper) ---
def categorize_transactions(transactions_json: str) -> str:
    """
    Takes a JSON string representing a list of transactions (potentially
    wrapped incorrectly by the LLM as a stringified dict like
    '{"result": "[{...}]"}'), categorizes each using Vertex AI LLM, and
    returns an enriched JSON string list with categories added.

    Args:
        transactions_json: JSON string input from the LLM.

    Returns:
        JSON string of the transaction list with an added 'category' field for each,
        or an empty JSON array '[]' on error.
    """
    logger.info("Starting transaction categorization tool (using Vertex AI)...")
    parsed_transactions: List[Dict[str, Any]] = []
    json_string_to_parse = None

    if not isinstance(transactions_json, str):
        logger.error(f"Tool Error: Expected transactions_json to be a string, but got {type(transactions_json)}")
        return json.dumps([])

    # --- Keep the Robust Parsing Logic from the previous step ---
    try:
        try:
            logger.debug("Attempt 1: Parsing input string directly as JSON list...")
            parsed_transactions = json.loads(transactions_json)
            if isinstance(parsed_transactions, list):
                logger.info("Successfully parsed input directly as list.")
                json_string_to_parse = transactions_json # Signal success
            else:
                logger.warning(f"Input parsed, but is not a list (Type: {type(parsed_transactions)}). Checking for wrapped structure...")
                parsed_transactions = []
        except json.JSONDecodeError:
            logger.warning("Attempt 1 failed. Input string is likely not a direct JSON list.")

        if not parsed_transactions:
             logger.debug("Attempt 2: Checking for '{\"result\": \"[...]}\"' structure...")
             if transactions_json.strip().startswith('{"result": "') and transactions_json.strip().endswith('"}'):
                 try:
                     start_marker = '"result": "'
                     start_index = transactions_json.find(start_marker)
                     if start_index != -1:
                         content_start = start_index + len(start_marker)
                         end_index = transactions_json.rfind('"')
                         if end_index > content_start :
                            inner_json_string = transactions_json[content_start:end_index]
                            try:
                                inner_json_string_decoded = json.loads(f'"{inner_json_string}"')
                            except json.JSONDecodeError:
                                logger.warning("Could not JSON-decode the extracted inner string, using as is.")
                                inner_json_string_decoded = inner_json_string

                            logger.debug(f"Attempting to parse extracted inner content: {inner_json_string_decoded[:100]}...")
                            parsed_transactions = json.loads(inner_json_string_decoded)
                            if isinstance(parsed_transactions, list):
                                logger.info("Successfully parsed extracted inner JSON string list.")
                                json_string_to_parse = inner_json_string_decoded # Signal success
                            else:
                                logger.error(f"Extracted inner data did not parse to a list. Type: {type(parsed_transactions)}")
                                parsed_transactions = []
                         else:
                            logger.error("Could not find closing quote for 'result' value.")
                     else:
                         logger.error("Could not find '\"result\": \"' marker.")
                 except json.JSONDecodeError as e:
                     logger.error(f"Failed to parse extracted/unescaped inner JSON string: {e}")
                 except Exception as ex:
                     logger.error(f"Error during manual extraction/parsing: {ex}")
             else:
                 logger.error("Input string did not parse directly and doesn't match wrapped format.")

        if json_string_to_parse is None and not parsed_transactions:
             logger.error("Failed to parse or extract a valid transaction list from the input.")
             return json.dumps([])

    except Exception as parse_error: # Catch potential errors during the parsing itself
        logger.error(f"Tool Error: Unexpected error during input parsing: {parse_error}", exc_info=True)
        return json.dumps([])


    # --- Proceed with categorization ---
    try:
        if not parsed_transactions:
             logger.info("Parsed transaction list is empty (parsing error occurred?). Nothing to categorize.")
             return json.dumps([])

        logger.info(f"Attempting to categorize {len(parsed_transactions)} transactions via Vertex AI.")
        categorized_count = 0
        # *** SET DELAY HERE (e.g., 3 seconds) - adjust if needed ***
        rate_limit_delay_seconds = 10

        for i, transaction in enumerate(parsed_transactions):
            # *** ADD DELAY BEFORE EACH CALL (except the first) ***
            if i > 0:
                logger.debug(f"Waiting {rate_limit_delay_seconds}s before next categorization call...")
                time.sleep(rate_limit_delay_seconds)

            if not isinstance(transaction, dict):
                logger.warning(f"Skipping item, not a dictionary: {transaction}")
                continue

            desc_key_found = None
            lower_keys = {k.lower(): k for k in transaction.keys()}
            possible_keys = ["page transaction details", "description", "details", "narrative", "transaction details"]
            for key in possible_keys:
                if key in lower_keys:
                    desc_key_found = lower_keys[key]
                    break

            if desc_key_found:
                description = str(transaction.get(desc_key_found, ""))
                category = get_category_from_llm_vertex(description) # Call the helper
                transaction['category'] = category
                if category != "Uncategorized":
                     categorized_count += 1
            else:
                logger.warning(f"Could not find a description key in transaction: {transaction}. Assigning Uncategorized.")
                transaction['category'] = "Uncategorized"


        logger.info(f"Finished categorization. Assigned categories to {categorized_count} transactions.")
        return json.dumps(parsed_transactions, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.error(f"Tool Error: Unexpected error during categorization loop: {e}", exc_info=True)
        # Return partially categorized list if loop fails mid-way
        return json.dumps(parsed_transactions or [], ensure_ascii=False, indent=2)


# Register the function as a FunctionTool (No change needed here)
categorization_tool = FunctionTool(
    func=categorize_transactions)