from fastapi import FastAPI, Request

app = FastAPI()

VERIFY_TOKEN = "anmol_bot_2026"

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
    data = await request.json()

    print("Received message:")
    print(data)

    return {"status": "received"}