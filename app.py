# webhook-repo/app.py

from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
from bson.objectid import ObjectId
import datetime
from datetime import datetime, timezone
from dateutil import parser
import os

app = Flask(__name__)

# Connect to MongoDB Atlas
client = MongoClient("mongodb+srv://hemanthhem51926:MtSZuSZzwfbbpzeH@cluster0.3yygfkr.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
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

    # Determine event type
    event_type = None
    if 'commits' in data:
        event_type = 'push'
    elif 'pull_request' in data:
        if data['pull_request'].get('merged'):
            event_type = 'merge'
        else:
            event_type = 'pull_request'

    data['event_type'] = event_type
    data['received_at'] = datetime.now(timezone.utc)

    db.events.insert_one(data)
    print(f"🔔 Webhook stored: {data['event_type']}")
    return "OK", 200

@app.route('/events')
def get_events():
    events = db.events.find().sort("received_at", -1).limit(10)
    output = []

    for e in events:
        event_type = e.get("event_type")

        if event_type == "push":
            author = e['commits'][0]['author']['name']
            to_branch = e['ref'].split('/')[-1]
            dt = parser.parse(e['commits'][0]['timestamp'])
            day_with_suffix = get_day_with_suffix(dt.day)
            timestamp = f"{day_with_suffix} {dt.strftime('%B %Y - %#I:%M %p UTC')}"
            message = f'"{author}" pushed to "{to_branch}" on {timestamp}'
            output.append({"message": message})

        elif event_type == "pull_request":
            pr = e["pull_request"]
            author = pr["user"]["login"]
            from_branch = pr["head"]["ref"]
            to_branch = pr["base"]["ref"]
            dt = parser.parse(pr["created_at"])
            day_with_suffix = get_day_with_suffix(dt.day)
            timestamp = f"{day_with_suffix} {dt.strftime('%B %Y - %#I:%M %p UTC')}"
            message = f'"{author}" submitted a pull request from "{from_branch}" to "{to_branch}" on {timestamp}'
            output.append({"message": message})

        elif event_type == "merge":
            pr = e["pull_request"]
            author = pr["user"]["login"]
            from_branch = pr["head"]["ref"]
            to_branch = pr["base"]["ref"]
            merged_at = pr.get("merged_at") or pr.get("updated_at")
            dt = parser.parse(merged_at)
            day_with_suffix = get_day_with_suffix(dt.day)
            timestamp = f"{day_with_suffix} {dt.strftime('%B %Y - %#I:%M %p UTC')}"
            message = f'"{author}" merged branch "{from_branch}" to "{to_branch}" on {timestamp}'
            output.append({"message": message})

    return jsonify(output)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
