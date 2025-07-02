from langchain.agents import Tool, initialize_agent
from langchain_groq import ChatGroq  # or your LLM provider
from datetime import datetime, timedelta
import re

from google.oauth2 import service_account
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

# Groq / your LLM setup
llm = ChatGroq(temperature=0, model_name="llama3-70b-8192")


# Google Calendar setup
SCOPES = ["https://www.googleapis.com/auth/calendar"]
SERVICE_ACCOUNT_FILE = "service_account.json"
CALENDAR_ID = "abhinandansingh9325@gmail.com"  # Replace with your calendar ID

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)
service = build("calendar", "v3", credentials=credentials)

# Single input string function
def book_meeting(input_text: str) -> str:
    try:
        print("DEBUG: Received input_text ->", input_text)

        # More flexible regex pattern
        match = re.search(
            r'with\s+(.*?)\s+on\s+(\d{4}-\d{2}-\d{2})\s+at\s+(\d{1,2}:\d{2})\s+for\s+(\d+)',
            input_text,
            re.IGNORECASE
        )

        if not match:
            return f"Unable to understand the meeting details from input: '{input_text}'"

        name, date, time, duration = match.groups()
        duration = int(duration)

        start_dt = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
        end_dt = start_dt + timedelta(minutes=duration)

        timezone = "Asia/Kolkata"
        event = {
            "summary": name,
            "start": {"dateTime": start_dt.isoformat(), "timeZone": timezone},
            "end": {"dateTime": end_dt.isoformat(), "timeZone": timezone}
        }

        created_event = service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
        return f"✅ Meeting booked successfully: {created_event.get('htmlLink')}"

    except Exception as e:
        return f"❌ Error while booking meeting: {str(e)}"

# Tool wrapper
tools = [
    Tool(
        name="book_meeting",
        func=book_meeting,
        description="Use this tool to book meetings. Input should be like 'Book a meeting with Abhi on 2025-07-03 at 15:00 for 30 minutes'"
    )
]

# Agent
agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent="zero-shot-react-description",
    verbose=True
)
