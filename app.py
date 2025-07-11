from flask import Flask, request, jsonify
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)

# ✅ MongoDB Atlas connection
client = MongoClient("mongodb+srv://hemanthhem51926:MtSZuSZzwfbbpzeH@cluster0.3yygfkr.mongodb.net/webhookDB?retryWrites=true&w=majority&appName=Cluster0")
db = client["webhookDB"]
collection = db["events"]

@app.route('/')
def home():
    return '✅ Flask app connected to MongoDB Atlas!'

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    data['received_at'] = datetime.utcnow()
    collection.insert_one(data)
    print("🔔 Webhook stored:", data)
    return jsonify({"status": "Webhook stored in MongoDB"}), 200

if __name__ == '__main__':
    app.run(port=5000, debug=True)
