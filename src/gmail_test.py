import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Scope = exactly what we're asking permission for.
# "readonly" means this token can NEVER modify or send mail — safest possible.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

CREDENTIALS_FILE = "credentials/credentials.json"
TOKEN_FILE = "credentials/token.json"


def get_gmail_service():
    creds = None

    # If we've authorized before, a token.json exists — reuse it (no browser).
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    # If there's no valid token, run the OAuth flow.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            # Token expired but refreshable → refresh silently.
            creds.refresh(Request())
        else:
            # First time: open a browser for you to approve access.
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the token so future runs skip the browser step.
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    # Build the Gmail API client object we'll make calls with.
    return build("gmail", "v1", credentials=creds)


def list_recent_emails():
    service = get_gmail_service()

    # Ask Gmail for the 5 most recent message IDs.
    results = service.users().messages().list(userId="me", maxResults=5).execute()
    messages = results.get("messages", [])

    if not messages:
        print("No messages found.")
        return

    print("Your 5 most recent emails:\n")
    for msg in messages:
        # Each item only has an ID — fetch the full message to read its headers.
        full = service.users().messages().get(userId="me", id=msg["id"]).execute()

        # Headers hold Subject, From, etc. Pull them into a dict for easy access.
        headers = full["payload"]["headers"]
        header_dict = {h["name"]: h["value"] for h in headers}

        # YOU: get the "Subject" from header_dict (use .get so it doesn't crash
        #      if missing — .get("Subject", "(no subject)") )
        subject = header_dict.get("Subject","(no subject)")

        # YOU: get the "From" the same way, defaulting to "(unknown)"
        sender = header_dict.get("From", "(unknown)")

        print(f"From: {sender}")
        print(f"Subject: {subject}")
        print("-" * 40)


if __name__ == "__main__":
    list_recent_emails()