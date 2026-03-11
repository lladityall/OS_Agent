#!/usr/bin/env python3
"""
RAM Tool: Email & Calendar
Read/send email via Gmail API; manage Google Calendar events and tasks.

SETUP REQUIRED:
1. Go to https://console.cloud.google.com/
2. Create a project, enable Gmail API + Google Calendar API
3. Create OAuth 2.0 credentials (Desktop app)
4. Download credentials.json to ~/.ram/credentials.json
5. Run: python3 tools/email_tool.py --setup
"""

import os
import json
import pickle
from pathlib import Path
from typing import Optional, List
from datetime import datetime, timedelta

CONFIG_DIR = Path.home() / ".ram"
CONFIG_DIR.mkdir(exist_ok=True)
TOKEN_PATH = CONFIG_DIR / "gmail_token.pickle"
CREDS_PATH = CONFIG_DIR / "credentials.json"

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/tasks",
]


def _get_credentials():
    """Get or refresh Google OAuth credentials"""
    creds = None
    if TOKEN_PATH.exists():
        with open(TOKEN_PATH, "rb") as f:
            creds = pickle.load(f)

    if creds and creds.valid:
        return creds

    if creds and creds.expired and creds.refresh_token:
        from google.auth.transport.requests import Request
        creds.refresh(Request())
    else:
        if not CREDS_PATH.exists():
            raise FileNotFoundError(
                f"credentials.json not found at {CREDS_PATH}. "
                "Download from Google Cloud Console."
            )
        from google_auth_oauthlib.flow import InstalledAppFlow
        flow = InstalledAppFlow.from_client_secrets_file(str(CREDS_PATH), SCOPES)
        creds = flow.run_local_server(port=0)

    with open(TOKEN_PATH, "wb") as f:
        pickle.dump(creds, f)
    return creds


# ── Gmail ─────────────────────────────────────────────────────────────────

def get_unread_emails(max_results: int = 10) -> dict:
    """Fetch unread emails from Gmail"""
    try:
        from googleapiclient.discovery import build
        creds = _get_credentials()
        service = build("gmail", "v1", credentials=creds)

        result = service.users().messages().list(
            userId="me", q="is:unread", maxResults=max_results
        ).execute()

        messages = result.get("messages", [])
        emails = []
        for msg in messages:
            msg_data = service.users().messages().get(
                userId="me", id=msg["id"], format="metadata",
                metadataHeaders=["From", "Subject", "Date"]
            ).execute()

            headers = {h["name"]: h["value"] for h in msg_data["payload"]["headers"]}
            emails.append({
                "id": msg["id"],
                "from": headers.get("From"),
                "subject": headers.get("Subject"),
                "date": headers.get("Date"),
                "snippet": msg_data.get("snippet", ""),
            })
        return {"success": True, "emails": emails, "count": len(emails)}
    except Exception as e:
        return {"success": False, "error": str(e), "setup_required": "credentials.json missing"}


def send_email(to: str, subject: str, body: str, cc: Optional[str] = None) -> dict:
    """Send an email via Gmail"""
    try:
        import base64
        from email.mime.text import MIMEText
        from googleapiclient.discovery import build

        creds = _get_credentials()
        service = build("gmail", "v1", credentials=creds)

        message = MIMEText(body)
        message["to"] = to
        message["subject"] = subject
        if cc:
            message["cc"] = cc

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        result = service.users().messages().send(
            userId="me", body={"raw": raw}
        ).execute()
        return {"success": True, "message_id": result["id"]}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ── Google Calendar ────────────────────────────────────────────────────────

def get_upcoming_events(days: int = 7, max_results: int = 20) -> dict:
    """Fetch upcoming calendar events"""
    try:
        from googleapiclient.discovery import build

        creds = _get_credentials()
        service = build("calendar", "v3", credentials=creds)

        now = datetime.utcnow().isoformat() + "Z"
        later = (datetime.utcnow() + timedelta(days=days)).isoformat() + "Z"

        result = service.events().list(
            calendarId="primary",
            timeMin=now,
            timeMax=later,
            maxResults=max_results,
            singleEvents=True,
            orderBy="startTime"
        ).execute()

        events = []
        for item in result.get("items", []):
            start = item["start"].get("dateTime", item["start"].get("date"))
            events.append({
                "id": item["id"],
                "title": item.get("summary", "(no title)"),
                "start": start,
                "location": item.get("location", ""),
                "description": item.get("description", "")[:200],
            })
        return {"success": True, "events": events}
    except Exception as e:
        return {"success": False, "error": str(e)}


def create_calendar_event(
    title: str,
    start: str,  # ISO format: "2025-03-15T10:00:00"
    end: str,
    description: str = "",
    location: str = "",
) -> dict:
    """Create a calendar event"""
    try:
        from googleapiclient.discovery import build
        creds = _get_credentials()
        service = build("calendar", "v3", credentials=creds)

        event = {
            "summary": title,
            "description": description,
            "location": location,
            "start": {"dateTime": start, "timeZone": "Asia/Kolkata"},
            "end": {"dateTime": end, "timeZone": "Asia/Kolkata"},
        }
        result = service.events().insert(calendarId="primary", body=event).execute()
        return {"success": True, "event_id": result["id"], "link": result.get("htmlLink")}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ── Google Tasks ────────────────────────────────────────────────────────────

def list_tasks(max_results: int = 20) -> dict:
    """List Google Tasks"""
    try:
        from googleapiclient.discovery import build
        creds = _get_credentials()
        service = build("tasks", "v1", credentials=creds)
        result = service.tasks().list(tasklist="@default", maxResults=max_results).execute()
        tasks = [{"id": t["id"], "title": t.get("title"), "status": t.get("status"),
                  "due": t.get("due", "")} for t in result.get("items", [])]
        return {"success": True, "tasks": tasks}
    except Exception as e:
        return {"success": False, "error": str(e)}


def add_task(title: str, notes: str = "", due: Optional[str] = None) -> dict:
    """Add a task to Google Tasks"""
    try:
        from googleapiclient.discovery import build
        creds = _get_credentials()
        service = build("tasks", "v1", credentials=creds)
        task = {"title": title, "notes": notes}
        if due:
            task["due"] = due
        result = service.tasks().insert(tasklist="@default", body=task).execute()
        return {"success": True, "task_id": result["id"]}
    except Exception as e:
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    import sys
    if "--setup" in sys.argv:
        print("Starting OAuth setup...")
        try:
            creds = _get_credentials()
            print("✓ Credentials saved successfully!")
        except Exception as e:
            print(f"✗ Setup failed: {e}")
    else:
        print("Email tool loaded. Run with --setup to authenticate.")
        print(f"Put credentials.json at: {CREDS_PATH}")
