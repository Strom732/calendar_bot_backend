from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
from agent import agent

import os
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

load_dotenv()

app = FastAPI()

# Pydantic models
class BookingRequest(BaseModel):
    name: str
    date: str  # Format: "YYYY-MM-DD"
    time: str  # Format: "HH:MM"
    duration: int  # in minutes

class ChatRequest(BaseModel):
    user_input: str

# Function to create Google Calendar event
def create_event(name, date, time, duration):
    try:
        creds = Credentials.from_service_account_file(
            "service_account.json",  # <- path to your JSON service account key
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
        if not calendar_id:
            raise ValueError("Missing GOOGLE_CALENDAR_ID in environment variables")

        event_result = service.events().insert(calendarId=calendar_id, body=event).execute()

        return {
            "message": "Booked!",
            "link": event_result.get("htmlLink")
        }

    except Exception as e:
        return {"error": str(e)}

# Direct booking endpoint
@app.post("/book")
def book_appointment(data: BookingRequest):
    return create_event(data.name, data.date, data.time, data.duration)

# Chat agent endpoint
@app.post("/chat")
def chat_with_agent(data: ChatRequest):
    try:
        response = agent.invoke({"input": data.user_input})
        return {"response": response.get("output")}
    except Exception as e:
        return {"error": str(e)}
