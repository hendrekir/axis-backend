import os
from datetime import datetime

from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from sqlalchemy.ext.asyncio import AsyncSession

from models import User

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
]


def _get_credentials(user: User) -> Credentials | None:
    """Build Google credentials from stored tokens. Returns None if not connected."""
    if not user.gmail_access_token:
        return None

    creds = Credentials(
        token=user.gmail_access_token,
        refresh_token=user.gmail_refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ["GOOGLE_CLIENT_ID"],
        client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
        scopes=SCOPES,
    )

    if creds.expiry:
        creds.expiry = user.gmail_token_expiry

    return creds


async def refresh_if_needed(user: User, db: AsyncSession) -> Credentials | None:
    """Return valid credentials, refreshing the access token if expired."""
    creds = _get_credentials(user)
    if creds is None:
        return None

    if creds.expired and creds.refresh_token:
        creds.refresh(GoogleRequest())
        user.gmail_access_token = creds.token
        user.gmail_token_expiry = creds.expiry
        await db.commit()

    return creds


def _extract_header(headers: list[dict], name: str) -> str:
    """Pull a header value from Gmail message headers."""
    for h in headers:
        if h["name"].lower() == name.lower():
            return h["value"]
    return ""


async def fetch_recent_emails(
    user: User, db: AsyncSession, after: datetime | None = None, max_results: int = 20
) -> list[dict]:
    """Fetch recent inbox emails, optionally only those after a timestamp."""
    creds = await refresh_if_needed(user, db)
    if creds is None:
        return []

    service = build("gmail", "v1", credentials=creds)

    # Gmail q parameter: after:YYYY/MM/DD (epoch seconds also works)
    query = None
    if after:
        epoch = int(after.timestamp())
        query = f"after:{epoch}"

    results = service.users().messages().list(
        userId="me", labelIds=["INBOX"], maxResults=max_results, q=query
    ).execute()

    messages = results.get("messages", [])
    if not messages:
        return []

    emails = []
    for msg_ref in messages:
        msg = service.users().messages().get(
            userId="me", id=msg_ref["id"], format="metadata",
            metadataHeaders=["From", "Subject", "Date"],
        ).execute()

        headers = msg.get("payload", {}).get("headers", [])
        emails.append({
            "id": msg["id"],
            "thread_id": msg.get("threadId"),
            "from": _extract_header(headers, "From"),
            "subject": _extract_header(headers, "Subject"),
            "date": _extract_header(headers, "Date"),
            "snippet": msg.get("snippet", ""),
            "label_ids": msg.get("labelIds", []),
            "is_unread": "UNREAD" in msg.get("labelIds", []),
        })

    return emails
