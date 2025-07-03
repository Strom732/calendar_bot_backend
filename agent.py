from langchain.agents import Tool, initialize_agent, AgentType
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain_groq import ChatGroq
from datetime import datetime, timedelta
import re

from google.oauth2 import service_account
from googleapiclient.discovery import build
from dotenv import load_dotenv
import os

load_dotenv()

# === Groq LLM ===
llm = ChatGroq(
    temperature=0,
    model_name="llama3-70b-8192"
)

# === Google Calendar Setup ===
SCOPES = ["https://www.googleapis.com/auth/calendar"]
SERVICE_ACCOUNT_FILE = "service_account.json"
CALENDAR_ID = "abhinandansingh9325@gmail.com"  # Replace with your calendar ID

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)
service = build("calendar", "v3", credentials=credentials)

# === Booking Tool ===
def book_meeting(input_text: str) -> str:
    try:
        match = re.search(
            r'with (.+?) on (\d{4}-\d{2}-\d{2}) at (\d{2}:\d{2}) for (\d+)',
            input_text
        )
        if not match:
            return "❌ Couldn't understand the meeting details."

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
        return f"❌ Error: {str(e)}"

# === Tool for the Agent ===
tools = [
    Tool(
        name="book_meeting",
        func=book_meeting,
        description="Use this tool to book meetings. Input format: 'Book a meeting with [name] on YYYY-MM-DD at HH:MM for [duration] minutes'"
    )
]

# === Memory ===
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

# === Prompt Template ===
prompt = PromptTemplate.from_template("""
You are a friendly calendar assistant. Help the user book a meeting in a conversation.
Ask if they want to book. If yes, ask one by one for:

1. Name of the person the meeting is with,
2. Date in YYYY-MM-DD format,
3. Time in 24-hour format (HH:MM),
4. Duration in minutes.

Only when all 4 are available, use the booking tool to schedule the meeting.

{chat_history}
Human: {input}
AI:""")

# === Final Agent ===
agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    memory=memory,
    verbose=True,
    agent_kwargs={"prompt": prompt}
)
