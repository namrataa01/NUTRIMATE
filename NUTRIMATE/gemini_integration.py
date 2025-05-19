from flask import Flask, request, jsonify, send_from_directory
import requests
import json
import os

app = Flask(__name__)

# Gemini API settings
GEMINI_API_KEY = "AIzaSyD3oCC5X0ODIGL56C6ZZUFCErni1hRSLyE"
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/query', methods=['POST'])
def process_query():
    user_query = request.json.get('query', '')
    
    # Call Gemini API
    try:
        gemini_response = query_gemini(user_query)
        return jsonify({"type": "text", "content": gemini_response})
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return jsonify({"type": "text", "content": "Sorry, I encountered an error while processing your request."})

def query_gemini(query_text):
    url = f"{GEMINI_API_URL}?key={GEMINI_API_KEY}"
    
    payload = {
        "contents": [{
            "parts": [{"text": query_text}]
        }]
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    
    if response.status_code == 200:
        result = response.json()
        # Extract text from response
        if 'candidates' in result and len(result['candidates']) > 0:
            if 'content' in result['candidates'][0] and 'parts' in result['candidates'][0]['content']:
                return result['candidates'][0]['content']['parts'][0]['text']
    
    # Return error message if response parsing fails
    return "I'm having trouble understanding that right now. Could you try asking something else?"

if __name__ == '__main__':
    app.run(debug=True)