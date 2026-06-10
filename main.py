
from fastapi import FastAPI, Request
import requests
import os

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

print("TOKEN EXISTS:", bool(WHATSAPP_TOKEN))
print("PHONE ID EXISTS:", bool(PHONE_NUMBER_ID))


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

            print("MESSAGE RECEIVED FROM:", sender)

            send_whatsapp_message(
                sender,
                "Hello!\n\nBook your appointment here:\nhttps://your-booking-link.com"
            )

        else:
            print("No messages field found")

    except Exception as e:
        print("ERROR:", str(e))

    return {"status": "received"}