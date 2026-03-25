from flask import Flask, request, jsonify
import datetime
import threading
import time
import os
import json
from datetime import timezone
from twilio.rest import Client
import smtplib
from email.message import EmailMessage
import pytz

app = Flask(__name__)

# ---------------- CONFIG ----------------
TASK_FILE = "tasks.json"

# 🔐 LOAD FROM ENV (SAFE)
API_KEY = os.environ.get("API_KEY")
EMAIL_USER = os.environ.get("EMAIL_USER")
EMAIL_PASS = os.environ.get("EMAIL_PASS")
TWILIO_SID = os.environ.get("TWILIO_SID")
TWILIO_AUTH = os.environ.get("TWILIO_AUTH")

tasks = []

# ---------------- SAVE / LOAD ----------------
def save_tasks():
    with open(TASK_FILE, "w") as f:
        json.dump(tasks, f, default=str, indent=4)

def load_tasks():
    global tasks
    if os.path.exists(TASK_FILE):
        with open(TASK_FILE, "r") as f:
            tasks = json.load(f)
            for t in tasks:
                t["time"] = datetime.datetime.fromisoformat(t["time"])

# ---------------- EMAIL ----------------
def send_email(receiver_email, subject, message):
    try:
        if not EMAIL_USER or not EMAIL_PASS:
            print("❌ Email credentials missing")
            return

        msg = EmailMessage()
        msg["From"] = EMAIL_USER
        msg["To"] = receiver_email
        msg["Subject"] = subject
        msg.set_content(message)

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(EMAIL_USER, EMAIL_PASS)
            smtp.send_message(msg)

        print("✅ Email sent")

    except Exception as e:
        print("❌ Email error:", e)

# ---------------- SCHEDULER ----------------
def scheduler():
    while True:
        now = datetime.datetime.now(datetime.timezone.utc)

        for task in tasks[:]:
            if now >= task["time"]:
                print("⏳ Running task:", task)

                try:
                    # EMAIL
                    if task.get("subject"):
                        send_email(task["target"], task["subject"], task["message"])

                    # WHATSAPP
                    else:
                        if not TWILIO_SID or not TWILIO_AUTH:
                            print("❌ Twilio credentials missing")
                        else:
                            client = Client(TWILIO_SID, TWILIO_AUTH)

                            client.messages.create(
                                from_='whatsapp:+14155238886',
                                body=task["message"],
                                to=f'whatsapp:{task["target"]}'
                            )

                            print("✅ WhatsApp sent")

                except Exception as e:
                    print("❌ Task error:", e)

                tasks.remove(task)
                save_tasks()

        time.sleep(5)

# ---------------- ROUTES ----------------
@app.route("/")
def home():
    return "Jarvis Cloud Running ✅"

@app.route("/schedule", methods=["POST"])
def schedule():
    # 🔐 SECURITY CHECK
    if not API_KEY or request.headers.get("x-api-key") != API_KEY:
        return jsonify({"error": "Unauthorized"}), 403

    data = request.json

    try:
        # ✅ VALIDATION
        if not data:
            return jsonify({"error": "No data provided"}), 400

        if "target" not in data or "message" not in data or "time" not in data:
            return jsonify({"error": "Missing required fields"}), 400

        # Basic validation
        if not isinstance(data["target"], str) or not data["target"]:
            return jsonify({"error": "Invalid target"}), 400

        # Convert string → datetime
        local_time = datetime.datetime.strptime(data["time"], "%Y-%m-%d %H:%M")

        # ✅ TIMEZONE SAFE
        ist = pytz.timezone("Asia/Kolkata")
        utc = pytz.utc

        local_dt = ist.localize(local_time)
        utc_time = local_dt.astimezone(utc)

        task = {
            "target": data["target"],
            "message": data["message"],
            "subject": data.get("subject"),
            "time": utc_time
        }

        tasks.append(task)
        save_tasks()

        print("📌 Task scheduled:", task)

        return jsonify({"status": "scheduled"})

    except Exception as e:
        print("❌ Schedule error:", e)
        return jsonify({"error": "Invalid data"}), 400

# ---------------- START ----------------
if __name__ == "__main__":
    load_tasks()

    threading.Thread(target=scheduler, daemon=True).start()

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

      
