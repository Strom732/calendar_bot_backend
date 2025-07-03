from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

load_dotenv()

app = FastAPI()

# Store temporary conversation state
conversation_state: Dict[str, Dict] = {}

# Pydantic models
class ChatRequest(BaseModel):
    user_input: str
    session_id: str = "default"  # Basic session management (extend later)

# Calendar booking function
def create_event(name, date, time, duration):
    try:
        creds = Credentials.from_service_account_file(
            "service_account.json",
            scopes=["https://www.googleapis.com/auth/calendar"]
        )
        service = build("calendar", "v3", credentials=creds)

        start_time = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
        end_time = start_time + timedelta(minutes=duration)

        event = {
            "summary": name,
            "start": {"dateTime": start_time.isoformat(), "timeZone": "Asia/Kolkata"},
            "end": {"dateTime": end_time.isoformat(), "timeZone": "Asia/Kolkata"},
        }

        calendar_id = os.getenv("GOOGLE_CALENDAR_ID")
        created_event = service.events().insert(calendarId=calendar_id, body=event).execute()
        return created_event.get("htmlLink")

    except Exception as e:
        return str(e)

# Chat endpoint with flow control
@app.post("/chat")
def chat_with_agent(data: ChatRequest):
    session = conversation_state.setdefault(data.session_id, {
        "step": 0,
        "name": None,
        "date": None,
        "time": None,
        "duration": None
    })

    user_input = data.user_input.strip().lower()

    if session["step"] == 0:
        session["step"] += 1
        return {"response": "👋 Hello! Would you like to book a meeting?"}

    elif session["step"] == 1:
        if "yes" in user_input:
            session["step"] += 1
            return {"response": "Great! Who is the meeting with?"}
        else:
            return {"response": "Alright, let me know if you change your mind!"}

    elif session["step"] == 2:
        session["name"] = data.user_input
        session["step"] += 1
        return {"response": "On which date would you like to schedule it? (e.g. 2025-07-03)"}

    elif session["step"] == 3:
        try:
            datetime.strptime(data.user_input, "%Y-%m-%d")
            session["date"] = data.user_input
            session["step"] += 1
            return {"response": "At what time? (24-hour format e.g. 13:00)"}
        except ValueError:
            return {"response": "⚠️ Please enter a valid date in YYYY-MM-DD format."}

    elif session["step"] == 4:
        session["time"] = data.user_input
        session["step"] += 1
        return {"response": "And how long should the meeting be? (in minutes)"}

    elif session["step"] == 5:
        try:
            duration = int(data.user_input)
            session["duration"] = duration
            link = create_event(
                session["name"], session["date"], session["time"], session["duration"]
            )
            conversation_state.pop(data.session_id, None)  # Reset state
            return {"response": f"✅ Booking your meeting...\n\n[Click here to view it]({link})"}
        except ValueError:
            return {"response": "⚠️ Please enter duration in minutes (e.g. 30)"}

    return {"response": "Something went wrong. Please try again."}
