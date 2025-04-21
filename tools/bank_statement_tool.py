# tools/bank_statement_tool.py

import os
import json
from typing import List, Dict, Optional # Added Optional
from pathlib import Path
from google.cloud import documentai_v1 as documentai
from google.api_core.client_options import ClientOptions
from google.adk.tools import FunctionTool
import logging

logger = logging.getLogger(__name__)

# Helper function to extract text (Keep the one that works from test_ocr.py)
def get_text(doc: documentai.Document, el: documentai.Document.Page.Layout) -> str:
    """Extracts text from a Document AI layout element."""
    text = ''
    # Check if layout, text_anchor, and text_segments exist
    if el and el.text_anchor and el.text_anchor.text_segments:
        for segment in el.text_anchor.text_segments:
            start_index = int(segment.start_index) if segment.start_index else 0
            end_index = int(segment.end_index)
            # Ensure indices are within bounds
            if 0 <= start_index <= end_index <= len(doc.text):
                 text += doc.text[start_index:end_index]
            else:
                 logger.warning(f"Invalid text segment indices: start={start_index}, end={end_index}, doc_len={len(doc.text)}")

    return text.strip().replace('\n', ' ')


# --- Function to identify the transaction table ---
# This is a heuristic and might need adjustment based on common statement layouts
def is_transaction_table(headers: List[str]) -> bool:
    """
    Checks if a list of header strings likely represents a transaction table
    by looking for keywords *within* the header strings. (With extra debugging)
    """
    if not headers: # Handle empty header list case
        logger.debug("Header check: Received empty headers list.")
        return False

    headers_lower = [h.lower().strip() for h in headers]
    logger.debug(f"Header check: Lowercase headers = {headers_lower}") # Log lowercase headers

    date_keywords = ["date", "transaction date", "posting date"]
    desc_keywords = ["description", "details", "narrative", "transaction details"]
    amount_keywords = ["amount", "debit", "credit"]

    # Check date
    has_date = False
    for h in headers_lower:
        if any(kw in h for kw in date_keywords):
            has_date = True
            break
    logger.debug(f"Header check: has_date = {has_date}")

    # Check description
    has_desc = False
    for h in headers_lower:
        if any(kw in h for kw in desc_keywords):
            has_desc = True
            break
    logger.debug(f"Header check: has_desc = {has_desc}")

    # Check amount
    has_amount = False
    for h in headers_lower:
        if any(kw in h for kw in amount_keywords):
            has_amount = True
            break
    logger.debug(f"Header check: has_amount = {has_amount}")

    # Final decision
    result = has_date and has_desc and has_amount
    logger.debug(f"Header check: Final result = {result} (date:{has_date}, desc:{has_desc}, amount:{has_amount})")

    return result


# --- Main Tool Function ---
def parse_bank_statement(*, file_path: str) -> str:
    """
    Parses a PDF bank statement from a given file path and extracts transaction data
    using Google Document AI, focusing on identifying the transaction table by headers.

    Args:
        file_path: The absolute path to the PDF file.

    Returns:
        JSON string of extracted transactions, or an empty JSON array '[]' on error or if no transaction table is found.
    """
    try:
        pdf_path_obj = Path(file_path)
        if not pdf_path_obj.is_file():
            logger.error(f"Tool Error: File not found at path: {file_path}")
            return json.dumps([])

        pdf_bytes = pdf_path_obj.read_bytes()
        mime_type = "application/pdf"

        project_id = os.getenv("GCP_PROJECT_ID")
        location = os.getenv("GCP_LOCATION", "us")
        processor_id = os.getenv("DOCUMENT_AI_PROCESSOR_ID")

        if not all([project_id, location, processor_id]):
            logger.error("Tool Error: Missing GCP config environment variables.")
            return json.dumps([])

        client = documentai.DocumentProcessorServiceClient(
            client_options=ClientOptions(api_endpoint=f"{location}-documentai.googleapis.com")
        )
        name = f"projects/{project_id}/locations/{location}/processors/{processor_id}"

        raw_document = documentai.RawDocument(content=pdf_bytes, mime_type=mime_type)
        request = documentai.ProcessRequest(name=name, raw_document=raw_document)

        result = client.process_document(request=request)
        document = result.document

        logger.info(f"Document AI processed {len(document.pages)} pages for {file_path}.")

        transactions: List[Dict[str, str]] = []
        found_transaction_table = False

        for page_number, page in enumerate(document.pages):
            logger.debug(f"Scanning Page {page_number + 1} with {len(page.tables)} tables.")
            for table_number, table in enumerate(page.tables):
                if not table.header_rows:
                    logger.debug(f"Skipping Table {table_number + 1} on page {page_number + 1} (no header rows).")
                    continue

                # Extract actual headers from the first header row
                header_row = table.header_rows[0]
                actual_headers = [get_text(document, cell.layout) for cell in header_row.cells]
                logger.info(f"Table {table_number + 1} Headers: {actual_headers}")

                # Check if this looks like the transaction table using our heuristic
                if is_transaction_table(actual_headers):
                    logger.info(f"--> Found potential transaction table (Table {table_number + 1}) on page {page_number + 1}.")
                    found_transaction_table = True

                    # Use the *actual headers* (lowercase) for mapping
                    header_keys = [h.lower().strip() for h in actual_headers]

                    for row_index, body_row in enumerate(table.body_rows):
                        row_values = [get_text(document, cell.layout) for cell in body_row.cells]

                        # Create a dictionary for the row, mapping header to value
                        # Ensure we don't go out of bounds if row has fewer cells than header
                        if len(row_values) >= len(header_keys):
                            # Create dictionary using actual headers as keys
                            row_dict = dict(zip(header_keys, row_values))
                            transactions.append(row_dict)
                        else:
                            logger.warning(f"Skipping row {row_index+1} in Table {table_number+1} (Page {page_number+1}) due to cell count mismatch (Headers: {len(header_keys)}, Cells: {len(row_values)}) Row: {row_values}")

                    # Optional: If you assume only ONE transaction table per document, you could break here
                    # break # Uncomment if you only want the first matching table

            # Optional: If you only want the first matching table across pages, you could break here too
            # if found_transaction_table:
            #     break

        if not found_transaction_table:
             logger.warning(f"No tables matching transaction criteria found in {file_path}.")

        logger.info(f"Extracted {len(transactions)} transaction rows.")
        return json.dumps(transactions, ensure_ascii=False)

    except FileNotFoundError:
        logger.error(f"Tool Error: File not found at path: {file_path}")
        return json.dumps([])
    except Exception as e:
        logger.error(f"Tool Error: An unexpected error occurred: {e}", exc_info=True)
        return json.dumps([])

# Register the function as a tool
bank_statement_tool = FunctionTool(parse_bank_statement)