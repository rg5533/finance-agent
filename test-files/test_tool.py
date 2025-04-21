#!/usr/bin/env python
"""Unit‑test for parse_bank_statement (Option A)."""
import base64
import json
import sys
from pathlib import Path
from pprint import pprint

from dotenv import load_dotenv
from tools.bank_statement_tool import parse_bank_statement

load_dotenv(override=True)


def run_test(pdf_path: Path) -> None:
    if not pdf_path.exists():
        sys.exit(f"❌  PDF not found: {pdf_path}")

    encoded = base64.b64encode(pdf_path.read_bytes()).decode()

    print("Calling parse_bank_statement …")
    try:
        raw = parse_bank_statement(content_b64=encoded, mime_type="application/pdf")
    except Exception as exc:
        sys.exit(f"❌  Tool raised an error:\n{exc}")

    print("\nRaw JSON returned:")
    print(raw)

    print("\nPretty‑printed transactions:")
    pprint(json.loads(raw))


if __name__ == "__main__":
    run_test(Path(sys.argv[1]) if len(sys.argv) > 1 else Path("sample.pdf"))
