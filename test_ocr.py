import os
from google.cloud import documentai_v1 as documentai
from google.api_core.client_options import ClientOptions

project_id = os.getenv("GCP_PROJECT_ID")
location = os.getenv("GCP_LOCATION") or "us"
processor_id = os.getenv("DOCUMENT_AI_PROCESSOR_ID")
file_path = "sample.pdf"

client = documentai.DocumentProcessorServiceClient(
    client_options=ClientOptions(api_endpoint=f"{location}-documentai.googleapis.com")
)

name = f"projects/{project_id}/locations/{location}/processors/{processor_id}"

with open(file_path, "rb") as file:
    pdf_content = file.read()

raw_document = documentai.RawDocument(content=pdf_content, mime_type="application/pdf")
request = documentai.ProcessRequest(name=name, raw_document=raw_document)

result = client.process_document(request=request)
document = result.document

# Helper function to extract text
def get_text(doc, el):
    text = ''
    for segment in el.text_anchor.text_segments:
        start_index = int(segment.start_index) if segment.start_index else 0
        end_index = int(segment.end_index)
        text += doc.text[start_index:end_index]
    return text.strip().replace('\n', ' ')

# Loop through pages and tables and print structured output
for page_number, page in enumerate(document.pages):
    print(f"\n📄 Page {page_number + 1}")
    for table_number, table in enumerate(page.tables):
        print(f"\n🧾 Table {table_number + 1}:")
        rows = []

        # Header rows (if exist)
        header_row_values = []
        for header_row in table.header_rows:
            header_row_values = [get_text(document, cell.layout) for cell in header_row.cells]
            rows.append(header_row_values)

        # Body rows
        for body_row in table.body_rows:
            body_row_values = [get_text(document, cell.layout) for cell in body_row.cells]
            rows.append(body_row_values)

        # Print structured rows neatly
        for row in rows:
            print("\t".join(row))
