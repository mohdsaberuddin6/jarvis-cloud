from flask import Flask, request, jsonify
import datetime
import threading
import time

app = Flask(__name__)

tasks = []

# 🔁 Background scheduler
def scheduler():
    while True:
        now = datetime.datetime.now()

        for task in tasks[:]:
            if now >= task["time"]:
                print(f"✅ Sending message to {task['target']}: {task['message']}")
                tasks.remove(task)

        time.sleep(5)

# 🌐 API to receive tasks
@app.route("/schedule", methods=["POST"])
def schedule():
    data = request.json

    task = {
        "target": data["target"],
        "message": data["message"],
        "time": datetime.datetime.strptime(data["time"], "%Y-%m-%d %H:%M")
    }

    tasks.append(task)

    print("📌 Task received:", task)

    return jsonify({"status": "scheduled"})

# 🚀 Start everything
if __name__ == "__main__":
    threading.Thread(target=scheduler, daemon=True).start()
    app.run(host="0.0.0.0", port=5000)