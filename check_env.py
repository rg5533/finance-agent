import os, google.auth
from dotenv import load_dotenv
load_dotenv(override=True)

print("GCP_PROJECT_ID =", os.getenv("GCP_PROJECT_ID"))
print("GOOGLE_APPLICATION_CREDENTIALS =", os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))

# explicitly get credentials from the service account JSON file
from google.oauth2 import service_account

creds = service_account.Credentials.from_service_account_file(
    os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
)
project = os.getenv("GCP_PROJECT_ID")

print("Authenticated as:", creds.service_account_email)
print("Detected project:", project)
