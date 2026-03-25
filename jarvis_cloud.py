from flask import Flask, request, jsonify
import datetime
import threading
import time
import os
import json
from email.message import EmailMessage
import smtplib
from twilio.rest import Client

app = Flask(__name__)

# ---------------- CONFIG ----------------
TASK_FILE = "tasks.json"

API_KEY = os.environ.get("API_KEY")
TWILIO_SID = os.environ.get("TWILIO_SID")
TWILIO_AUTH = os.environ.get("TWILIO_AUTH")

tasks = []

# ---------------- SAVE / LOAD ----------------
def save_tasks():
    with open(TASK_FILE, "w") as f:
        json.dump([
            {**t, "time": t["time"].strftime("%Y-%m-%d %H:%M:%S")}
            for t in tasks
        ], f, indent=4)

def load_tasks():
    global tasks
    if os.path.exists(TASK_FILE):
        try:
            with open(TASK_FILE, "r") as f:
                data = json.load(f)
                tasks = [
                    {**t, "time": datetime.datetime.strptime(t["time"], "%Y-%m-%d %H:%M:%S")}
                    for t in data
                ]
        except Exception as e:
            print("❌ Load error:", e)
            tasks = []

# ---------------- EMAIL ----------------
def send_email(receiver_email, subject, message):
    try:
        print("📧 Sending email to:", receiver_email)

        # 🔥 Load env here (IMPORTANT)
        EMAIL_USER = os.environ.get("EMAIL_USER")
        EMAIL_PASS = os.environ.get("EMAIL_PASS")

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

        print("✅ Email sent SUCCESSFULLY")

    except Exception as e:
        print("❌ Email error:", e)

# ---------------- SCHEDULER ----------------
def scheduler():
    print("🚀 Scheduler started")

    while True:
        try:
            now = datetime.datetime.now()

            print("\n🧠 ===== LOOP START =====")
            print("⏰ Current time:", now)
            print("📦 Tasks:", tasks)

            for task in tasks[:]:
                print("📅 Checking task:", task["time"])

                if now >= task["time"]:
                    print("⏳ Running task:", task)

                    try:
                        # 📧 EMAIL
                        if "@" in task["target"]:
                            send_email(
                                task["target"],
                                task.get("subject", "No Subject"),
                                task["message"]
                            )

                        # 📱 WHATSAPP
                        else:
                            if not TWILIO_SID or not TWILIO_AUTH:
                                print("❌ Twilio not configured")
                                continue

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

        except Exception as e:
            print("❌ Scheduler crash:", e)

        time.sleep(5)

# ---------------- ROUTES ----------------
@app.route("/")
def home():
    return "Jarvis Cloud Running ✅"

@app.route("/schedule", methods=["POST"])
def schedule():

    # 🔐 SECURITY
    if not API_KEY or request.headers.get("x-api-key") != API_KEY:
        return jsonify({"error": "Unauthorized"}), 403

    data = request.json

    try:
        if not data:
            return jsonify({"error": "No data"}), 400

        target = data.get("target")
        message = data.get("message")
        subject = data.get("subject", "No Subject")
        time_str = data.get("time")

        if not target or not message or not time_str:
            return jsonify({"error": "Missing fields"}), 400

        # ✅ Parse time
        task_time = datetime.datetime.strptime(time_str, "%Y-%m-%d %H:%M")

        task = {
            "target": target,
            "message": message,
            "subject": subject,
            "time": task_time
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

    # 🔥 Start scheduler thread
    threading.Thread(target=scheduler, daemon=True).start()

    port = int(os.environ.get("PORT", 10000))
    print(f"🚀 Running on port {port}")

    app.run(host="0.0.0.0", port=port)
    
