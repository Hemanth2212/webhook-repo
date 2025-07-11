from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
from dateutil import parser
from datetime import datetime, timezone

app = Flask(__name__)

# ✅ Connect to MongoDB Atlas with TLS bypass for local testing
client = MongoClient(
    "mongodb+srv://hemanthhem51926:MtSZuSZzwfbbpzeH@cluster0.3yygfkr.mongodb.net/?retryWrites=true&w=majority",
    tls=True,
    tlsAllowInvalidCertificates=True
)

db = client.webhookDB

# Helper: Add ordinal suffix to day
def get_day_with_suffix(day):
    if 10 <= day % 100 <= 20:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')
    return f"{day}{suffix}"

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    if not data:
        return "No data received", 400

    print("📩 Incoming data:", data)  # Debugging print

    schema_doc = {}
    event_type = None

    # ✅ Handle Push event
    if 'commits' in data:
        event_type = 'PUSH'
        commit = data['commits'][0]
        schema_doc = {
            "request_id": commit['id'],
            "author": data.get('pusher', {}).get('name', commit['author']['name']),
            "action": event_type,
            "from_branch": None,
            "to_branch": data['ref'].split('/')[-1],
            "timestamp": parser.parse(commit['timestamp'])
        }

    # ✅ Handle Pull Request event (including merge)
    elif 'pull_request' in data:
        pr = data['pull_request']
        event_type = 'MERGE' if pr.get('merged') else 'PULL_REQUEST'
        schema_doc = {
            "request_id": str(pr["id"]),
            "author": pr["user"]["login"],
            "action": event_type,
            "from_branch": pr["head"]["ref"],
            "to_branch": pr["base"]["ref"],
            "timestamp": parser.parse(pr.get("merged_at") or pr.get("created_at") or pr.get("updated_at"))
        }

    else:
        return "Event type not handled", 400

    # ✅ Insert formatted document to MongoDB
    db.events.insert_one(schema_doc)
    print(f"🔔 Webhook stored: {schema_doc['action']} event by {schema_doc['author']}")
    return "OK", 200

@app.route('/events')
def get_events():
    events = db.events.find().sort("timestamp", -1).limit(10)
    output = []

    for e in events:
        dt = e.get("timestamp")
        if not dt:
            continue

        action = e.get("action")
        author = e.get("author")
        from_branch = e.get("from_branch")
        to_branch = e.get("to_branch")

        day_with_suffix = get_day_with_suffix(dt.day)
        timestamp_str = f"{day_with_suffix} {dt.strftime('%B %Y - %#I:%M %p UTC')}"

        if action == "PUSH":
            message = f'"{author}" pushed to "{to_branch}" on {timestamp_str}'
        elif action == "PULL_REQUEST":
            message = f'"{author}" submitted a pull request from "{from_branch}" to "{to_branch}" on {timestamp_str}'
        elif action == "MERGE":
            message = f'"{author}" merged branch "{from_branch}" to "{to_branch}" on {timestamp_str}'
        else:
            message = f"Unknown event type: {action}"

        output.append({"message": message})

    return jsonify(output)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
