import os
import requests
import psycopg2

DATABASE_URL = os.getenv("DATABASE_URL")
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")

REVIEW_LINK = "https://g.page/r/CVCRvic5gGXEBM/review"


def send_whatsapp_message(to_number, message):

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

    response = requests.post(
        url,
        headers=headers,
        json=payload
    )

    print(
        f"Sent to {to_number}:",
        response.status_code
    )


def send_review_template(to_number):

    url = f"https://graph.facebook.com/v23.0/{PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "template",
        "template": {
            "name": "review_request",
            "language": {
                "code": "en"
            }
        }
    }

    response = requests.post(
        url,
        headers=headers,
        json=payload
    )

    print(
        f"Reminder sent to {to_number}:",
        response.status_code
    )


conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

# 18-hour review message

cursor.execute(
    """
    SELECT phone
    FROM patients
    WHERE review_sent = FALSE
    AND opted_out = FALSE
    AND first_contact_time <= NOW() - INTERVAL '18 hours'
    """
)

patients = cursor.fetchall()

print("Patients due:", len(patients))

for patient in patients:

    phone = patient[0]

    message = f"""Thank you for contacting Heartline.

We hope your experience was satisfactory.

If you have a moment, we'd greatly appreciate your feedback:

{REVIEW_LINK}

Thank you for your support.
To stop receiving follow-up messages, reply STOP.
"""

    send_whatsapp_message(phone, message)

    cursor.execute(
        """
        UPDATE patients
        SET review_sent = TRUE,
            review_sent_at = NOW()
        WHERE phone = %s
        """,
        (phone,)
    )

# 5-day reminder template

cursor.execute(
    """
    SELECT phone
    FROM patients
    WHERE review_sent = TRUE
    AND reminder_sent = FALSE
    AND opted_out = FALSE
    AND review_sent_at <= NOW() - INTERVAL '5 days'
    """
)

patients = cursor.fetchall()

print("Reminder patients:", len(patients))

for patient in patients:

    phone = patient[0]

    send_review_template(phone)

    cursor.execute(
        """
        UPDATE patients
        SET reminder_sent = TRUE
        WHERE phone = %s
        """,
        (phone,)
    )

conn.commit()
conn.close()

print("Review scheduler complete")