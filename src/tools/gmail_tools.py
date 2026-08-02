import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
CREDENTIALS_FILE = "credentials/credentials.json"
TOKEN_FILE = "credentials/token.json"


def get_gmail_service():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
    return build("gmail", "v1", credentials=creds)


# Build the Gmail service once, then reuse it across all tool calls
# (so we don't re-authenticate on every single email).
_service = None
def _svc():
    global _service
    if _service is None:
        _service = get_gmail_service()
    return _service


# ---- TOOL 1: read the inbox ----
def list_recent_emails(max_results=5):
    results = _svc().users().messages().list(userId="me", maxResults=max_results).execute()
    messages = results.get("messages", [])
    out = []
    for msg in messages:
        full = _svc().users().messages().get(userId="me", id=msg["id"]).execute()
        headers = {h["name"]: h["value"] for h in full["payload"]["headers"]}
        out.append({
            "id": msg["id"],
            "sender": headers.get("From", "(unknown)"),
            "subject": headers.get("Subject", "(no subject)"),
        })
    return out


# ---- TOOL 2: peek at an email's content ----
def get_email_body(email_id):
    full = _svc().users().messages().get(userId="me", id=email_id).execute()
    # "snippet" is Gmail's short preview — simpler than decoding the full body.
    return full.get("snippet", "(no preview available)")


# ---- TOOL 3: a SIMULATED action (prints, changes nothing) ----
def label_email(email_id, label):
    print(f"   [SIMULATED] Would label email {email_id} as '{label}'")
    return f"Email {email_id} labeled as '{label}' (simulated)"