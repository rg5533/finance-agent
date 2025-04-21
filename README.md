# 💼 Bank Statement Agent

Your personal financial assistant that makes sense of bank statements! This Google ADK-powered agent analyzes bank statements in PDF format, extracting transaction data using Document AI and answering your questions in plain language - no more squinting at tiny numbers or scrolling through pages of transactions.

## Features

- PDF bank statement parsing using Google Document AI
- Natural language question answering about bank statements
- Transaction data extraction and analysis
- Command-line interface for easy interaction
- Detailed logging for debugging and tracking

## Prerequisites

- Python 3.9+
- Google Cloud Platform account with Document AI enabled
- Document AI processor configured for form parsing
- Environment variables set up for GCP authentication

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/bank-agent.git
cd bank-agent
```

2. Create and activate a virtual environment:
```bash
python -m venv adk-env
.\adk-env\Scripts\activate  # On Windows
# source adk-env/bin/activate  # On Unix/MacOS
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables in a `.env` file:
```
GCP_PROJECT_ID=your-gcp-project-id
GCP_LOCATION=us  # or your preferred region
DOCUMENT_AI_PROCESSOR_ID=your-processor-id
GOOGLE_APPLICATION_CREDENTIALS=path/to/your/credentials.json
```

## Quick Start ⚡

Just point the agent at your statement and ask away! Use the command-line interface:

```bash
python main.py path/to/your/statement.pdf "What is my current balance?"
```

Curious about your spending? Try questions like:

```bash
python main.py path/to/your/statement.pdf "List all transactions over $100"
python main.py path/to/your/statement.pdf "What was my largest deposit this month?"
python main.py path/to/your/statement.pdf "How much did I spend on groceries?"
```

## How It Works

The agent uses the Google Agent Development Kit (ADK) to create an LLM-powered agent that:

1. Takes a user question and PDF file path as input
2. Uses the `bank_statement_tool` to extract transaction data from the PDF
3. Processes the extracted data using Google Document AI
4. Analyzes the transaction data to answer the user's question
5. Returns a natural language response

## Development

The project structure is organized as follows:

- `bank_agent.py` - Main agent definition
- `main.py` - CLI entrypoint
- `tools/bank_statement_tool.py` - Tool for PDF parsing
- `logs/` - Directory for log files
- `test-files/` - Test files and examples

## Logging

Detailed logs are saved in the `logs/` directory with timestamps. Each run creates a new log file with format `agent_YYYYMMDD_HHMMSS.log`.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Future Improvements

This project is under active development with iterative improvements planned:

- LLM to use multiple tools
- Adding database support for storing transactions
- Enhanced transaction categorization tool
- Financial insights and spending analysis
- Web interface for easier interaction
- Multi-statement analysis for tracking over time

Feedback and feature requests are welcome!

## License

This project is licensed under the MIT License - see the LICENSE file for details.