from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import gap
import llm
import os

app = Flask(__name__)
CORS(app)  # Enable CORS

@app.route('/')
def home():
    print("Home Route Accessed", flush=True)
    return send_from_directory('.', 'index.html')

@app.route('/api', methods=['POST'])
def api_handler():
    print("API Handler Reached", flush=True)
    try:
        data = request.json
        print(f"Request Data: {data}", flush=True)
        action = data.get('action')
        print(f"Processing Action: {action}", flush=True)

        if action == 'dashboard':
            result = gap.generate_gap_analysis()
            return jsonify(result)
        
        elif action == 'generate_content':
            title = data.get('title')
            if not title:
                return jsonify({"error": "Title is required for content generation"}), 400
            result = llm.generate_podcast_draft(title)
            return jsonify(result)
        
        else:
            return jsonify({"error": "Invalid action"}), 400

    except Exception as e:
        print(f"Error processing request: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("Starting Local Fertility Friday App...")
    print("Please open: http://localhost:5000")
    app.run(debug=True, port=5000)
