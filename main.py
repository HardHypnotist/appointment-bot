from fastapi import FastAPI, Request
import requests
import os
import psycopg2
from datetime import datetime

app = FastAPI()

@app.middleware("http")
async def log_all_requests(request: Request, call_next):
    print(f"REQUEST: {request.method} {request.url.path}")
    response = await call_next(request)
    return response

print("WHATSAPP BOT STARTED")

VERIFY_TOKEN = "anmol_bot_2026"

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
DATABASE_URL = os.getenv("DATABASE_URL")

print("TOKEN EXISTS:", bool(WHATSAPP_TOKEN))
print("PHONE ID EXISTS:", bool(PHONE_NUMBER_ID))
print("DATABASE EXISTS:", bool(DATABASE_URL))
try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS patients (
        phone TEXT PRIMARY KEY,
        created_at TIMESTAMP,
        first_contact_time TIMESTAMP,
        review_sent BOOLEAN DEFAULT FALSE,
        reminder_sent BOOLEAN DEFAULT FALSE
    )
    """)

    conn.commit()

    print("POSTGRES TABLE READY")

    conn.close()

except Exception as e:
    print("POSTGRES ERROR:", str(e))


def send_whatsapp_message(to_number, message):
    print("Sending message to:", to_number)

    url = f"https://graph.facebook.com/v23.0/{PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {
            "body": message
        }
    }

    response = requests.post(url, headers=headers, json=payload)

    print("Status Code:", response.status_code)
    print("Response:", response.text)


@app.get("/")
def home():
    return {"status": "running"}


@app.get("/webhook")
async def verify(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return int(challenge)

    return {"error": "verification failed"}


@app.post("/webhook")
async def webhook(request: Request):
    print("WEBHOOK HIT")
    data = await request.json()

    print("FULL PAYLOAD:")
    print(data)

    try:
        entry = data["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]

        if "messages" in value:

            message = value["messages"][0]
            sender = message["from"]
            message_text = message.get("text", {}).get("body", "").strip().upper()

            print("MESSAGE RECEIVED FROM:", sender)

            if message_text in ["STOP", "REMOVE", "UNSUBSCRIBE"]:

                conn = psycopg2.connect(DATABASE_URL)
                cursor = conn.cursor()

                cursor.execute(
                    """
                    UPDATE patients
                    SET opted_out = TRUE
                    WHERE phone = %s
                    """,
                    (sender,)
                )

                conn.commit()
                conn.close()

                send_whatsapp_message(
                    sender,
                    "You have been removed from future follow-up messages."
                )

                return {"status": "opted_out"}

            # Check database
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()

            cursor.execute(
                "SELECT phone FROM patients WHERE phone=%s",
                (sender,)
            )

            existing = cursor.fetchone()

            if not existing:
                print("NEW PATIENT")

                cursor.execute(
                    """
                    INSERT INTO patients
                    (
                        phone,
                        created_at,
                        first_contact_time
                    )
                    VALUES (%s, NOW(), NOW())
                    """,
                    (sender,)
                )

                conn.commit()

                
                send_whatsapp_message(
                    sender,
                    "Welcome to Heartline.\n\n"
                    "Thank you for contacting us. To book your appointment, please use the link below:\n\n"
                    "https://hplix.in/HP4304\n\n"
                    "We look forward to serving you.\n\n"
                    "Team Heartline"
                )

            else:
                print("EXISTING PATIENT")


            conn.close()

        else:
            print("No messages field found")

    except Exception as e:
        print("ERROR:", str(e))

    return {"status": "received"}