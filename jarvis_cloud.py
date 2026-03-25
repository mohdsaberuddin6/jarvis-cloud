from flask import Flask, request, jsonify
import datetime
import threading
import time
import os
from datetime import timezone
from twilio.rest import Client

app = Flask(__name__)

tasks = []

# 🔁 Background scheduler
def scheduler():
    while True:
        now = datetime.datetime.now(datetime.timezone.utc)

        for task in tasks[:]:
            if now >= task["time"]:
                print("⏳ Checking task:", task["time"], "Current:", now)

                from twilio.rest import Client
                import os

                account_sid = os.environ.get("TWILIO_SID")
                auth_token = os.environ.get("TWILIO_AUTH")

                client = Client(account_sid, auth_token)

                client.messages.create(
                    from_='whatsapp:+14155238886',
                    body=task["message"],
                    to=f'whatsapp:{task["target"]}'
                )

                print("✅ Message sent:", task["message"])

                tasks.remove(task)

        time.sleep(5)

@app.route("/")
def home():
    return "Jarvis Cloud Running ✅"

# 🌐 API to receive tasks
@app.route("/schedule", methods=["POST"])
def schedule():
    data = request.json

    # Convert string → datetime
    local_time = datetime.datetime.strptime(data["time"], "%Y-%m-%d %H:%M")

    # Convert IST → UTC
    utc_time = local_time - datetime.timedelta(hours=5, minutes=30)

    task = {
        "target": data["target"],
        "message": data["message"],
        "time": utc_time.replace(tzinfo=timezone.utc)
    }

    tasks.append(task)

    print("📌 Task received:", task)

    return jsonify({"status": "scheduled"})

# 🚀 Start everything
if __name__ == "__main__":
    threading.Thread(target=scheduler, daemon=True).start()

    import os
    port = int(os.environ.get("PORT", 5000))

    app.run(host="0.0.0.0", port=port)
   
